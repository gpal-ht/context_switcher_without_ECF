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
    /// Detects blockers recorded across multiple closed sessions (ADR-0016).
    /// Groups the wrap-up Blockers field case- and whitespace-insensitively and
    /// keeps those seen in <paramref name="minOccurrences"/>+ sessions, most
    /// frequent first (ties broken by most recent). Scope: one project (via the
    /// shared <see cref="ProjectLookup"/>) or all projects (<c>null</c>). Pure
    /// over the stored sessions; reads state, writes nothing.
    /// </summary>
    /// <exception cref="ValidationException">A blank project reference.</exception>
    /// <exception cref="NotFoundException">A project reference that matches nothing.</exception>
    public IReadOnlyList<RecurringBlocker> DetectRecurringBlockers(
        string? projectNameOrId = null, int minOccurrences = 2)
    {
        if (minOccurrences < 1)
        {
            minOccurrences = 1;
        }
        var state = _store.Load();
        IEnumerable<WorkSession> query = state.Sessions.Where(s => !s.IsOpen && s.WrapUp is not null);
        if (projectNameOrId is not null)
        {
            var project = ProjectLookup.Resolve(state, projectNameOrId);
            query = query.Where(s => s.ProjectId == project.Id);
        }

        var entries = query
            .Select(s => (Text: s.WrapUp!.Blockers.Trim(), When: s.EndedUtc ?? s.StartedUtc))
            .Where(e => e.Text.Length > 0)
            .ToList();

        return entries
            .GroupBy(e => NormalizeBlocker(e.Text))
            .Where(g => g.Count() >= minOccurrences)
            .Select(g =>
            {
                var latest = g.OrderByDescending(e => e.When).First();
                return new RecurringBlocker { Text = latest.Text, Count = g.Count(), LastSeenUtc = latest.When };
            })
            .OrderByDescending(b => b.Count)
            .ThenByDescending(b => b.LastSeenUtc)
            .ToList();
    }

    /// <summary>
    /// A read-only, data-derived recommendation for planning the next session
    /// (ADR-0018). Default scope is the ACTIVE project (planning is about the
    /// next session); a reference targets that project. Composes a suggested
    /// focus length (median of recent sessions), the pending next action, and
    /// the top recurring blocker. Pure over the stored sessions; writes and
    /// applies nothing.
    /// </summary>
    /// <exception cref="ValidationException">A blank reference, or no active project when defaulting.</exception>
    /// <exception cref="NotFoundException">A reference that matches nothing.</exception>
    public PlanningRecommendation RecommendPlanning(string? projectNameOrId = null)
    {
        var state = _store.Load();
        Project project;
        if (projectNameOrId is not null)
        {
            project = ProjectLookup.Resolve(state, projectNameOrId);
        }
        else if (state.ActiveProjectId is Guid activeId
                 && state.Projects.FirstOrDefault(p => p.Id == activeId) is Project active)
        {
            project = active;
        }
        else
        {
            throw new ValidationException("There is no active project to plan for. Select one first.");
        }

        var closed = state.Sessions
            .Where(s => s.ProjectId == project.Id && !s.IsOpen)
            .OrderByDescending(s => s.StartedUtc)
            .ToList();
        var recent = closed.Take(5).ToList();

        TimeSpan? suggested = null;
        string reason;
        if (recent.Count < 2)
        {
            reason = "Not enough history yet — pick a focus length you are comfortable with.";
        }
        else
        {
            var median = Median(recent.Select(s => s.Duration ?? TimeSpan.Zero));
            var minutes = Math.Max(5, Math.Round(median.TotalMinutes / 5.0) * 5);
            suggested = TimeSpan.FromMinutes(minutes);
            reason = $"Based on your {recent.Count} most recent sessions.";
        }

        var pending = closed
            .Select(s => s.WrapUp?.NextAction)
            .FirstOrDefault(a => !string.IsNullOrWhiteSpace(a));

        var blockers = DetectRecurringBlockers(project.Id.ToString());
        var topBlocker = blockers.Count > 0 ? blockers[0] : null;

        return new PlanningRecommendation
        {
            Scope = project.Name,
            SuggestedFocus = suggested,
            SuggestedFocusReason = reason,
            PendingNextAction = pending,
            TopBlocker = topBlocker,
        };
    }

    /// <summary>
    /// Ranks the non-archived projects to suggest which to pick up next
    /// (ADR-0019): projects with a pending next action first, then most
    /// recently worked, then by name. Reports each project's last-worked time,
    /// pending next action, and a plain-language reason. Pure over the stored
    /// projects/sessions; reads state, writes and selects nothing.
    /// </summary>
    public IReadOnlyList<NextProjectSuggestion> SuggestNextProject()
    {
        var state = _store.Load();
        var activeId = state.ActiveProjectId;

        var suggestions = state.Projects
            .Where(p => p.Status == ProjectStatus.Active)
            .Select(p =>
            {
                var projectSessions = state.Sessions
                    .Where(s => s.ProjectId == p.Id)
                    .OrderByDescending(s => s.StartedUtc)
                    .ToList();
                DateTimeOffset? lastWorked = projectSessions.Count > 0 ? projectSessions[0].StartedUtc : null;
                var pending = projectSessions
                    .Select(s => s.WrapUp?.NextAction)
                    .FirstOrDefault(a => !string.IsNullOrWhiteSpace(a));

                var reason = !string.IsNullOrWhiteSpace(pending) ? "You left off with a clear next step."
                    : lastWorked is not null ? "Recently active."
                    : "Not started yet.";

                return new NextProjectSuggestion
                {
                    Project = p.Name,
                    IsActive = p.Id == activeId,
                    LastWorkedUtc = lastWorked,
                    PendingNextAction = pending,
                    Reason = reason,
                };
            })
            .OrderByDescending(s => s.PendingNextAction is not null)
            .ThenByDescending(s => s.LastWorkedUtc ?? DateTimeOffset.MinValue)
            .ThenBy(s => s.Project, StringComparer.OrdinalIgnoreCase)
            .ToList();

        return suggestions;
    }

    private static TimeSpan Median(IEnumerable<TimeSpan> values)
    {
        var sorted = values.OrderBy(v => v).ToList();
        var n = sorted.Count;
        if (n == 0)
        {
            return TimeSpan.Zero;
        }
        return n % 2 == 1
            ? sorted[n / 2]
            : TimeSpan.FromTicks((sorted[n / 2 - 1].Ticks + sorted[n / 2].Ticks) / 2);
    }

    /// <summary>Grouping key for a blocker: lowercased, whitespace-collapsed.</summary>
    private static string NormalizeBlocker(string text) =>
        string.Join(' ', text.ToLowerInvariant()
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries));

    /// <summary>
    /// Computes estimation-accuracy trends over closed, timed sessions for a
    /// scope (ADR-0017): mean accuracy, over/under bias, and a recent-vs-earlier
    /// directional trend. Scope: one project (via the shared
    /// <see cref="ProjectLookup"/>) or all projects (<c>null</c>). Pure over the
    /// stored sessions; reads state, writes nothing.
    /// </summary>
    /// <exception cref="ValidationException">A blank project reference.</exception>
    /// <exception cref="NotFoundException">A project reference that matches nothing.</exception>
    public EstimationTrend ComputeEstimationTrend(string? projectNameOrId = null)
    {
        var state = _store.Load();
        IEnumerable<WorkSession> query = state.Sessions.Where(s => !s.IsOpen && s.EstimationAccuracy is not null);

        string scope = "all projects";
        if (projectNameOrId is not null)
        {
            var project = ProjectLookup.Resolve(state, projectNameOrId);
            query = query.Where(s => s.ProjectId == project.Id);
            scope = project.Name;
        }
        // Oldest -> newest so the trend split is chronological.
        var timed = query.OrderBy(s => s.StartedUtc).ToList();

        if (timed.Count == 0)
        {
            return new EstimationTrend
            {
                Scope = scope,
                TimedCount = 0,
                AverageAccuracyPercent = 0,
                AverageError = TimeSpan.Zero,
                Bias = EstimationBias.WellCalibrated,
            };
        }

        var averageAccuracy = timed.Average(s => s.EstimationAccuracy!.Value) * 100.0;
        var averageErrorTicks = (long)timed.Average(s => s.Overrun!.Value.Ticks);
        var averageError = TimeSpan.FromTicks(averageErrorTicks);
        var averagePlannedTicks = timed.Average(s => s.PlannedDuration!.Value.Ticks);

        // Within +/-10% of the average plan counts as well-calibrated.
        var bias = Math.Abs(averageErrorTicks) <= 0.10 * averagePlannedTicks
            ? EstimationBias.WellCalibrated
            : averageErrorTicks > 0 ? EstimationBias.UnderEstimates : EstimationBias.OverEstimates;

        double? recentPct = null, earlierPct = null;
        bool? improving = null;
        if (timed.Count >= 2)
        {
            var split = timed.Count / 2; // recent half takes the extra when odd
            earlierPct = timed.Take(split).Average(s => s.EstimationAccuracy!.Value) * 100.0;
            recentPct = timed.Skip(split).Average(s => s.EstimationAccuracy!.Value) * 100.0;
            improving = recentPct > earlierPct;
        }

        return new EstimationTrend
        {
            Scope = scope,
            TimedCount = timed.Count,
            AverageAccuracyPercent = averageAccuracy,
            AverageError = averageError,
            Bias = bias,
            RecentAccuracyPercent = recentPct,
            EarlierAccuracyPercent = earlierPct,
            Improving = improving,
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
        if (lastClosed is null)
        {
            return null;
        }
        // Fold in recent notes/decisions so returning to a project surfaces the
        // captured knowledge alongside the last session's reflection (ADR-0024).
        var recentKnowledge = state.Knowledge
            .Where(k => k.ProjectId == activeId)
            .OrderByDescending(k => k.CreatedUtc)
            .Take(KnowledgeService.RecentOnResume)
            .ToList();
        return ResumeBrief.FromSession(lastClosed, recentKnowledge);
    }

    private static WorkSession? FindOpenSession(WorkspaceState state) =>
        state.Sessions.FirstOrDefault(s => s.IsOpen);

    private static Guid RequireActiveProjectId(WorkspaceState state) =>
        state.ActiveProjectId is Guid id
            ? id
            : throw new ValidationException("There is no active project. Select one first.");
}
