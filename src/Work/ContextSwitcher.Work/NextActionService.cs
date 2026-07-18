namespace ContextSwitcher.Work;

/// <summary>
/// Application service for per-project next-actions (ADR-0025): a lightweight
/// list of open work items so "what remains unfinished" is explicit and can be
/// surfaced on resume.
///
/// Deterministic and clock-injected like <see cref="WorkSessionService"/>. All
/// persistence goes through <see cref="IWorkspaceStore"/>; the CLI/UI call this
/// service and never touch the store directly. Project resolution is shared via
/// <see cref="ProjectLookup"/> so scoping semantics cannot drift.
/// </summary>
public sealed class NextActionService
{
    private readonly IWorkspaceStore _store;
    private readonly Func<DateTimeOffset> _clock;

    public NextActionService(IWorkspaceStore store, Func<DateTimeOffset>? clock = null)
    {
        _store = store;
        _clock = clock ?? (() => DateTimeOffset.UtcNow);
    }

    /// <summary>Adds an open next-action to a project (by name or id).</summary>
    /// <exception cref="ValidationException">Blank/over-length text or a blank project reference.</exception>
    /// <exception cref="NotFoundException">No project matches the reference.</exception>
    public NextAction AddNextAction(string projectNameOrId, string text)
    {
        var normalized = NextAction.NormalizeText(text);
        var state = _store.Load();
        var project = ProjectLookup.Resolve(state, projectNameOrId);

        var action = new NextAction
        {
            Id = Guid.NewGuid(),
            ProjectId = project.Id,
            Text = normalized,
            CreatedUtc = _clock(),
            Status = NextActionStatus.Open,
            CompletedUtc = null,
        };
        state.NextActions.Add(action);
        _store.Save(state);
        return action;
    }

    /// <summary>
    /// Marks a next-action done. The reference is the action's id, given in
    /// full or as any unambiguous prefix (ids are shown abbreviated). Completing
    /// an already-done action is a calm no-op that returns it unchanged.
    /// </summary>
    /// <exception cref="ValidationException">A blank or ambiguous reference.</exception>
    /// <exception cref="NotFoundException">No action matches the reference.</exception>
    public NextAction CompleteNextAction(string idOrPrefix)
    {
        var query = (idOrPrefix ?? "").Trim();
        if (query.Length == 0)
        {
            throw new ValidationException("A next-action id is required.");
        }
        var state = _store.Load();

        var matches = state.NextActions
            .Select((action, index) => (action, index))
            .Where(x => x.action.Id.ToString().StartsWith(query, StringComparison.OrdinalIgnoreCase))
            .ToList();
        if (matches.Count == 0)
        {
            throw new NotFoundException($"No next-action has the id '{query}'.");
        }
        if (matches.Count > 1)
        {
            throw new ValidationException(
                $"The id '{query}' is ambiguous — it matches {matches.Count} next-actions. " +
                "Provide more characters.");
        }

        var (existing, at) = matches[0];
        if (existing.Status == NextActionStatus.Done)
        {
            return existing; // idempotent
        }
        var done = existing with { Status = NextActionStatus.Done, CompletedUtc = _clock() };
        state.NextActions[at] = done;
        _store.Save(state);
        return done;
    }

    /// <summary>Open next-actions for the active project, oldest first.</summary>
    /// <exception cref="ValidationException">No active project.</exception>
    public IReadOnlyList<NextAction> ListOpenNextActionsForActiveProject()
    {
        var state = _store.Load();
        var activeId = state.ActiveProjectId is Guid id
            ? id
            : throw new ValidationException("There is no active project. Select one first.");
        return NextActionsFor(state, activeId).Where(a => a.IsOpen).ToList();
    }

    /// <summary>
    /// All next-actions (open and done) for any project (by name or id), oldest
    /// first. Does not change the active project.
    /// </summary>
    /// <exception cref="ValidationException">The reference is blank.</exception>
    /// <exception cref="NotFoundException">No project matches.</exception>
    public IReadOnlyList<NextAction> ListNextActions(string projectNameOrId)
    {
        var state = _store.Load();
        var project = ProjectLookup.Resolve(state, projectNameOrId);
        return NextActionsFor(state, project.Id);
    }

    private static IReadOnlyList<NextAction> NextActionsFor(WorkspaceState state, Guid projectId) =>
        state.NextActions
            .Where(a => a.ProjectId == projectId)
            .OrderBy(a => a.CreatedUtc)
            .ToList();
}
