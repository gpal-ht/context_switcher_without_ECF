namespace ContextSwitcher.Work.Tests;

/// <summary>Lifecycle + wrap-up tests for <see cref="WorkSessionService"/> (in-memory store).</summary>
public sealed class WorkSessionServiceTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 17, 09, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;

    public WorkSessionServiceTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
    }

    private Project GivenActiveProject(string name = "Alpha")
    {
        var project = _projects.CreateProject(name);
        return project; // first project auto-activates
    }

    [Test]
    public void Start_requires_an_active_project()
    {
        Check.Throws<ValidationException>(() => _sessions.StartSession(), "no active project");
    }

    [Test]
    public void Start_opens_a_session_on_the_active_project()
    {
        var project = GivenActiveProject();
        var session = _sessions.StartSession("  design the API  ");
        Check.Equal(project.Id, session.ProjectId, "session bound to active project");
        Check.Equal("design the API", session.Objective, "objective trimmed");
        Check.Equal(T0, session.StartedUtc, "start time recorded");
        Check.That(session.IsOpen, "new session is open");
        Check.Equal(null, session.Duration, "open session has no duration");
        Check.Equal(session.Id, _sessions.GetOpenSession()!.Id, "open session is reported");
    }

    [Test]
    public void Cannot_start_a_second_session_while_one_is_open()
    {
        GivenActiveProject();
        _sessions.StartSession();
        Check.Throws<ValidationException>(() => _sessions.StartSession(), "second start blocked");
    }

    [Test]
    public void Overlong_objective_is_rejected()
    {
        GivenActiveProject();
        Check.Throws<ValidationException>(
            () => _sessions.StartSession(new string('x', WorkSession.MaxObjectiveLength + 1)),
            "over-length objective");
    }

    [Test]
    public void End_requires_an_open_session()
    {
        GivenActiveProject();
        Check.Throws<ValidationException>(
            () => _sessions.EndSession(SessionOutcome.Completed), "nothing to end");
    }

    [Test]
    public void End_records_outcome_wrapup_and_duration()
    {
        GivenActiveProject();
        _sessions.StartSession("ship it");
        _now = T0.AddMinutes(90);
        var ended = _sessions.EndSession(
            SessionOutcome.PartiallyCompleted,
            completedWork: "  wired the store  ",
            unfinishedWork: "the UI",
            blockers: "none",
            futureSelfNotes: "watch the clock skew",
            nextAction: "write tests");

        Check.That(!ended.IsOpen, "session is closed");
        Check.Equal(T0.AddMinutes(90), ended.EndedUtc, "end time recorded");
        Check.Equal(TimeSpan.FromMinutes(90), ended.Duration, "duration computed");
        Check.Equal(SessionOutcome.PartiallyCompleted, ended.WrapUp!.Outcome, "outcome stored");
        Check.Equal("wired the store", ended.WrapUp!.CompletedWork, "completed work trimmed");
        Check.Equal("write tests", ended.WrapUp!.NextAction, "next action stored");
        Check.Equal(null, _sessions.GetOpenSession(), "no open session after end");
    }

    [Test]
    public void End_after_start_lets_a_new_session_begin()
    {
        GivenActiveProject();
        _sessions.StartSession();
        _sessions.EndSession(SessionOutcome.Completed);
        var second = _sessions.StartSession(); // must not throw
        Check.That(second.IsOpen, "a fresh session opens after the prior one ended");
    }

    [Test]
    public void Duration_is_clamped_to_non_negative_under_clock_skew()
    {
        GivenActiveProject();
        _now = T0.AddMinutes(10);
        _sessions.StartSession();
        _now = T0; // clock went backwards
        var ended = _sessions.EndSession(SessionOutcome.Interrupted);
        Check.Equal(TimeSpan.Zero, ended.Duration, "negative duration clamped to zero");
    }

    [Test]
    public void History_lists_active_project_sessions_newest_first()
    {
        GivenActiveProject();
        _sessions.StartSession("first");
        _now = T0.AddHours(1);
        _sessions.EndSession(SessionOutcome.Completed);
        _now = T0.AddHours(2);
        _sessions.StartSession("second");

        var history = _sessions.ListSessionsForActiveProject();
        Check.Equal(2, history.Count, "two sessions");
        Check.Equal("second", history[0].Objective, "newest first");
        Check.Equal("first", history[1].Objective, "oldest last");
    }

    [Test]
    public void History_is_scoped_to_the_active_project()
    {
        GivenActiveProject("Alpha");
        _sessions.StartSession("alpha work");
        _sessions.EndSession(SessionOutcome.Completed);

        _projects.CreateProject("Beta");
        _projects.SwitchActiveProject("Beta");

        var betaHistory = _sessions.ListSessionsForActiveProject();
        Check.Equal(0, betaHistory.Count, "Beta has no sessions");
    }

    [Test]
    public void Resume_brief_is_the_last_completed_session()
    {
        GivenActiveProject();
        _sessions.StartSession("old");
        _now = T0.AddHours(1);
        _sessions.EndSession(SessionOutcome.Blocked, unfinishedWork: "old work", blockers: "waiting on X");
        _now = T0.AddHours(2);
        _sessions.StartSession("newer");
        _now = T0.AddHours(3);
        _sessions.EndSession(SessionOutcome.DecisionReached,
            blockers: "resolved", nextAction: "implement the decision");

        var brief = _sessions.GetResumeBriefForActiveProject()!;
        Check.Equal(SessionOutcome.DecisionReached, brief.Outcome, "most recent outcome");
        Check.Equal("implement the decision", brief.NextAction, "most recent next action");
        Check.Equal("resolved", brief.Blockers, "most recent blockers");
    }

    [Test]
    public void Resume_brief_is_null_without_a_completed_session()
    {
        GivenActiveProject();
        Check.Equal(null, _sessions.GetResumeBriefForActiveProject(), "no completed session yet");
        _sessions.StartSession(); // open, not closed
        Check.Equal(null, _sessions.GetResumeBriefForActiveProject(), "open session is not a resume brief");
    }
}
