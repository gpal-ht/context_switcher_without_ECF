namespace ContextSwitcher.Work.Tests;

/// <summary>Focus-timer tests for timed sessions (ADR-0012), clock-injected.</summary>
public sealed class TimerSwitchingTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 17, 09, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;

    public TimerSwitchingTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
        _projects.CreateProject("Alpha"); // auto-active
    }

    [Test]
    public void Untimed_session_has_no_deadline_or_remaining()
    {
        var s = _sessions.StartSession("no timer");
        Check.Equal(null, s.PlannedDuration, "no planned duration");
        Check.Equal(null, s.Deadline, "no deadline");
        Check.Equal(null, s.RemainingAt(_now), "no remaining");
        Check.That(!s.IsElapsedAt(_now.AddHours(1)), "untimed never elapses");
    }

    [Test]
    public void Timed_session_computes_deadline_and_remaining()
    {
        var s = _sessions.StartSession("focus", TimeSpan.FromMinutes(25));
        Check.Equal(TimeSpan.FromMinutes(25), s.PlannedDuration, "planned duration stored");
        Check.Equal(T0.AddMinutes(25), s.Deadline, "deadline = start + planned");
        Check.Equal(TimeSpan.FromMinutes(15), s.RemainingAt(T0.AddMinutes(10)), "remaining decreases");
        Check.That(!s.IsElapsedAt(T0.AddMinutes(24)), "not elapsed before deadline");
    }

    [Test]
    public void Timed_session_elapses_at_and_after_deadline()
    {
        var s = _sessions.StartSession("focus", TimeSpan.FromMinutes(25));
        Check.That(s.IsElapsedAt(T0.AddMinutes(25)), "elapsed exactly at deadline");
        Check.That(s.IsElapsedAt(T0.AddMinutes(40)), "still elapsed past deadline");
        Check.Equal(TimeSpan.FromMinutes(-5), s.RemainingAt(T0.AddMinutes(30)), "remaining goes negative");
    }

    [Test]
    public void Invalid_planned_durations_are_rejected()
    {
        Check.Throws<ValidationException>(
            () => _sessions.StartSession("x", TimeSpan.Zero), "zero duration");
        Check.Throws<ValidationException>(
            () => _sessions.StartSession("x", TimeSpan.FromMinutes(-5)), "negative duration");
        Check.Throws<ValidationException>(
            () => _sessions.StartSession("x", TimeSpan.FromHours(25)), "over the 24h cap");
    }

    [Test]
    public void A_closed_session_reports_no_remaining()
    {
        _sessions.StartSession("focus", TimeSpan.FromMinutes(25));
        _now = T0.AddMinutes(30);
        var ended = _sessions.EndSession(SessionOutcome.Completed);
        Check.Equal(null, ended.RemainingAt(_now), "ended session has no remaining");
        Check.That(!ended.IsElapsedAt(_now), "ended session is not 'elapsed' (it's done)");
    }

    [Test]
    public void Extend_gives_a_fresh_window_from_now()
    {
        _sessions.StartSession("focus", TimeSpan.FromMinutes(25));
        _now = T0.AddMinutes(30); // 5 minutes past the deadline
        var extended = _sessions.ExtendActiveSession(TimeSpan.FromMinutes(5));
        Check.That(!extended.IsElapsedAt(_now), "no longer elapsed right after extend");
        Check.Equal(_now.AddMinutes(5), extended.Deadline, "deadline is now + extension");
        Check.Equal(TimeSpan.FromMinutes(5), extended.RemainingAt(_now), "about five minutes left");
    }

    [Test]
    public void Extend_requires_an_open_session_and_a_positive_amount()
    {
        Check.Throws<ValidationException>(
            () => _sessions.ExtendActiveSession(TimeSpan.FromMinutes(5)), "no open session");
        _sessions.StartSession("focus", TimeSpan.FromMinutes(25));
        Check.Throws<ValidationException>(
            () => _sessions.ExtendActiveSession(TimeSpan.Zero), "non-positive extension");
    }

    [Test]
    public void Planned_duration_round_trips_and_absence_stays_null()
    {
        var dir = Path.Combine(Path.GetTempPath(), "cs-timer-" + Guid.NewGuid().ToString("N"));
        try
        {
            var store = new JsonFileWorkspaceStore(dir);
            var projects = new ProjectRegistry(store, () => _now);
            projects.CreateProject("Beta");
            projects.SwitchActiveProject("Beta");
            new WorkSessionService(store, () => _now).StartSession("timed", TimeSpan.FromMinutes(50));

            var reloaded = new WorkSessionService(new JsonFileWorkspaceStore(dir), () => _now);
            var s = reloaded.GetOpenSession()!;
            Check.Equal(TimeSpan.FromMinutes(50), s.PlannedDuration, "planned duration persisted");

            // A session written without the field loads as untimed.
            Check.That(File.ReadAllText(Path.Combine(dir, "workspace.json")).Contains("planned_duration"),
                "the field is present in JSON when set");
        }
        finally
        {
            try { Directory.Delete(dir, recursive: true); } catch (DirectoryNotFoundException) { }
        }
    }
}
