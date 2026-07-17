using System.Collections.ObjectModel;
using ContextSwitcher.Work;

namespace ContextSwitcher.App.ViewModels;

/// <summary>
/// View-model for the shell window (ADR-0011). Binds XAML to the Work Engine
/// services; contains no business logic — every mutating action calls a service
/// and refreshes observable state. Service failures become a friendly
/// <see cref="StatusMessage"/>, never a stack trace in the UI.
/// </summary>
public sealed class ShellViewModel : ObservableObject
{
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;

    public ShellViewModel(ProjectRegistry projects, WorkSessionService sessions)
    {
        _projects = projects;
        _sessions = sessions;

        AddProjectCommand = new RelayCommand(() => Run(AddProject));
        SwitchCommand = new RelayCommand(() => Run(SwitchToSelected), () => SelectedProject is not null);
        ArchiveCommand = new RelayCommand(() => Run(ArchiveSelected), () => SelectedProject is not null);
        StartSessionCommand = new RelayCommand(() => Run(StartSession), () => ActiveProject is not null && OpenSession is null);
        EndSessionCommand = new RelayCommand(() => Run(EndSession), () => OpenSession is not null);
        ExtendCommand = new RelayCommand(() => Run(ExtendSession), () => OpenSession is not null);
        WrapUpNowCommand = new RelayCommand(DismissElapsedPrompt, () => OpenSession is not null);
        RefreshCommand = new RelayCommand(Refresh);

        Refresh();
    }

    /// <summary>Minutes to extend by when the user snoozes the elapsed prompt (ADR-0012).</summary>
    private static readonly TimeSpan ExtendBy = TimeSpan.FromMinutes(5);

    // ---- Observable collections -------------------------------------------
    public ObservableCollection<Project> Projects { get; } = new();
    public ObservableCollection<SessionRow> History { get; } = new();
    public IReadOnlyList<SessionOutcome> Outcomes { get; } = Enum.GetValues<SessionOutcome>();

    // The project whose history the list shows — defaults to the active project
    // but can be any project, without changing the active project (ADR-0014).
    private bool _suppressHistoryReload;
    private Project? _selectedHistoryProject;
    public Project? SelectedHistoryProject
    {
        get => _selectedHistoryProject;
        set { if (Set(ref _selectedHistoryProject, value) && !_suppressHistoryReload) { RebuildHistory(); } }
    }

    private SessionRow? _selectedHistoryRow;
    public SessionRow? SelectedHistoryRow
    {
        get => _selectedHistoryRow;
        set { if (Set(ref _selectedHistoryRow, value)) { SelectedSessionDetail = BuildDetail(value?.Session); } }
    }

    private string _selectedSessionDetail = "Select a session to see its details.";
    public string SelectedSessionDetail { get => _selectedSessionDetail; private set => Set(ref _selectedSessionDetail, value); }

    private string _nextUpText = "";
    public string NextUpText { get => _nextUpText; private set => Set(ref _nextUpText, value); }

    private string _insightsText = "";
    public string InsightsText { get => _insightsText; private set => Set(ref _insightsText, value); }

    private string _blockersText = "";
    public string BlockersText { get => _blockersText; private set => Set(ref _blockersText, value); }

    private string _estimationText = "";
    public string EstimationText { get => _estimationText; private set => Set(ref _estimationText, value); }

    private string _recommendationText = "";
    public string RecommendationText { get => _recommendationText; private set => Set(ref _recommendationText, value); }

    // ---- Commands ----------------------------------------------------------
    public RelayCommand AddProjectCommand { get; }
    public RelayCommand SwitchCommand { get; }
    public RelayCommand ArchiveCommand { get; }
    public RelayCommand StartSessionCommand { get; }
    public RelayCommand EndSessionCommand { get; }
    public RelayCommand ExtendCommand { get; }
    public RelayCommand WrapUpNowCommand { get; }
    public RelayCommand RefreshCommand { get; }

