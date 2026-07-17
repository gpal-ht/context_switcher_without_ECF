namespace ContextSwitcher.Work;

/// <summary>
/// Application service for the work-session lifecycle and wrap-up (ADR-0009).
///
/// Invariants:
///   * at most one open session exists across the workspace;
///   * a session starts on the active project (there must be one);
///   * ending a session requires an outcome; the reflective wrap-up fields
///     are optional (calm, not punitive).
///
/// Session operations are scoped to the active project for this slice. All
/// persistence goes through <see cref="IWorkspaceStore"/>; the CLI/UI call
/// this service and never touch the store directly.
/// </summary>
public sealed class WorkSessionService
{
    private readonly IWorkspaceStore _store;
    private readonly Func<DateTimeOffset> _clock;

    public WorkSessionService(IWorkspaceStore store, Func<DateTimeOffset>? clock = null)
    {
        _store = store;
        _clock = clock ?? (() => DateTimeOffset.UtcNow);
    }

    /// <summary>Starts a session on the active project.</summary>
    /// <param name="plannedDuration">
    /// Optional focus-timer duration (ADR-0012). Null = untimed.
    /// </param>
    /// <exception cref="ValidationException">
    /// No active project, a session is already open, or an invalid duration.
    /// </exception>
    public WorkSession StartSession(string? objective = null, TimeSpan? plannedDuration = null)
    {
        var normalizedObjective = WorkSession.NormalizeObjective(objective);
        var normalizedPlanned = WorkSession.NormalizePlannedDuration(plannedDuration);

        var state = _store.Load();
        if (FindOpenSession(state) is WorkSession open)
        {
            var project = state.Projects.FirstOrDefault(p => p.Id == open.ProjectId);
            var where = project is null ? "" : $" on '{project.Name}'";
            throw new ValidationException(
                $"A work session is already in progress{where}. End it before starting another.");
        }
        if (state.ActiveProjectId is not Guid activeId)
        {
            throw new ValidationException(
                "There is no active project to start a session on. Select one first.");
        }

        var session = new WorkSession
        {
            Id = Guid.NewGuid(),
            ProjectId = activeId,
            Objective = normalizedObjective,
            StartedUtc = _clock(),
            EndedUtc = null,
            WrapUp = null,
            PlannedDuration = normalizedPlanned,
        };
        state.Sessions.Add(session);
        _store.Save(state);
        return session;
    }

    /// <summary>
    /// Extends ("snoozes") the open session's focus timer so its deadline
    /// becomes now + <paramref name="by"/> — giving a fresh window even if the
    /// timer already elapsed (ADR-0012).
    /// </summary>
    /// <exception cref="ValidationException">No open session, or a non-positive extension.</exception>
    public WorkSession ExtendActiveSession(TimeSpan by)
    {
        if (by <= TimeSpan.Zero)
        {
            throw new ValidationException("The extension must be greater than zero.");
        }
        var state = _store.Load();
        var index = state.Sessions.FindIndex(s => s.IsOpen);
        if (index < 0)
        {
            throw new ValidationException("There is no work session in progress to extend.");
        }
        var open = state.Sessions[index];
        var elapsedSoFar = _clock() - open.StartedUtc;
        var newPlanned = WorkSession.NormalizePlannedDuration(
            (elapsedSoFar > TimeSpan.Zero ? elapsedSoFar : TimeSpan.Zero) + by);
        var extended = open with { PlannedDuration = newPlanned };
        state.Sessions[index] = extended;
        _store.Save(state);
        return extended;
    }

    /// <summary>Ends the open session with a required outcome and optional wrap-up.</summary>
    /// <exception cref="ValidationException">No session is open.</exception>
    public WorkSession EndSession(
        SessionOutcome outcome,
        string? completedWork = null,
        string? unfinishedWork = null,
        string? blockers = null,
        string? futureSelfNotes = null,
        string? nextAction = null)
    {
        var state = _store.Load();
        var index = state.Sessions.FindIndex(s => s.IsOpen);
        if (index < 0)
        {
            throw new ValidationException(
                "There is no work session in progress to end. Start one first.");
        }

        var wrapUp = new WrapUp
        {
            Outcome = outcome,
            CompletedWork = WrapUp.NormalizeField(completedWork, "completed work"),
            UnfinishedWork = WrapUp.NormalizeField(unfinishedWork, "unfinished work"),
            Blockers = WrapUp.NormalizeField(blockers, "blockers"),
            FutureSelfNotes = WrapUp.NormalizeField(futureSelfNotes, "future-self notes"),
            NextAction = WrapUp.NormalizeField(nextAction, "next action"),
        };
        var ended = state.Sessions[index] with { EndedUtc = _clock(), WrapUp = wrapUp };
        state.Sessions[index] = ended;
        _store.Save(state);
        return ended;
    }

