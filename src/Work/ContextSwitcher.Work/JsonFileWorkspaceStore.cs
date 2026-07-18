using System.Text.Json;
using System.Text.Json.Serialization;

namespace ContextSwitcher.Work;

/// <summary>
/// JSON file adapter for <see cref="IWorkspaceStore"/> (ADR-0008).
///
/// * Location: &lt;dataHome&gt;/workspace.json. The default data home is
///   %LOCALAPPDATA%/ContextSwitcher, overridable via the
///   CONTEXT_SWITCHER_DATA_HOME environment variable (a directory path).
/// * Writes are atomic: serialize to a temp file in the same directory, then
///   move it over the target.
/// * A missing file is a fresh workspace (first run). A malformed file or an
///   unsupported (newer) schema_version is a <see cref="StoreCorruptException"/>;
///   an older/blank version is migrated on load (see <see cref="WorkspaceMigrator"/>).
///   The file is never modified, reset, or overwritten in response to a read.
/// * <see cref="Update"/> serializes concurrent writers with a sibling lock file
///   (ADR-0026) so a load-mutate-save critical section cannot lose updates or
///   observe a torn file.
/// </summary>
public sealed class JsonFileWorkspaceStore : IWorkspaceStore
{
    public const string FileName = "workspace.json";
    public const string DataHomeEnvVar = "CONTEXT_SWITCHER_DATA_HOME";

    /// <summary>Default bound on how long <see cref="Update"/> waits for the lock.</summary>
    public static readonly TimeSpan DefaultLockTimeout = TimeSpan.FromSeconds(10);

    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        Converters = { new JsonStringEnumConverter(JsonNamingPolicy.SnakeCaseLower) },
    };

    private readonly string _directory;
    private readonly TimeSpan _lockTimeout;

    /// <param name="directory">
    /// Data directory. When null, resolves CONTEXT_SWITCHER_DATA_HOME, then
    /// %LOCALAPPDATA%/ContextSwitcher.
    /// </param>
    /// <param name="lockTimeout">
    /// How long <see cref="Update"/> waits for the exclusive lock before failing
    /// with <see cref="StoreLockedException"/>. Defaults to
    /// <see cref="DefaultLockTimeout"/>.
    /// </param>
    public JsonFileWorkspaceStore(string? directory = null, TimeSpan? lockTimeout = null)
    {
        _directory = directory ?? ResolveDefaultDirectory();
        _lockTimeout = lockTimeout ?? DefaultLockTimeout;
    }

    public string FilePath => Path.Combine(_directory, FileName);

    /// <summary>Sibling lock file guarding <see cref="Update"/> (never holds data).</summary>
    public string LockFilePath => FilePath + ".lock";

    public static string ResolveDefaultDirectory()
    {
        var overridden = Environment.GetEnvironmentVariable(DataHomeEnvVar);
        if (!string.IsNullOrWhiteSpace(overridden))
        {
            return overridden.Trim();
        }
        var localAppData = Environment.GetFolderPath(
            Environment.SpecialFolder.LocalApplicationData,
            Environment.SpecialFolderOption.Create);
        return Path.Combine(localAppData, "ContextSwitcher");
    }

    public WorkspaceState Load()
    {
        if (!File.Exists(FilePath))
        {
            return new WorkspaceState();
        }

        string json;
        try
        {
            json = File.ReadAllText(FilePath);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            throw new StoreCorruptException(
                $"The workspace file could not be read: {FilePath} ({ex.Message}). " +
                "Your data has not been modified.", ex);
        }

        WorkspaceState? state;
        try
        {
            state = JsonSerializer.Deserialize<WorkspaceState>(json, SerializerOptions);
        }
        catch (JsonException ex)
        {
            throw new StoreCorruptException(
                $"The workspace file is not valid JSON: {FilePath}. " +
                "Your data has not been modified; repair or move the file and retry.", ex);
        }

        if (state is null)
        {
            throw new StoreCorruptException(
                $"The workspace file is empty or null: {FilePath}. " +
                "Your data has not been modified; repair or move the file and retry.");
        }
        // Explicit version handling (ADR-0026): equal loads as-is, older/blank is
        // migrated in memory, newer/unparseable throws. The file is not rewritten
        // here; a migrated state is persisted on the next Save.
        return WorkspaceMigrator.Migrate(state, FilePath);
    }

    public void Save(WorkspaceState state)
    {
        Directory.CreateDirectory(_directory);
        var json = JsonSerializer.Serialize(state, SerializerOptions);
        var tempPath = Path.Combine(_directory, FileName + "." + Guid.NewGuid().ToString("N") + ".tmp");
        try
        {
            File.WriteAllText(tempPath, json);
            File.Move(tempPath, FilePath, overwrite: true);
        }
        finally
        {
            if (File.Exists(tempPath))
            {
                try { File.Delete(tempPath); } catch (IOException) { /* best effort */ }
            }
        }
    }

    /// <summary>
    /// Guarded read-modify-write (ADR-0026). Holds an exclusive sibling lock file
    /// across load-mutate-save so two processes/threads cannot interleave and
    /// lose each other's updates. The write itself stays atomic (temp-then-move).
    /// </summary>
    /// <exception cref="StoreLockedException">
    /// The lock could not be acquired within the configured timeout.
    /// </exception>
    public WorkspaceState Update(Func<WorkspaceState, WorkspaceState> mutate)
    {
        ArgumentNullException.ThrowIfNull(mutate);
        Directory.CreateDirectory(_directory);
        using var lockHandle = AcquireLock();
        var updated = mutate(Load())
            ?? throw new ValidationException("The mutation returned a null workspace state.");
        Save(updated);
        return updated;
    }

    /// <summary>
    /// Opens the sibling lock file with <see cref="FileShare.None"/> — the OS
    /// grants it to exactly one holder at a time, across processes and threads —
    /// retrying with bounded backoff until the timeout, then failing loudly.
    /// </summary>
    private FileStream AcquireLock()
    {
        var deadline = Environment.TickCount64 + (long)_lockTimeout.TotalMilliseconds;
        var backoffMs = 2;
        IOException? last = null;
        while (true)
        {
            try
            {
                return new FileStream(
                    LockFilePath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            }
            catch (IOException ex)
            {
                // Sharing violation: another holder has the lock. Retry until the
                // deadline (one attempt is always made before giving up).
                last = ex;
                if (Environment.TickCount64 >= deadline)
                {
                    break;
                }
                Thread.Sleep(backoffMs);
                backoffMs = Math.Min(backoffMs * 2, 25);
            }
        }
        throw new StoreLockedException(
            $"Another writer holds the workspace lock at {LockFilePath}; it could not " +
            $"be acquired within {_lockTimeout.TotalSeconds:0.###}s. Your data has not " +
            "been modified; retry in a moment.", last!);
    }
}