    // ---- New-project inputs ------------------------------------------------
    private string _newProjectName = "";
    public string NewProjectName { get => _newProjectName; set => Set(ref _newProjectName, value); }

    private string _newProjectDescription = "";
    public string NewProjectDescription { get => _newProjectDescription; set => Set(ref _newProjectDescription, value); }

    private Project? _selectedProject;
    public Project? SelectedProject
    {
        get => _selectedProject;
        set { if (Set(ref _selectedProject, value)) { SwitchCommand.RaiseCanExecuteChanged(); ArchiveCommand.RaiseCanExecuteChanged(); } }
    }

    // ---- Session inputs ----------------------------------------------------
    private string _sessionObjective = "";
    public string SessionObjective { get => _sessionObjective; set => Set(ref _sessionObjective, value); }

    private string _sessionMinutes = "";
    public string SessionMinutes { get => _sessionMinutes; set => Set(ref _sessionMinutes, value); }

    private SessionOutcome _selectedOutcome = SessionOutcome.Completed;
    public SessionOutcome SelectedOutcome { get => _selectedOutcome; set => Set(ref _selectedOutcome, value); }

    private string _completedWork = "";
    public string CompletedWork { get => _completedWork; set => Set(ref _completedWork, value); }

    private string _unfinishedWork = "";
    public string UnfinishedWork { get => _unfinishedWork; set => Set(ref _unfinishedWork, value); }

    private string _blockers = "";
    public string Blockers { get => _blockers; set => Set(ref _blockers, value); }

    private string _futureSelfNotes = "";
    public string FutureSelfNotes { get => _futureSelfNotes; set => Set(ref _futureSelfNotes, value); }

    private string _nextAction = "";
    public string NextAction { get => _nextAction; set => Set(ref _nextAction, value); }

    // ---- Derived / display state ------------------------------------------
    public Project? ActiveProject { get; private set; }
    public WorkSession? OpenSession { get; private set; }

    private string _activeProjectText = "";
    public string ActiveProjectText { get => _activeProjectText; private set => Set(ref _activeProjectText, value); }

    private string _sessionStatusText = "";
    public string SessionStatusText { get => _sessionStatusText; private set => Set(ref _sessionStatusText, value); }

    private string _resumeBriefText = "";
    public string ResumeBriefText { get => _resumeBriefText; private set => Set(ref _resumeBriefText, value); }

    private string _statusMessage = "";
    public string StatusMessage { get => _statusMessage; private set => Set(ref _statusMessage, value); }

    // ---- Focus timer (ADR-0012) -------------------------------------------
    private bool _promptDismissed;

    /// <summary>True while the open session carries a focus timer.</summary>
    public bool TimerVisible => OpenSession?.PlannedDuration is not null;

    private string _countdownText = "";
    public string CountdownText { get => _countdownText; private set => Set(ref _countdownText, value); }

    /// <summary>True when the open timed session has passed its deadline.</summary>
    public bool IsTimerElapsed { get; private set; }

    /// <summary>
    /// Two-way bound to the elapsed InfoBar's IsOpen. The bar shows when the
    /// timer has elapsed and the user has not dismissed it; closing it (X) sets
    /// the dismiss flag so it does not immediately reopen (safe escape, ADR-0012).
    /// </summary>
    public bool ElapsedPromptOpen
    {
        get => OpenSession is not null && IsTimerElapsed && !_promptDismissed;
        set { if (!value) { _promptDismissed = true; Raise(); } }
    }

