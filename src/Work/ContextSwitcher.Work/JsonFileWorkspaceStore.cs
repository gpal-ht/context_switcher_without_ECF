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
///   unsupported schema_version is a <see cref="StoreCorruptException"/>; the
///   file is never modified, reset, or overwritten in response.
/// </summary>
public sealed class JsonFileWorkspaceStore : IWorkspaceStore
{
    public const string FileName = "workspace.json";
    public const string DataHomeEnvVar = "CONTEXT_SWITCHER_DATA_HOME";

    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        Converters = { new JsonStringEnumConverter(JsonNamingPolicy.SnakeCaseLower) },
    };

    private readonly string _directory;

    /// <param name="directory">
    /// Data directory. When null, resolves CONTEXT_SWITCHER_DATA_HOME, then
    /// %LOCALAPPDATA%/ContextSwitcher.
    /// </param>
    public JsonFileWorkspaceStore(string? directory = null)
    {
        _directory = directory ?? ResolveDefaultDirectory();
    }

    public string FilePath => Path.Combine(_directory, FileName);

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
        if (state.SchemaVersion != WorkspaceState.CurrentSchemaVersion)
        {
            throw new StoreCorruptException(
                $"The workspace file at {FilePath} uses schema version " +
                $"'{state.SchemaVersion}', but this build supports " +
                $"'{WorkspaceState.CurrentSchemaVersion}'. Your data has not been " +
                "modified; use a matching application version.");
        }
        return state;
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
}
