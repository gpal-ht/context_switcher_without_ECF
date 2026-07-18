namespace ContextSwitcher.Work;

/// <summary>
/// Application service for capturing and surfacing project knowledge — notes
/// and decisions (ADR-0024). Deterministic and clock-injected, mirroring
/// <see cref="WorkSessionService"/>: every entry is timestamped from the
/// injected clock, and all persistence goes through <see cref="IWorkspaceStore"/>.
///
/// Knowledge is append-only. A capture targets a project by name/id, or the
/// active project when the reference is omitted (null). Project resolution is
/// delegated to the shared <see cref="ProjectLookup"/> so this service cannot
/// drift from the rest of the engine on what a project reference means.
/// </summary>
public sealed class KnowledgeService
{
    /// <summary>How many recent entries a resume brief folds in (ADR-0024).</summary>
    public const int RecentOnResume = 5;

    private readonly IWorkspaceStore _store;
    private readonly Func<DateTimeOffset> _clock;

    public KnowledgeService(IWorkspaceStore store, Func<DateTimeOffset>? clock = null)
    {
        _store = store;
        _clock = clock ?? (() => DateTimeOffset.UtcNow);
    }

    /// <summary>
    /// Captures a free-form note against a project (the active project when
    /// <paramref name="projectNameOrId"/> is null).
    /// </summary>
    /// <exception cref="ValidationException">Empty text, or no active project when defaulting.</exception>
    /// <exception cref="NotFoundException">A project reference that matches nothing.</exception>
    public KnowledgeEntry AddNote(string? projectNameOrId, string text)
    {
        var normalizedText = KnowledgeEntry.NormalizeText(text);
        var state = _store.Load();
        var project = ResolveTarget(state, projectNameOrId);

        var entry = new KnowledgeEntry
        {
            Id = Guid.NewGuid(),
            ProjectId = project.Id,
            Kind = KnowledgeKind.Note,
            Text = normalizedText,
            Rationale = "",
            CreatedUtc = _clock(),
        };
        state.Knowledge.Add(entry);
        _store.Save(state);
        return entry;
    }

    /// <summary>
    /// Captures a decision against a project (the active project when
    /// <paramref name="projectNameOrId"/> is null), with an optional rationale.
    /// </summary>
    /// <exception cref="ValidationException">Empty text, or no active project when defaulting.</exception>
    /// <exception cref="NotFoundException">A project reference that matches nothing.</exception>
    public KnowledgeEntry AddDecision(string? projectNameOrId, string text, string? rationale = null)
    {
        var normalizedText = KnowledgeEntry.NormalizeText(text);
        var normalizedRationale = KnowledgeEntry.NormalizeRationale(rationale);
        var state = _store.Load();
        var project = ResolveTarget(state, projectNameOrId);

        var entry = new KnowledgeEntry
        {
            Id = Guid.NewGuid(),
            ProjectId = project.Id,
            Kind = KnowledgeKind.Decision,
            Text = normalizedText,
            Rationale = normalizedRationale,
            CreatedUtc = _clock(),
        };
        state.Knowledge.Add(entry);
        _store.Save(state);
        return entry;
    }

    /// <summary>Knowledge for the active project, most recent first.</summary>
    /// <exception cref="ValidationException">No active project.</exception>
    public IReadOnlyList<KnowledgeEntry> ListKnowledgeForActiveProject()
    {
        var state = _store.Load();
        var project = RequireActiveProject(state);
        return KnowledgeFor(state, project.Id);
    }

    /// <summary>
    /// Knowledge for any project (by name or id), most recent first. Does not
    /// change the active project.
    /// </summary>
    /// <exception cref="ValidationException">The reference is blank.</exception>
    /// <exception cref="NotFoundException">No project matches.</exception>
    public IReadOnlyList<KnowledgeEntry> ListKnowledge(string projectNameOrId)
    {
        var state = _store.Load();
        var project = ProjectLookup.Resolve(state, projectNameOrId);
        return KnowledgeFor(state, project.Id);
    }

    private static IReadOnlyList<KnowledgeEntry> KnowledgeFor(WorkspaceState state, Guid projectId) =>
        state.Knowledge
            .Where(k => k.ProjectId == projectId)
            .OrderByDescending(k => k.CreatedUtc)
            .ToList();

    /// <summary>The named/id'd project, or the active project when the reference is null.</summary>
    private static Project ResolveTarget(WorkspaceState state, string? projectNameOrId)
    {
        if (projectNameOrId is not null)
        {
            return ProjectLookup.Resolve(state, projectNameOrId);
        }
        return RequireActiveProject(state);
    }

    private static Project RequireActiveProject(WorkspaceState state) =>
        state.ActiveProjectId is Guid activeId
        && state.Projects.FirstOrDefault(p => p.Id == activeId) is Project active
            ? active
            : throw new ValidationException("There is no active project. Select one first.");
}