    /// <summary>
    /// Recomputes the countdown from the open session and the current time.
    /// Called by the UI's one-second DispatcherTimer; does not touch the store.
    /// </summary>
    public void Tick()
    {
        var open = OpenSession;
        if (open?.PlannedDuration is null)
        {
            if (CountdownText.Length > 0) CountdownText = "";
            SetElapsed(false);
            return;
        }
        var remaining = open.RemainingAt(DateTimeOffset.UtcNow) ?? TimeSpan.Zero;
        if (remaining > TimeSpan.Zero)
        {
            CountdownText = $"Focus timer: {FormatClock(remaining)} left";
            SetElapsed(false);
        }
        else
        {
            CountdownText = $"Focus time is up — {FormatClock(-remaining)} over";
            SetElapsed(true);
        }
    }

    private void SetElapsed(bool value)
    {
        if (IsTimerElapsed != value)
        {
            IsTimerElapsed = value;
            Raise(nameof(IsTimerElapsed));
        }
        Raise(nameof(ElapsedPromptOpen));
    }

    // ---- Command bodies ----------------------------------------------------
    private void AddProject()
    {
        var project = _projects.CreateProject(NewProjectName, NewProjectDescription);
        NewProjectName = "";
        NewProjectDescription = "";
        StatusMessage = $"Created '{project.Name}'.";
    }

    private void SwitchToSelected()
    {
        var target = SelectedProject ?? throw new ValidationException("Select a project first.");
        var switched = _projects.SwitchActiveProject(target.Id.ToString());
        StatusMessage = $"Active project is now '{switched.Name}'.";
    }

    private void ArchiveSelected()
    {
        var target = SelectedProject ?? throw new ValidationException("Select a project first.");
        var archived = _projects.ArchiveProject(target.Id.ToString());
        StatusMessage = $"Archived '{archived.Name}'.";
    }

    private void StartSession()
    {
        TimeSpan? planned = null;
        var minutesText = SessionMinutes.Trim();
        if (minutesText.Length > 0)
        {
            if (!double.TryParse(minutesText, out var minutes) || minutes <= 0)
            {
                throw new ValidationException("Focus minutes must be a positive number, or left blank.");
            }
            planned = TimeSpan.FromMinutes(minutes);
        }
        _sessions.StartSession(SessionObjective, planned);
        SessionObjective = "";
        SessionMinutes = "";
        _promptDismissed = false;
        StatusMessage = planned is null ? "Work session started." : "Focus session started.";
    }

    private void ExtendSession()
    {
        _sessions.ExtendActiveSession(ExtendBy);
        _promptDismissed = false;
        StatusMessage = $"Extended by {(int)ExtendBy.TotalMinutes} minutes.";
    }

    private void DismissElapsedPrompt()
    {
        _promptDismissed = true;
        Raise(nameof(ElapsedPromptOpen));
        StatusMessage = "Fill in the wrap-up on the right and press End session when ready.";
    }

    private void EndSession()
    {
        var ended = _sessions.EndSession(
            SelectedOutcome, CompletedWork, UnfinishedWork, Blockers, FutureSelfNotes, NextAction);
        CompletedWork = UnfinishedWork = Blockers = FutureSelfNotes = NextAction = "";
        _promptDismissed = false;
        StatusMessage = $"Session ended ({Format(ended.WrapUp!.Outcome)}).";
    }

    /// <summary>Runs a service action, mapping domain failures to a friendly status.</summary>
    private void Run(Action action)
    {
        try
        {
            action();
            Refresh();
        }
        catch (WorkEngineException ex)
        {
            StatusMessage = ex.Message;
        }
        catch (Exception ex)
        {
            StatusMessage = $"Unexpected error: {ex.Message}";
        }
    }

