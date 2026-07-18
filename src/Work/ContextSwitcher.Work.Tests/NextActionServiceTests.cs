namespace ContextSwitcher.Work.Tests;

/// <summary>
/// Behavioural tests for <see cref="NextActionService"/> and its resume-brief
/// integration (ADR-0025), against the in-memory store.
/// </summary>
public sealed class NextActionServiceTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 18, 09, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;
    private readonly NextActionService _todos;

    public NextActionServiceTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
        _todos = new NextActionService(_store, () => _now);
    }

    private Project GivenActiveProject(string name = "Alpha") => _projects.CreateProject(name);

    [Test]
    public void Add_stores_an_open_action_on_the_named_project()
    {
        var project = GivenActiveProject();
        var action = _todos.AddNextAction(project.Name, "  wire up the store  ");
        Check.Equal(project.Id, action.ProjectId, "action bound to the project");
        Check.Equal("wire up the store", action.Text, "text trimmed");
        Check.Equal(T0, action.CreatedUtc, "created time recorded");
        Check.That(action.IsOpen, "new action is open");
        Check.Equal(NextActionStatus.Open, action.Status, "status is Open");
        Check.Equal(null, action.CompletedUtc, "open action has no completion time");
    }

    [Test]
    public void Add_defaults_to_the_active_project_when_targeted_by_active_id()
    {
        var project = GivenActiveProject();
        var action = _todos.AddNextAction(project.Id.ToString(), "resolve by id");
        Check.Equal(project.Id, action.ProjectId, "resolved by id");
    }

    [Test]
    public void Add_rejects_blank_text()
    {
        GivenActiveProject();
        Check.Throws<ValidationException>(
            () => _todos.AddNextAction("Alpha", "   "), "blank text rejected");
    }

    [Test]
    public void Add_rejects_overlong_text()
    {
        GivenActiveProject();
        Check.Throws<ValidationException>(
            () => _todos.AddNextAction("Alpha", new string('x', NextAction.MaxTextLength + 1)),
            "over-length text rejected");
    }

    [Test]
    public void Add_to_an_unknown_project_is_not_found()
    {
        GivenActiveProject();
        Check.Throws<NotFoundException>(
            () => _todos.AddNextAction("Nope", "orphan"), "unknown project rejected");
    }

    [Test]
    public void Complete_marks_the_action_done_with_a_completion_time()
    {
        GivenActiveProject();
        var action = _todos.AddNextAction("Alpha", "finish me");
        _now = T0.AddMinutes(30);
        var done = _todos.CompleteNextAction(action.Id.ToString());
        Check.That(!done.IsOpen, "action is closed");
        Check.Equal(NextActionStatus.Done, done.Status, "status is Done");
        Check.Equal(T0.AddMinutes(30), done.CompletedUtc, "completion time recorded");
    }

    [Test]
    public void Complete_accepts_a_unique_id_prefix()
    {
        GivenActiveProject();
        var action = _todos.AddNextAction("Alpha", "by prefix");
        var prefix = action.Id.ToString()[..8];
        var done = _todos.CompleteNextAction(prefix);
        Check.Equal(action.Id, done.Id, "prefix resolved to the action");
        Check.That(!done.IsOpen, "completed via prefix");
    }

    [Test]
    public void Complete_is_idempotent()
    {
        GivenActiveProject();
        var action = _todos.AddNextAction("Alpha", "twice");
        _now = T0.AddMinutes(10);
        _todos.CompleteNextAction(action.Id.ToString());
        _now = T0.AddMinutes(20);
        var again = _todos.CompleteNextAction(action.Id.ToString());
        Check.Equal(T0.AddMinutes(10), again.CompletedUtc, "re-completing keeps the first completion time");
    }

    [Test]
    public void Complete_unknown_id_is_not_found()
    {
        GivenActiveProject();
        _todos.AddNextAction("Alpha", "real one");
        Check.Throws<NotFoundException>(
            () => _todos.CompleteNextAction(Guid.NewGuid().ToString()), "unknown id rejected");
    }

    [Test]
    public void List_open_for_active_project_excludes_done_items()
    {
        GivenActiveProject();
        var keep = _todos.AddNextAction("Alpha", "still open");
        var finish = _todos.AddNextAction("Alpha", "will finish");
        _todos.CompleteNextAction(finish.Id.ToString());

        var open = _todos.ListOpenNextActionsForActiveProject();
        Check.Equal(1, open.Count, "only the open action remains");
        Check.Equal(keep.Id, open[0].Id, "the open action is the surviving one");
    }

    [Test]
    public void List_open_requires_an_active_project()
    {
        Check.Throws<ValidationException>(
            () => _todos.ListOpenNextActionsForActiveProject(), "no active project");
    }

    [Test]
    public void ListNextActions_returns_open_and_done_oldest_first()
    {
        GivenActiveProject();
        var first = _todos.AddNextAction("Alpha", "first");
        _now = T0.AddMinutes(1);
        var second = _todos.AddNextAction("Alpha", "second");
        _todos.CompleteNextAction(first.Id.ToString());

        var all = _todos.ListNextActions("Alpha");
        Check.Equal(2, all.Count, "both open and done listed");
        Check.Equal(first.Id, all[0].Id, "oldest first");
        Check.Equal(second.Id, all[1].Id, "then the newer one");
        Check.That(!all[0].IsOpen, "the completed one is done");
    }

    [Test]
    public void Actions_are_scoped_to_their_project()
    {
        GivenActiveProject("Alpha");
        _todos.AddNextAction("Alpha", "alpha item");
        _projects.CreateProject("Beta");

        var betaActions = _todos.ListNextActions("Beta");
        Check.Equal(0, betaActions.Count, "Beta has no actions");

        _projects.SwitchActiveProject("Beta");
        var betaOpen = _todos.ListOpenNextActionsForActiveProject();
        Check.Equal(0, betaOpen.Count, "active-scope respects the switched project");
    }

    [Test]
    public void Resume_brief_includes_only_open_next_actions()
    {
        GivenActiveProject();
        var open = _todos.AddNextAction("Alpha", "left to do");
        var done = _todos.AddNextAction("Alpha", "already finished");
        _todos.CompleteNextAction(done.Id.ToString());

        // A completed session is required for a resume brief to exist.
        _sessions.StartSession("some work");
        _now = T0.AddHours(1);
        _sessions.EndSession(SessionOutcome.PartiallyCompleted, unfinishedWork: "the rest");

        var brief = _sessions.GetResumeBriefForActiveProject()!;
        Check.Equal(1, brief.OpenNextActions.Count, "brief carries the open action");
        Check.Equal(open.Id, brief.OpenNextActions[0].Id, "the open action is surfaced");
    }
}

