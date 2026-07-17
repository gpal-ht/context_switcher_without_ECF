namespace ContextSwitcher.Work.Tests;

/// <summary>Tests for personalized planning recommendations (ADR-0018).</summary>
public sealed class PlanningRecommendationTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 17, 09, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;

    public PlanningRecommendationTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
        _projects.CreateProject("Alpha");
    }

    private void RunSession(TimeSpan length, string? nextAction = null, string? blockers = null)
    {
        _sessions.StartSession("work");
        _now = _now.AddMinutes(length.TotalMinutes);
        _sessions.EndSession(SessionOutcome.Completed, nextAction: nextAction, blockers: blockers);
        _now = _now.AddMinutes(5); // gap between sessions
    }

    [Test]
    public void No_active_project_to_plan_for_is_rejected()
    {
        // Fresh workspace with no projects.
        var store = new InMemoryWorkspaceStore();
        var svc = new WorkSessionService(store, () => _now);
        Check.Throws<ValidationException>(() => svc.RecommendPlanning(), "no active project");
    }

    [Test]
    public void Suggests_the_median_recent_duration_rounded_to_five_minutes()
    {
        RunSession(TimeSpan.FromMinutes(20));
        RunSession(TimeSpan.FromMinutes(32));
        RunSession(TimeSpan.FromMinutes(40)); // median of {20,32,40} = 32 -> 30m

        var rec = _sessions.RecommendPlanning();
        Check.Equal("Alpha", rec.Scope, "recommends for the active project");
        Check.Equal(TimeSpan.FromMinutes(30), rec.SuggestedFocus, "median 32m rounds to 30m");
        Check.That(rec.SuggestedFocusReason.Contains("3"), "reason cites the number of recent sessions");
    }

    [Test]
    public void Median_uses_middle_value_and_ignores_a_single_outlier()
    {
        RunSession(TimeSpan.FromMinutes(25));
        RunSession(TimeSpan.FromMinutes(25));
        RunSession(TimeSpan.FromMinutes(180)); // outlier; median of {25,25,180} = 25 -> 25m

        Check.Equal(TimeSpan.FromMinutes(25), _sessions.RecommendPlanning().SuggestedFocus,
            "an outlier does not skew the median-based suggestion");
    }

    [Test]
    public void No_suggestion_until_there_is_enough_history()
    {
        var rec0 = _sessions.RecommendPlanning();
        Check.Equal(null, rec0.SuggestedFocus, "no sessions -> no number");
        Check.That(rec0.SuggestedFocusReason.Length > 0, "still explains why");

        RunSession(TimeSpan.FromMinutes(30));
        Check.Equal(null, _sessions.RecommendPlanning().SuggestedFocus, "one session is not enough");

        RunSession(TimeSpan.FromMinutes(30));
        Check.Equal(TimeSpan.FromMinutes(30), _sessions.RecommendPlanning().SuggestedFocus,
            "two sessions is enough to suggest");
    }

    [Test]
    public void Surfaces_the_latest_pending_next_action()
    {
        RunSession(TimeSpan.FromMinutes(30), nextAction: "write the adapter");
        RunSession(TimeSpan.FromMinutes(30)); // no next action
        // The most recent session that noted a next action wins.
        Check.Equal("write the adapter", _sessions.RecommendPlanning().PendingNextAction, "latest recorded next action");
    }

    [Test]
    public void Surfaces_a_recurring_blocker_as_a_heads_up()
    {
        RunSession(TimeSpan.FromMinutes(30), blockers: "waiting on API");
        RunSession(TimeSpan.FromMinutes(30), blockers: "Waiting on API");

        var rec = _sessions.RecommendPlanning();
        Check.That(rec.TopBlocker is not null, "a recurring blocker is surfaced");
        Check.Equal(2, rec.TopBlocker!.Count, "counted across both sessions");
    }

    [Test]
    public void A_specific_project_can_be_targeted_without_switching()
    {
        RunSession(TimeSpan.FromMinutes(30)); RunSession(TimeSpan.FromMinutes(30)); // Alpha
        _projects.CreateProject("Beta");
        // Active project stays Alpha; recommend for Beta explicitly.
        var rec = _sessions.RecommendPlanning("Beta");
        Check.Equal("Beta", rec.Scope, "targets the named project");
        Check.Equal(null, rec.SuggestedFocus, "Beta has no history yet");
        Check.Equal("Alpha", _projects.GetActiveProject()!.Name, "active project unchanged");
    }
}