    private void Refresh()
    {
        var previouslySelected = SelectedProject?.Id;

        Projects.Clear();
        foreach (var project in _projects.ListProjects())
        {
            Projects.Add(project);
        }

        ActiveProject = _projects.GetActiveProject();
        ActiveProjectText = ActiveProject is null
            ? "No active project."
            : $"Active project: {ActiveProject.Name}"
              + (ActiveProject.Description.Length > 0 ? $" — {ActiveProject.Description}" : "");

        OpenSession = _sessions.GetOpenSession();
        SessionStatusText = OpenSession is null
            ? "No session in progress."
            : $"In progress since {OpenSession.StartedUtc.ToLocalTime():g}"
              + (OpenSession.Objective.Length > 0 ? $" — {OpenSession.Objective}" : "");

        ResumeBriefText = BuildResumeBrief();
        NextUpText = BuildNextUpText();
        InsightsText = BuildInsightsText();
        BlockersText = BuildBlockersText();
        EstimationText = BuildEstimationText();
        RecommendationText = BuildRecommendationText();

        // Choose which project's history to show: keep the current choice if it
        // still exists, otherwise default to the active project (ADR-0014).
        // Suppress the setter's reload — RebuildHistory runs once, below.
        _suppressHistoryReload = true;
        var desiredHistoryId = SelectedHistoryProject?.Id ?? ActiveProject?.Id;
        SelectedHistoryProject = desiredHistoryId is Guid hid
            ? Projects.FirstOrDefault(p => p.Id == hid)
              ?? (ActiveProject is not null ? Projects.FirstOrDefault(p => p.Id == ActiveProject.Id) : null)
            : null;
        _suppressHistoryReload = false;
        RebuildHistory();

        // Restore selection and refresh command availability.
        SelectedProject = previouslySelected is Guid id
            ? Projects.FirstOrDefault(p => p.Id == id)
            : null;
        StartSessionCommand.RaiseCanExecuteChanged();
        EndSessionCommand.RaiseCanExecuteChanged();
        ExtendCommand.RaiseCanExecuteChanged();
        WrapUpNowCommand.RaiseCanExecuteChanged();
        Raise(nameof(ActiveProject));
        Raise(nameof(OpenSession));
        Raise(nameof(TimerVisible));
        Tick(); // sync the countdown / elapsed prompt to the (possibly new) session
    }

    private string BuildNextUpText()
    {
        var suggestions = _sessions.SuggestNextProject(); // ADR-0019
        if (suggestions.Count == 0)
        {
            return "No active projects yet.";
        }
        return string.Join(Environment.NewLine, suggestions.Take(3).Select((s, i) =>
        {
            var active = s.IsActive ? " (active)" : "";
            var detail = !string.IsNullOrEmpty(s.PendingNextAction) ? s.PendingNextAction : s.Reason;
            return $"{i + 1}. {s.Project}{active} — {detail}";
        }));
    }

    private string BuildInsightsText()
    {
        var ins = _sessions.ComputeInsights(); // all projects (ADR-0015)
        if (ins.SessionCount == 0)
        {
            return "No completed sessions yet — wrap up a session to build focus trends.";
        }
        var lines = new List<string>
        {
            $"{ins.SessionCount} sessions · {FormatSpan(ins.TotalFocus)} total focus",
        };
        if (ins.AverageFocus is TimeSpan avg)
        {
            lines.Add($"Average {FormatSpan(avg)}/session · {ins.CompletionRate * 100:0}% completed");
        }
        if (ins.TimedCount > 0)
        {
            lines.Add($"Estimation: {ins.OverranCount}/{ins.TimedCount} ran over ({FormatSignedSpan(ins.AverageOverrun)})");
        }
        var trend = ins.TrendDirection > 0 ? "up from" : ins.TrendDirection < 0 ? "down from" : "same as";
        lines.Add($"This week: {FormatSpan(ins.RecentFocus)} ({trend} {FormatSpan(ins.PriorFocus)} previous week)");
        return string.Join(Environment.NewLine, lines);
    }

    private string BuildBlockersText()
    {
        var recurring = _sessions.DetectRecurringBlockers(); // all projects, default threshold (ADR-0016)
        if (recurring.Count == 0)
        {
            return "None detected yet.";
        }
        return string.Join(Environment.NewLine,
            recurring.Take(5).Select(b => $"{b.Count}× {b.Text}"));
    }

