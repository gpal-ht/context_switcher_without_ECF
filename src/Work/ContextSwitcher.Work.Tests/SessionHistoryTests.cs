namespace ContextSwitcher.Work.Tests;

/// <summary>Tests for the session-history detail measures (ADR-0013).</summary>
public sealed class SessionHistoryTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 17, 09, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;

    public SessionHistoryTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
        _projects.CreateProject("Alpha");
    }

    [Test]
    public void Overrun_is_positive_when_a_timed_session_runs_over()
    {
        _sessions.StartSession("focus", TimeSpan.FromMinutes(25));
        _now = T0.AddMinutes(30);
        var ended = _sessions.EndSession(SessionOutcome.Completed);
        Check.Equal(TimeSpan.FromMinutes(5), ended.Overrun, "5 minutes over the 25-minute plan");
    }

    [Test]
    public void Overrun_is_negative_when_a_timed_session_finishes_early()
    {
        _sessions.StartSession("focus", TimeSpan.FromMinutes(25));
        _now = T0.AddMinutes(20);
        var ended = _sessions.EndSession(SessionOutcome.Completed);
        Check.Equal(TimeSpan.FromMinutes(-5), ended.Overrun, "5 minutes under the plan");
    }

    [Test]
    public void Overrun_is_null_for_untimed_or_open_sessions()
    {
        var open = _sessions.StartSession("untimed");
        Check.Equal(null, open.Overrun, "open + untimed has no overrun");

        var timedOpen = _sessions.GetOpenSession();
        // still the same untimed open session
        Check.Equal(null, timedOpen!.Overrun, "open session has no overrun");

        _now = T0.AddMinutes(10);
        var ended = _sessions.EndSession(SessionOutcome.Completed);
        Check.Equal(null, ended.Overrun, "closed but untimed has no overrun");
    }

    [Test]
    public void History_entries_expose_full_detail_for_review()
    {
        _sessions.StartSession("design the API", TimeSpan.FromMinutes(25));
        _now = T0.AddMinutes(30);
        _sessions.EndSession(
            SessionOutcome.PartiallyCompleted,
            completedWork: "sketched the port",
            unfinishedWork: "the adapter",
            nextAction: "write the adapter");

        var latest = _sessions.ListSessionsForActiveProject()[0];
        Check.Equal("design the API", latest.Objective, "objective preserved for review");
        Check.Equal(TimeSpan.FromMinutes(30), latest.Duration, "actual duration available");
        Check.Equal(TimeSpan.FromMinutes(5), latest.Overrun, "overrun available");
        Check.Equal(SessionOutcome.PartiallyCompleted, latest.WrapUp!.Outcome, "outcome available");
        Check.Equal("the adapter", latest.WrapUp!.UnfinishedWork, "wrap-up fields readable");
        Check.Equal("write the adapter", latest.WrapUp!.NextAction, "next action readable");
    }
}