    /// <summary>The single open session, or null when none is in progress.</summary>
    public WorkSession? GetOpenSession() => FindOpenSession(_store.Load());

    /// <summary>Session history for the active project, most recent first.</summary>
    /// <exception cref="ValidationException">No active project.</exception>
    public IReadOnlyList<WorkSession> ListSessionsForActiveProject()
    {
        var state = _store.Load();
        var activeId = RequireActiveProjectId(state);
        return SessionsFor(state, activeId);
    }

    /// <summary>
    /// Session history for any project (by name or id), most recent first
    /// (ADR-0014). Does not change the active project.
    /// </summary>
    /// <exception cref="ValidationException">The reference is blank.</exception>
    /// <exception cref="NotFoundException">No project matches.</exception>
    public IReadOnlyList<WorkSession> ListSessions(string projectNameOrId)
    {
        var state = _store.Load();
        var project = ProjectLookup.Resolve(state, projectNameOrId);
        return SessionsFor(state, project.Id);
    }

    private static IReadOnlyList<WorkSession> SessionsFor(WorkspaceState state, Guid projectId) =>
        state.Sessions
            .Where(s => s.ProjectId == projectId)
            .OrderByDescending(s => s.StartedUtc)
            .ToList();

    /// <summary>
    /// Computes focus-trends insights over closed sessions for a scope
    /// (ADR-0015). <paramref name="projectNameOrId"/> null = all projects.
    /// Pure over the stored sessions plus the injected clock (which drives the
    /// week-over-week windows); reads state, writes nothing.
    /// </summary>
    /// <exception cref="ValidationException">A blank project reference.</exception>
    /// <exception cref="NotFoundException">A project reference that matches nothing.</exception>
    public FocusInsights ComputeInsights(string? projectNameOrId = null)
    {
        var state = _store.Load();
        IEnumerable<WorkSession> query = state.Sessions.Where(s => !s.IsOpen);

        string scope = "all projects";
        if (projectNameOrId is not null)
        {
            var project = ProjectLookup.Resolve(state, projectNameOrId);
            query = query.Where(s => s.ProjectId == project.Id);
            scope = project.Name;
        }
        var closed = query.ToList();

        var now = _clock();
        var recentCut = now - TimeSpan.FromDays(7);
        var priorCut = now - TimeSpan.FromDays(14);

        var total = closed.Aggregate(TimeSpan.Zero, (acc, s) => acc + (s.Duration ?? TimeSpan.Zero));
        var outcomeCounts = closed
            .Where(s => s.WrapUp is not null)
            .GroupBy(s => s.WrapUp!.Outcome)
            .ToDictionary(g => g.Key, g => g.Count());

        var timed = closed.Where(s => s.Overrun is not null).ToList();
        var overran = timed.Count(s => s.Overrun!.Value > TimeSpan.Zero);
        TimeSpan? averageOverrun = timed.Count == 0
            ? null
            : TimeSpan.FromTicks((long)timed.Average(s => s.Overrun!.Value.Ticks));

        var recent = closed
            .Where(s => s.StartedUtc >= recentCut)
            .Aggregate(TimeSpan.Zero, (acc, s) => acc + (s.Duration ?? TimeSpan.Zero));
        var prior = closed
            .Where(s => s.StartedUtc >= priorCut && s.StartedUtc < recentCut)
            .Aggregate(TimeSpan.Zero, (acc, s) => acc + (s.Duration ?? TimeSpan.Zero));

        return new FocusInsights
        {
            Scope = scope,
            SessionCount = closed.Count,
            TotalFocus = total,
            AverageFocus = closed.Count == 0 ? null : TimeSpan.FromTicks(total.Ticks / closed.Count),
            OutcomeCounts = outcomeCounts,
            TimedCount = timed.Count,
            OverranCount = overran,
            AverageOverrun = averageOverrun,
            RecentFocus = recent,
            PriorFocus = prior,
        };
    }

    /// <summary>
    /// Resume brief for the active project: the most recent completed session's
    /// reflection, or null when the project has no completed session yet.
    /// </summary>
    /// <exception cref="ValidationException">No active project.</exception>
    public ResumeBrief? GetResumeBriefForActiveProject()
    {
        var state = _store.Load();
        var activeId = RequireActiveProjectId(state);
        var lastClosed = state.Sessions
            .Where(s => s.ProjectId == activeId && !s.IsOpen && s.WrapUp is not null)
            .OrderByDescending(s => s.EndedUtc)
            .FirstOrDefault();
        return lastClosed is null ? null : ResumeBrief.FromSession(lastClosed);
    }

    private static WorkSession? FindOpenSession(WorkspaceState state) =>
        state.Sessions.FirstOrDefault(s => s.IsOpen);

    private static Guid RequireActiveProjectId(WorkspaceState state) =>
        state.ActiveProjectId is Guid id
            ? id
            : throw new ValidationException("There is no active project. Select one first.");
}
