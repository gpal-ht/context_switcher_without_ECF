namespace ContextSwitcher.Work.Tests;

/// <summary>
/// Persistence tests for <see cref="JsonFileWorkspaceStore"/> against a
/// temp directory (created per fixture instance, removed on dispose).
/// </summary>
public sealed class JsonFileWorkspaceStoreTests : IDisposable
{
    private readonly string _dir = Path.Combine(
        Path.GetTempPath(), "cs-store-tests-" + Guid.NewGuid().ToString("N"));

    public void Dispose()
    {
        try { Directory.Delete(_dir, recursive: true); } catch (DirectoryNotFoundException) { }
    }

    private JsonFileWorkspaceStore NewStore() => new(_dir);

    [Test]
    public void Missing_file_is_a_fresh_workspace_not_an_error()
    {
        var state = NewStore().Load();
        Check.Equal(0, state.Projects.Count, "no projects on first run");
        Check.Equal(null, state.ActiveProjectId, "no active project on first run");
    }

    [Test]
    public void State_round_trips_through_disk()
    {
        var registry = new ProjectRegistry(NewStore());
        var alpha = registry.CreateProject("Alpha", "first");
        registry.CreateProject("Beta");
        registry.SwitchActiveProject("Beta");

        // A brand-new store instance (fresh process semantics) sees the state.
        var reloaded = new ProjectRegistry(NewStore());
        var names = reloaded.ListProjects().Select(p => p.Name).ToArray();
        Check.Equal(2, names.Length, "both projects persisted");
        Check.Equal("Beta", reloaded.GetActiveProject()!.Name, "active selection persisted");
        var alphaReloaded = reloaded.ListProjects().First(p => p.Name == "Alpha");
        Check.Equal(alpha.Id, alphaReloaded.Id, "id persisted");
        Check.Equal("first", alphaReloaded.Description, "description persisted");
        Check.Equal(alpha.CreatedUtc, alphaReloaded.CreatedUtc, "created timestamp persisted");
    }

    [Test]
    public void Save_is_atomic_and_leaves_no_temp_files()
    {
        var store = NewStore();
        store.Save(new WorkspaceState());
        store.Save(new WorkspaceState { Projects = { NewProject("Alpha") } });
        var leftovers = Directory.GetFiles(_dir, "*.tmp");
        Check.Equal(0, leftovers.Length, "no temp files remain after save");
        Check.Equal(1, store.Load().Projects.Count, "last save wins");
    }

    [Test]
    public void Malformed_json_is_a_store_corrupt_error_and_data_is_untouched()
    {
        var store = NewStore();
        Directory.CreateDirectory(_dir);
        File.WriteAllText(store.FilePath, "{ this is not json");

        Check.Throws<StoreCorruptException>(() => store.Load(), "malformed JSON");
        Check.Equal("{ this is not json", File.ReadAllText(store.FilePath),
            "corrupted file was not modified");
    }

    [Test]
    public void Unsupported_schema_version_fails_clearly_without_touching_data()
    {
        var store = NewStore();
        Directory.CreateDirectory(_dir);
        File.WriteAllText(store.FilePath, """{ "schema_version": "9.9.9", "projects": [] }""");

        var ex = Check.Throws<StoreCorruptException>(() => store.Load(), "unsupported schema");
        Check.That(ex.Message.Contains("9.9.9"), "error names the found version");
        Check.That(ex.Message.Contains(WorkspaceState.CurrentSchemaVersion),
            "error names the supported version");
    }

    [Test]
    public void Written_file_carries_the_current_schema_version()
    {
        var store = NewStore();
        store.Save(new WorkspaceState { Projects = { NewProject("Alpha") } });
        var text = File.ReadAllText(store.FilePath);
        Check.That(text.Contains($"\"schema_version\": \"{WorkspaceState.CurrentSchemaVersion}\""),
            "schema_version recorded in the file");
        Check.That(text.Contains("\"name\": \"Alpha\""), "snake_case field naming used");
    }

    private static Project NewProject(string name) => new()
    {
        Id = Guid.NewGuid(),
        Name = name,
        CreatedUtc = DateTimeOffset.UtcNow,
        UpdatedUtc = DateTimeOffset.UtcNow,
    };
}