    private string BuildRecommendationText()
    {
        if (ActiveProject is null)
        {
            return "Select a project to see suggestions for your next session.";
        }
        PlanningRecommendation rec;
        try
        {
            rec = _sessions.RecommendPlanning(ActiveProject.Id.ToString());
        }
        catch (WorkEngineException)
        {
            return "";
        }
        var lines = new List<string>
        {
            rec.SuggestedFocus is TimeSpan focus
                ? $"Suggested focus: {FormatSpan(focus)} ({rec.SuggestedFocusReason})"
                : $"Suggested focus: not enough history yet",
        };
        if (!string.IsNullOrEmpty(rec.PendingNextAction))
        {
            lines.Add($"Pick up where you left off: {rec.PendingNextAction}");
        }
        if (rec.TopBlocker is RecurringBlocker blocker)
        {
            lines.Add($"Watch out for: \"{blocker.Text}\" (blocked you {blocker.Count}×)");
        }
        lines.Add("Suggestions only — you decide.");
        return string.Join(Environment.NewLine, lines);
    }

    private string BuildEstimationText()
    {
        var t = _sessions.ComputeEstimationTrend(); // all projects (ADR-0017)
        if (t.TimedCount == 0)
        {
            return "No timed sessions yet — set a focus timer to track this.";
        }
        var lines = new List<string>
        {
            $"{t.AverageAccuracyPercent:0}% accurate over {t.TimedCount} timed sessions",
            t.Bias switch
            {
                EstimationBias.UnderEstimates => $"Tends to under-estimate (runs ~{FormatSpan(t.AverageError)} over)",
                EstimationBias.OverEstimates => $"Tends to over-estimate (finishes ~{FormatSpan(-t.AverageError)} early)",
                _ => "Well-calibrated (within ~10% of plan)",
            },
        };
        if (t.Improving is bool improving)
        {
            var word = improving ? "improving"
                     : t.RecentAccuracyPercent < t.EarlierAccuracyPercent ? "declining" : "steady";
            lines.Add($"Trend: {word} (recent {t.RecentAccuracyPercent:0}% vs earlier {t.EarlierAccuracyPercent:0}%)");
        }
        return string.Join(Environment.NewLine, lines);
    }

    private static string FormatSpan(TimeSpan d)
    {
        if (d < TimeSpan.Zero) d = TimeSpan.Zero;
        return d.TotalHours >= 1 ? $"{(int)d.TotalHours}h {d.Minutes}m"
             : d.TotalMinutes >= 1 ? $"{d.Minutes}m" : $"{d.Seconds}s";
    }

    private static string FormatSignedSpan(TimeSpan? span) => span switch
    {
        null => "no plans",
        { } o when o > TimeSpan.Zero => $"avg {FormatSpan(o)} over plan",
        { } o when o < TimeSpan.Zero => $"avg {FormatSpan(-o)} under plan",
        _ => "on plan",
    };

    private string BuildResumeBrief()
    {
        if (ActiveProject is null)
        {
            return "";
        }
        ResumeBrief? brief;
        try
        {
            brief = _sessions.GetResumeBriefForActiveProject();
        }
        catch (WorkEngineException)
        {
            return "";
        }
        if (brief is null)
        {
            return "No previous wrap-up yet — this is a fresh start.";
        }
        var lines = new List<string> { $"Last session: {Format(brief.Outcome)} ({brief.EndedUtc.ToLocalTime():g})" };
        if (brief.UnfinishedWork.Length > 0) lines.Add($"Unfinished: {brief.UnfinishedWork}");
        if (brief.Blockers.Length > 0) lines.Add($"Blockers: {brief.Blockers}");
        if (brief.FutureSelfNotes.Length > 0) lines.Add($"Notes: {brief.FutureSelfNotes}");
        if (brief.NextAction.Length > 0) lines.Add($"Next action: {brief.NextAction}");
        return string.Join(Environment.NewLine, lines);
    }

