namespace ContextSwitcher.Work;

/// <summary>
/// Context Switcher-owned persistence port for workspace state (ADR-0008).
/// Adapters: <see cref="JsonFileWorkspaceStore"/> (production),
/// <see cref="InMemoryWorkspaceStore"/> (test seam). Synchronous by design:
/// workspace state is a small local document.
/// </summary>
public interface IWorkspaceStore
{
    /// <summary>
    /// Loads the workspace, or returns a fresh empty state when none has been
    /// persisted yet (first run is not an error).
    /// </summary>
    /// <exception cref="StoreCorruptException">
    /// The store exists but cannot be read; user data is left untouched.
    /// </exception>
    WorkspaceState Load();

    /// <summary>Persists the workspace atomically.</summary>
    void Save(WorkspaceState state);
}

/// <summary>In-memory store for deterministic tests. Not persistent.</summary>
public sealed class InMemoryWorkspaceStore : IWorkspaceStore
{
    private WorkspaceState? _state;

    public WorkspaceState Load() => _state ?? new WorkspaceState();

    public void Save(WorkspaceState state) => _state = state;
}
