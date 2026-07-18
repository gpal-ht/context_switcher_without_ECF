namespace ContextSwitcher.Work.Tests;

/// <summary>
/// Concurrency and schema-migration hardening for <see cref="JsonFileWorkspaceStore"/>
/// (ADR-0026). Every test runs against a fresh temp directory removed on dispose;
/// tests are deterministic and use no real sleeps beyond the store's own bounded,
/// sub-second lock backoff exercised by the timeout case.
/// </summary>
public sealed class PersistenceHardeningTests : IDisposable
{
    private readonly string _dir = Path.Combine(
        Path.GetTempPath(), "cs-harden-tests-" + Guid.NewGuid().ToString("N"));

    public void Dispose()
    {
        try { Directory.Delete(_dir, recursive: true); } catch (DirectoryNotFoundException) { }
    }

    private JsonFileWorkspaceStore NewStore() => new(_dir);

    private void WriteRaw(string json)
    {
        Directory.CreateDirectory(_dir);
        File.WriteAllText(Path.Combine(_dir, JsonFileWorkspaceStore.FileName), json);
    }

    // ---- Schema migration --------------------------------------------------

    [Test]
    public void Older_version_file_is_migrated_to_current_on_load()
    {
        // A hypothetical earlier version with the same shape upgrades cleanly.
        WriteRaw("""{ "schema_version": "0.0.9", "active_project_id": null, "projects": [] }""");

        var state = NewStore().Load();
        Check.Equal(WorkspaceState.CurrentSchemaVersion, state.SchemaVersion,
            "older version is stamped to current on load");
    }

    [Test]
    public void Blank_version_is_treated_as_oldest_and_migrated()
    {
        // A pre-versioned file (explicit empty schema_version) is the oldest schema.
        WriteRaw("""{ "schema_version": "", "projects": [] }""");

        var state = NewStore().Load();
        Check.Equal(WorkspaceState.CurrentSchemaVersion, state.SchemaVersion,
            "blank version is migrated to current");
    }

    [Test]
    public void Absent_version_key_loads_at_current_without_data_loss()
    {
        // No schema_version key at all: deserializes to the current default and
        // loads unchanged (0.1.0 is the first schema, so absent == current shape).
        WriteRaw("""
            {
              "projects": [
                {
                  "id": "11111111-1111-1111-1111-111111111111",
                  "name": "Alpha",
                  "created_utc": "2026-01-01T00:00:00+00:00",
                  "updated_utc": "2026-01-01T00:00:00+00:00"
                }
              ]
            }
            """);

        var state = NewStore().Load();
        Check.Equal(WorkspaceState.CurrentSchemaVersion, state.SchemaVersion, "loads at current");
        Check.Equal(1, state.Projects.Count, "existing data preserved");
    }

    [Test]
    public void Load_does_not_rewrite_the_file_but_next_save_persists_the_migration()
    {
        WriteRaw("""{ "schema_version": "0.0.9", "projects": [] }""");
        var store = NewStore();

        var state = store.Load();
        Check.That(File.ReadAllText(store.FilePath).Contains("0.0.9"),
            "loading migrates in memory only; the file on disk is untouched");

        store.Save(state);
        Check.That(File.ReadAllText(store.FilePath)
                .Contains($"\"schema_version\": \"{WorkspaceState.CurrentSchemaVersion}\""),
            "the migrated version is persisted on the next save");
    }

    [Test]
    public void Newer_minor_version_is_rejected_by_version_comparison()
    {
        // Rejection is a semantic comparison, not string (in)equality: a newer
        // MINOR bump is refused just like a wildly-newer one.
        WriteRaw("""{ "schema_version": "0.2.0", "projects": [] }""");
        var store = NewStore();

        var ex = Check.Throws<StoreCorruptException>(() => store.Load(), "newer schema rejected");
        Check.That(ex.Message.Contains("0.2.0"), "error names the found version");
        Check.That(ex.Message.Contains(WorkspaceState.CurrentSchemaVersion),
            "error names the supported version");
    }

    [Test]
    public void Unparseable_version_is_a_store_corrupt_error()
    {
        WriteRaw("""{ "schema_version": "not-a-version", "projects": [] }""");
        Check.Throws<StoreCorruptException>(() => NewStore().Load(), "garbage version rejected");
    }

    // ---- Concurrency -------------------------------------------------------

    [Test]
    public void Update_persists_and_is_visible_to_a_fresh_store()
    {
        var store = NewStore();
        var result = store.Update(s =>
        {
            s.Projects.Add(NewProject("Alpha"));
            return s;
        });

        Check.Equal(1, result.Projects.Count, "update returns the persisted state");
        Check.Equal(1, new JsonFileWorkspaceStore(_dir).Load().Projects.Count,
            "a fresh store instance sees the update");
    }

    [Test]
    public void Concurrent_updates_do_not_lose_data()
    {
        // Without the guarded critical section, interleaved load-mutate-save under
        // last-writer-wins would drop most of these adds. The lock serializes them,
        // so every writer's project survives. Deterministic: join-based, no sleeps.
        var store = NewStore();
        store.Save(new WorkspaceState());

        const int writers = 12;
        var errors = new Exception?[writers];
        var threads = new Thread[writers];
        var start = new ManualResetEventSlim(false);

        for (var i = 0; i < writers; i++)
        {
            var n = i;
            threads[n] = new Thread(() =>
            {
                try
                {
                    start.Wait();
                    store.Update(s =>
                    {
                        s.Projects.Add(NewProject("P" + n));
                        return s;
                    });
                }
                catch (Exception ex) { errors[n] = ex; }
            });
            threads[n].Start();
        }

        start.Set(); // release all writers roughly together to maximize contention
        foreach (var t in threads) t.Join();

        Check.That(Array.TrueForAll(errors, e => e is null), "no writer failed");
        var final = store.Load();
        Check.Equal(writers, final.Projects.Count, "every concurrent update survived (no lost writes)");
        var distinct = final.Projects.Select(p => p.Name).Distinct().Count();
        Check.Equal(writers, distinct, "each writer's distinct project is present");
    }

    [Test]
    public void Update_surfaces_a_domain_exception_when_the_lock_is_held()
    {
        // Hold the lock file exactly the way the store does, then a short-timeout
        // Update must fail loudly rather than hang. Backoff is bounded and tiny.
        Directory.CreateDirectory(_dir);
        var store = new JsonFileWorkspaceStore(_dir, lockTimeout: TimeSpan.FromMilliseconds(150));

        using (new FileStream(store.LockFilePath, FileMode.OpenOrCreate,
                   FileAccess.ReadWrite, FileShare.None))
        {
            var ex = Check.Throws<StoreLockedException>(
                () => store.Update(s => s), "held lock surfaces StoreLockedException");
            Check.That(ex.Message.Contains(store.LockFilePath), "error names the lock file");
        }

        // Once released, the same store can update normally.
        store.Update(s => { s.Projects.Add(NewProject("After")); return s; });
        Check.Equal(1, store.Load().Projects.Count, "update succeeds after the lock is released");
    }

    private static Project NewProject(string name) => new()
    {
        Id = Guid.NewGuid(),
        Name = name,
        CreatedUtc = DateTimeOffset.UtcNow,
        UpdatedUtc = DateTimeOffset.UtcNow,
    };
}