    private void RebuildHistory()
    {
        var previouslySelected = SelectedHistoryRow?.Session.Id;
        History.Clear();
        if (SelectedHistoryProject is Project historyProject)
        {
            try
            {
                foreach (var s in _sessions.ListSessions(historyProject.Id.ToString()))
                {
                    var when = s.StartedUtc.ToLocalTime().ToString("g");
                    var objective = s.Objective.Length > 0 ? $" ({s.Objective})" : "";
                    var summary = s.IsOpen
                        ? $"{when} — in progress{objective}"
                        : $"{when} — {Format(s.WrapUp!.Outcome)}, {FormatClock(s.Duration ?? TimeSpan.Zero)}{objective}";
                    History.Add(new SessionRow { Session = s, Summary = summary });
                }
            }
            catch (WorkEngineException)
            {
                // No active project between refreshes; leave history empty.
            }
        }

        // Preserve the selection across a refresh when the same session is still present.
        SelectedHistoryRow = previouslySelected is Guid id
            ? History.FirstOrDefault(r => r.Session.Id == id)
            : null;
    }

    private string BuildDetail(WorkSession? s)
    {
        if (s is null)
        {
            return "Select a session to see its details.";
        }
        var lines = new List<string>();
        if (s.Objective.Length > 0) lines.Add($"Objective: {s.Objective}");
        lines.Add($"Started: {s.StartedUtc.ToLocalTime():g}");
        if (s.IsOpen)
        {
            lines.Add("Status: in progress");
            return string.Join(Environment.NewLine, lines);
        }
        lines.Add($"Ended: {s.EndedUtc!.Value.ToLocalTime():g}");
        lines.Add($"Duration: {FormatClock(s.Duration ?? TimeSpan.Zero)}");
        if (s.PlannedDuration is TimeSpan planned)
        {
            lines.Add($"Planned: {FormatClock(planned)} ({FormatOverrun(s.Overrun)})");
        }
        lines.Add($"Outcome: {Format(s.WrapUp!.Outcome)}");
        if (s.WrapUp!.CompletedWork.Length > 0) lines.Add($"Completed: {s.WrapUp.CompletedWork}");
        if (s.WrapUp!.UnfinishedWork.Length > 0) lines.Add($"Unfinished: {s.WrapUp.UnfinishedWork}");
        if (s.WrapUp!.Blockers.Length > 0) lines.Add($"Blockers: {s.WrapUp.Blockers}");
        if (s.WrapUp!.FutureSelfNotes.Length > 0) lines.Add($"Notes: {s.WrapUp.FutureSelfNotes}");
        if (s.WrapUp!.NextAction.Length > 0) lines.Add($"Next action: {s.WrapUp.NextAction}");
        return string.Join(Environment.NewLine, lines);
    }

    private static string FormatOverrun(TimeSpan? overrun) => overrun switch
    {
        null => "no plan",
        { } o when o > TimeSpan.Zero => $"{FormatClock(o)} over",
        { } o when o < TimeSpan.Zero => $"{FormatClock(-o)} early",
        _ => "on time",
    };

    private static string FormatClock(TimeSpan t)
    {
        if (t < TimeSpan.Zero) t = TimeSpan.Zero;
        return t.TotalHours >= 1
            ? $"{(int)t.TotalHours}h {t.Minutes:00}m"
            : $"{t.Minutes:00}:{t.Seconds:00}";
    }

    private static string Format(SessionOutcome outcome)
    {
        var name = outcome.ToString();
        var chars = new List<char>(name.Length + 4);
        for (var i = 0; i < name.Length; i++)
        {
            if (i > 0 && char.IsUpper(name[i])) chars.Add('-');
            chars.Add(char.ToLowerInvariant(name[i]));
        }
        return new string(chars.ToArray());
    }
}
