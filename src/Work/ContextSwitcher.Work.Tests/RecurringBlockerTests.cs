namespace ContextSwitcher.Work.Tests;

/// <summary>Tests for recurring-blocker detection (ADR-0016).</summary>
public sealed class RecurringBlockerTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 17, 09, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;

    public RecurringBlockerTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
        _projects.CreateProject("Alpha");
    }

    /// <summary>Runs a closed session that records the given blocker text.</summary>
    private void RunWithBlocker(string? blockers, int minutesLater = 30)
    {
        _sessions.StartSession("work");
        _now = _now.AddMinutes(minutesLater);
        _sessions.EndSession(SessionOutcome.Blocked, blockers: blockers);
    }

    [Test]
    public void Detects_a_blocker_seen_in_two_or_more_sessions()
    {
        RunWithBlocker("Waiting on API");
        RunWithBlocker("Waiting on API");
        RunWithBlocker("flaky test");   // one-off, below the default threshold

        var recurring = _sessions.DetectRecurringBlockers();
        Check.Equal(1, recurring.Count, "one recurring blocker");
        Check.Equal("Waiting on API", recurring[0].Text, "the repeated blocker");
        Check.Equal(2, recurring[0].Count, "seen twice");
    }

    [Test]
    public void Grouping_ignores_case_and_extra_whitespace()
    {
        RunWithBlocker("Waiting on API");
        RunWithBlocker("  waiting   on  api ");

        var recurring = _sessions.DetectRecurringBlockers();
        Check.Equal(1, recurring.Count, "normalized to one group");
        Check.Equal(2, recurring[0].Count, "both counted together");
        Check.Equal("waiting   on  api", recurring[0].Text.Trim(), "shows the most recent original wording");
    }

    [Test]
    public void Empty_or_blank_blockers_are_ignored()
    {
        RunWithBlocker(null);
        RunWithBlocker("   ");
        RunWithBlocker("");
        Check.Equal(0, _sessions.DetectRecurringBlockers().Count, "no blockers recorded");
    }

    [Test]
    public void Orders_by_count_then_most_recent()
    {
        RunWithBlocker("rare thing");            // 09:00 -> ends 09:30
        RunWithBlocker("common blocker");
        RunWithBlocker("common blocker");
        RunWithBlocker("rare thing");            // now 2 each; "rare thing" seen more recently
        RunWithBlocker("common blocker");        // common now 3

        var recurring = _sessions.DetectRecurringBlockers();
        Check.Equal(2, recurring.Count, "two recurring blockers");
        Check.Equal("common blocker", recurring[0].Text, "most frequent first");
        Check.Equal(3, recurring[0].Count, "common seen 3x");
        Check.Equal("rare thing", recurring[1].Text, "then the less frequent");
    }

    [Test]
    public void Last_seen_is_the_most_recent_occurrence()
    {
        RunWithBlocker("waiting on api");         // ends T0+30m
        var firstEnd = _now;
        _now = _now.AddHours(3);
        RunWithBlocker("waiting on api");         // ends later
        var recurring = _sessions.DetectRecurringBlockers();
        Check.That(recurring[0].LastSeenUtc > firstEnd, "last-seen reflects the later session");
    }

    [Test]
    public void Min_occurrences_threshold_is_respected()
    {
        RunWithBlocker("twice"); RunWithBlocker("twice");
        RunWithBlocker("thrice"); RunWithBlocker("thrice"); RunWithBlocker("thrice");

        var atLeastThree = _sessions.DetectRecurringBlockers(minOccurrences: 3);
        Check.Equal(1, atLeastThree.Count, "only the 3x blocker qualifies");
        Check.Equal("thrice", atLeastThree[0].Text, "the thrice blocker");
    }

    [Test]
    public void Scope_can_be_a_single_project_or_all_projects()
    {
        RunWithBlocker("alpha blocker"); RunWithBlocker("alpha blocker");
        _projects.CreateProject("Beta");
        _projects.SwitchActiveProject("Beta");
        RunWithBlocker("beta blocker"); RunWithBlocker("beta blocker");

        Check.Equal(2, _sessions.DetectRecurringBlockers().Count, "all projects sees both");
        var alpha = _sessions.DetectRecurringBlockers("Alpha");
        Check.Equal(1, alpha.Count, "Alpha scope sees only its blocker");
        Check.Equal("alpha blocker", alpha[0].Text, "correct project's blocker");
    }

    [Test]
    public void Unknown_scope_is_rejected()
    {
        Check.Throws<NotFoundException>(() => _sessions.DetectRecurringBlockers("Ghost"), "unknown project");
    }
}
