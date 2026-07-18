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

    /// <summary>
    /// Guarded read-modify-write (ADR-0026): loads the current state, applies
    /// <paramref name="mutate"/>, and persists the result as a single critical
    /// section protected against concurrent writers. Prefer this over separate
    /// <see cref="Load"/>/<see cref="Save"/> when an update must not race another
    /// process or thread (otherwise concurrent writers can lose each other's
    /// changes under last-writer-wins). Returns the persisted state.
    /// </summary>
    /// <exception cref="StoreLockedException">
    /// The exclusive lock could not be acquired within the timeout.
    /// </exception>
    /// <exception cref="StoreCorruptException">The existing store cannot be read.</exception>
    WorkspaceState Update(Func<WorkspaceState, WorkspaceState> mutate);
}

/// <summary>In-memory store for deterministic tests. Not persistent.</summary>
public sealed class InMemoryWorkspaceStore : IWorkspaceStore
{
    private readonly object _gate = new();
    private WorkspaceState? _state;

    public WorkspaceState Load()
    {
        lock (_gate) { return _state ?? new WorkspaceState(); }
    }

    public void Save(WorkspaceState state)
    {
        lock (_gate) { _state = state; }
    }

    public WorkspaceState Update(Func<WorkspaceState, WorkspaceState> mutate)
    {
        ArgumentNullException.ThrowIfNull(mutate);
        lock (_gate)
        {
            var updated = mutate(_state ?? new WorkspaceState())
                ?? throw new ValidationException("The mutation returned a null workspace state.");
            _state = updated;
            return updated;
        }
    }
}
