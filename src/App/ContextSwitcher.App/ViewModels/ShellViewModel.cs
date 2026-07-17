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
        RefreshCommand = new RelayCommand(Refresh);

        Refresh();
    }

    // ---- Observable collections -------------------------------------------
    public ObservableCollection<Project> Projects { get; } = new();
    public ObservableCollection<string> History { get; } = new();
    public IReadOnlyList<SessionOutcome> Outcomes { get; } = Enum.GetValues<SessionOutcome>();

    // ---- Commands ----------------------------------------------------------
    public RelayCommand AddProjectCommand { get; }
    public RelayCommand SwitchCommand { get; }
    public RelayCommand ArchiveCommand { get; }
    public RelayCommand StartSessionCommand { get; }
    public RelayCommand EndSessionCommand { get; }
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
        _sessions.StartSession(SessionObjective);
        SessionObjective = "";
        StatusMessage = "Work session started.";
    }

    private void EndSession()
    {
        var ended = _sessions.EndSession(
            SelectedOutcome, CompletedWork, UnfinishedWork, Blockers, FutureSelfNotes, NextAction);
        CompletedWork = UnfinishedWork = Blockers = FutureSelfNotes = NextAction = "";
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
        RebuildHistory();

        // Restore selection and refresh command availability.
        SelectedProject = previouslySelected is Guid id
            ? Projects.FirstOrDefault(p => p.Id == id)
            : null;
        StartSessionCommand.RaiseCanExecuteChanged();
        EndSessionCommand.RaiseCanExecuteChanged();
        Raise(nameof(ActiveProject));
        Raise(nameof(OpenSession));
    }

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
        History.Clear();
        if (ActiveProject is null)
        {
            return;
        }
        try
        {
            foreach (var s in _sessions.ListSessionsForActiveProject())
            {
                var when = s.StartedUtc.ToLocalTime().ToString("g");
                History.Add(s.IsOpen
                    ? $"{when} — in progress" + (s.Objective.Length > 0 ? $" ({s.Objective})" : "")
                    : $"{when} — {Format(s.WrapUp!.Outcome)}" + (s.Objective.Length > 0 ? $" ({s.Objective})" : ""));
            }
        }
        catch (WorkEngineException)
        {
            // No active project between refreshes; leave history empty.
        }
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
