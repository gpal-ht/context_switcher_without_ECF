namespace ContextSwitcher.Work.Tests;

/// <summary>Tests for per-session estimation accuracy and the trend summary (ADR-0017).</summary>
public sealed class EstimationTrendTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 17, 09, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;

    public EstimationTrendTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
        _projects.CreateProject("Alpha");
    }

    /// <summary>Runs a closed session starting at <paramref name="start"/> with a plan and actual length.</summary>
    private void Run(DateTimeOffset start, TimeSpan planned, TimeSpan actual)
    {
        _now = start;
        _sessions.StartSession("work", planned);
        _now = start + actual;
        _sessions.EndSession(SessionOutcome.Completed);
    }

    [Test]
    public void Per_session_accuracy_is_one_for_a_perfect_estimate()
    {
        Run(T0, TimeSpan.FromMinutes(25), TimeSpan.FromMinutes(25));
        var s = _sessions.ListSessionsForActiveProject()[0];
        Check.Equal(1.0, s.EstimationAccuracy, "perfect estimate scores 1.0");
    }

    [Test]
    public void Per_session_accuracy_drops_with_error_and_floors_at_zero()
    {
        Run(T0, TimeSpan.FromMinutes(20), TimeSpan.FromMinutes(25)); // 25% over -> 0.75
        var over = _sessions.ListSessionsForActiveProject()[0];
        Check.Equal(0.75, over.EstimationAccuracy, "25% over scores 0.75");

        Run(T0.AddHours(2), TimeSpan.FromMinutes(10), TimeSpan.FromMinutes(40)); // 300% over -> floored 0
        var wayOver = _sessions.ListSessionsForActiveProject()[0];
        Check.Equal(0.0, wayOver.EstimationAccuracy, "off by >100% floors at 0");
    }

    [Test]
    public void Untimed_or_open_sessions_have_no_accuracy()
    {
        var open = _sessions.StartSession("untimed");
        Check.Equal(null, open.EstimationAccuracy, "open + untimed");
        _now = T0.AddMinutes(10);
        var ended = _sessions.EndSession(SessionOutcome.Completed);
        Check.Equal(null, ended.EstimationAccuracy, "closed but untimed");
    }

    [Test]
    public void No_timed_sessions_reports_zeroed_trend()
    {
        var t = _sessions.ComputeEstimationTrend();
        Check.Equal(0, t.TimedCount, "no timed sessions");
        Check.Equal(0.0, t.AverageAccuracyPercent, "no accuracy");
        Check.Equal(EstimationBias.WellCalibrated, t.Bias, "no bias to report");
        Check.Equal(null, t.Improving, "no trend");
    }

    [Test]
    public void Average_accuracy_and_under_estimate_bias()
    {
        // Both run over their plan -> under-estimating.
        Run(T0, TimeSpan.FromMinutes(20), TimeSpan.FromMinutes(25)); // 0.75
        Run(T0.AddHours(2), TimeSpan.FromMinutes(20), TimeSpan.FromMinutes(30)); // 0.5
        var t = _sessions.ComputeEstimationTrend();
        Check.Equal(2, t.TimedCount, "two timed sessions");
        Check.Equal(62.5, Math.Round(t.AverageAccuracyPercent, 1), "average of 75% and 50%");
        Check.Equal(EstimationBias.UnderEstimates, t.Bias, "consistently over plan = under-estimating");
    }

    [Test]
    public void Over_estimate_and_well_calibrated_bias()
    {
        Run(T0, TimeSpan.FromMinutes(40), TimeSpan.FromMinutes(20)); // finishes early
        Run(T0.AddHours(2), TimeSpan.FromMinutes(40), TimeSpan.FromMinutes(25));
        Check.Equal(EstimationBias.OverEstimates, _sessions.ComputeEstimationTrend().Bias, "finishes early = over-estimating");

        // Fresh workspace for a well-calibrated case.
        var store = new InMemoryWorkspaceStore();
        var p = new ProjectRegistry(store, () => _now);
        p.CreateProject("Cal");
        var svc = new WorkSessionService(store, () => _now);
        _now = T0; svc.StartSession("w", TimeSpan.FromMinutes(30)); _now = T0.AddMinutes(31); svc.EndSession(SessionOutcome.Completed);
        _now = T0.AddHours(2); svc.StartSession("w", TimeSpan.FromMinutes(30)); _now = T0.AddHours(2).AddMinutes(29); svc.EndSession(SessionOutcome.Completed);
        Check.Equal(EstimationBias.WellCalibrated, svc.ComputeEstimationTrend().Bias, "within 10% is well-calibrated");
    }

    [Test]
    public void Trend_compares_recent_half_to_earlier_half()
    {
        // Earlier sessions inaccurate, recent ones perfect -> improving.
        Run(T0, TimeSpan.FromMinutes(20), TimeSpan.FromMinutes(30));            // 0.5
        Run(T0.AddDays(1), TimeSpan.FromMinutes(20), TimeSpan.FromMinutes(30)); // 0.5
        Run(T0.AddDays(2), TimeSpan.FromMinutes(20), TimeSpan.FromMinutes(20)); // 1.0
        Run(T0.AddDays(3), TimeSpan.FromMinutes(20), TimeSpan.FromMinutes(20)); // 1.0

        var t = _sessions.ComputeEstimationTrend();
        Check.Equal(true, t.Improving, "recent half more accurate");
        Check.That(t.RecentAccuracyPercent > t.EarlierAccuracyPercent, "recent beats earlier");
        Check.Equal(50.0, Math.Round(t.EarlierAccuracyPercent!.Value, 1), "earlier half avg 50%");
        Check.Equal(100.0, Math.Round(t.RecentAccuracyPercent!.Value, 1), "recent half avg 100%");
    }

    [Test]
    public void Scope_and_unknown_project()
    {
        Run(T0, TimeSpan.FromMinutes(20), TimeSpan.FromMinutes(20));
        _projects.CreateProject("Beta");
        _projects.SwitchActiveProject("Beta");
        Run(T0.AddHours(1), TimeSpan.FromMinutes(20), TimeSpan.FromMinutes(40));

        Check.Equal(2, _sessions.ComputeEstimationTrend().TimedCount, "all projects");
        Check.Equal(1, _sessions.ComputeEstimationTrend("Alpha").TimedCount, "Alpha scope");
        Check.Throws<NotFoundException>(() => _sessions.ComputeEstimationTrend("Ghost"), "unknown project");
    }
}