/// <summary>
/// Persistence tests for next-actions through <see cref="JsonFileWorkspaceStore"/>
/// (ADR-0025), including additive backward-compatibility.
/// </summary>
public sealed class NextActionPersistenceTests : IDisposable
{
    private readonly string _dir = Path.Combine(
        Path.GetTempPath(), "cs-nextaction-tests-" + Guid.NewGuid().ToString("N"));

    public void Dispose()
    {
        try { Directory.Delete(_dir, recursive: true); } catch (DirectoryNotFoundException) { }
    }

    private JsonFileWorkspaceStore NewStore() => new(_dir);

    [Test]
    public void Next_actions_round_trip_through_disk()
    {
        var store = NewStore();
        var registry = new ProjectRegistry(store);
        registry.CreateProject("Alpha");
        var todos = new NextActionService(store);
        var open = todos.AddNextAction("Alpha", "keep open");
        var toFinish = todos.AddNextAction("Alpha", "finish this");
        todos.CompleteNextAction(toFinish.Id.ToString());

        // Fresh store instance = fresh-process semantics.
        var reloaded = new NextActionService(NewStore());
        var all = reloaded.ListNextActions("Alpha");
        Check.Equal(2, all.Count, "both actions persisted");
        var reloadedOpen = all.First(a => a.Id == open.Id);
        Check.That(reloadedOpen.IsOpen, "open action persisted as open");
        Check.Equal("keep open", reloadedOpen.Text, "text persisted");
        var reloadedDone = all.First(a => a.Id == toFinish.Id);
        Check.That(!reloadedDone.IsOpen, "done action persisted as done");
        Check.That(reloadedDone.CompletedUtc is not null, "completion time persisted");
    }

    [Test]
    public void A_file_without_next_actions_loads_clean()
    {
        // Backward compatibility (ADR-0025): a file written before the
        // next_actions field existed has no such key. It must load, defaulting
        // the collection to empty, without bumping the schema version.
        var store = NewStore();
        Directory.CreateDirectory(_dir);
        File.WriteAllText(store.FilePath,
            """{ "schema_version": "0.1.0", "active_project_id": null, "projects": [], "sessions": [] }""");

        var state = store.Load();
        Check.Equal(0, state.NextActions.Count, "missing next_actions defaults to empty");
        Check.Equal("0.1.0", state.SchemaVersion, "schema version unchanged by the additive field");
    }
}
