namespace ContextSwitcher.Work.Tests;

/// <summary>Tests for focus-trends insights (ADR-0015), clock-injected.</summary>
public sealed class FocusInsightsTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 17, 12, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;

    public FocusInsightsTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
    }

    /// <summary>Runs a closed session on the active project starting at a given time.</summary>
    private void Run(DateTimeOffset start, TimeSpan length, SessionOutcome outcome, TimeSpan? planned = null)
    {
        _now = start;
        _sessions.StartSession("work", planned);
        _now = start + length;
        _sessions.EndSession(outcome);
    }

    [Test]
    public void Empty_workspace_yields_zeroed_insights()
    {
        _projects.CreateProject("Alpha");
        var ins = _sessions.ComputeInsights();
        Check.Equal(0, ins.SessionCount, "no sessions");
        Check.Equal(TimeSpan.Zero, ins.TotalFocus, "no focus");
        Check.Equal(null, ins.AverageFocus, "no average");
        Check.Equal(null, ins.AverageOverrun, "no timed sessions");
        Check.Equal(0.0, ins.CompletionRate, "no completion rate");
    }

    [Test]
    public void Totals_average_and_completion_rate()
    {
        _projects.CreateProject("Alpha");
        Run(T0, TimeSpan.FromMinutes(30), SessionOutcome.Completed);
        Run(T0.AddHours(2), TimeSpan.FromMinutes(10), SessionOutcome.PartiallyCompleted);

        var ins = _sessions.ComputeInsights();
        Check.Equal(2, ins.SessionCount, "two closed sessions");
        Check.Equal(TimeSpan.FromMinutes(40), ins.TotalFocus, "total focus 40m");
        Check.Equal(TimeSpan.FromMinutes(20), ins.AverageFocus, "average 20m");
        Check.Equal(1, ins.OutcomeCounts[SessionOutcome.Completed], "one completed");
        Check.Equal(1, ins.OutcomeCounts[SessionOutcome.PartiallyCompleted], "one partial");
        Check.Equal(0.5, ins.CompletionRate, "50% completed");
    }

    [Test]
    public void Estimation_accuracy_averages_signed_overrun()
    {
        _projects.CreateProject("Alpha");
        Run(T0, TimeSpan.FromMinutes(30), SessionOutcome.Completed, planned: TimeSpan.FromMinutes(20)); // +10
        Run(T0.AddHours(3), TimeSpan.FromMinutes(15), SessionOutcome.Completed, planned: TimeSpan.FromMinutes(25)); // -10
        Run(T0.AddHours(6), TimeSpan.FromMinutes(5), SessionOutcome.Completed); // untimed, ignored

        var ins = _sessions.ComputeInsights();
        Check.Equal(2, ins.TimedCount, "two timed sessions");
        Check.Equal(1, ins.OverranCount, "one ran over");
        Check.Equal(TimeSpan.Zero, ins.AverageOverrun, "average overrun nets to zero (+10, -10)");
    }

    [Test]
    public void Week_over_week_trend_uses_the_clock()
    {
        _projects.CreateProject("Alpha");
        // "prior" week: ~10 days ago; "recent" week: ~2 days ago; anchor now = T0.
        Run(T0.AddDays(-10), TimeSpan.FromMinutes(20), SessionOutcome.Completed);
        Run(T0.AddDays(-2), TimeSpan.FromMinutes(50), SessionOutcome.Completed);
        _now = T0; // evaluate insights "now"

        var ins = _sessions.ComputeInsights();
        Check.Equal(TimeSpan.FromMinutes(50), ins.RecentFocus, "last 7 days focus");
        Check.Equal(TimeSpan.FromMinutes(20), ins.PriorFocus, "prior 7 days focus");
        Check.That(ins.TrendDirection > 0, "focus trending up week over week");
    }

    [Test]
    public void Scope_can_be_a_single_project_or_all_projects()
    {
        _projects.CreateProject("Alpha");
        _projects.CreateProject("Beta");
        _projects.SwitchActiveProject("Alpha");
        Run(T0, TimeSpan.FromMinutes(30), SessionOutcome.Completed);
        _projects.SwitchActiveProject("Beta");
        Run(T0.AddHours(1), TimeSpan.FromMinutes(10), SessionOutcome.Completed);
        _now = T0.AddHours(2);

        var all = _sessions.ComputeInsights();
        Check.Equal(2, all.SessionCount, "all projects sees both");
        Check.Equal("all projects", all.Scope, "workspace scope label");

        var alpha = _sessions.ComputeInsights("Alpha");
        Check.Equal(1, alpha.SessionCount, "Alpha scope sees only Alpha");
        Check.Equal(TimeSpan.FromMinutes(30), alpha.TotalFocus, "Alpha total");
        Check.Equal("Alpha", alpha.Scope, "project scope label");
    }

    [Test]
    public void Unknown_scope_is_rejected()
    {
        _projects.CreateProject("Alpha");
        Check.Throws<NotFoundException>(() => _sessions.ComputeInsights("Ghost"), "unknown project");
    }
}
