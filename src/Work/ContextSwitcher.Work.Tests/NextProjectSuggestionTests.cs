namespace ContextSwitcher.Work.Tests;

/// <summary>Tests for the "what to work on next" ranking (ADR-0019).</summary>
public sealed class NextProjectSuggestionTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 17, 09, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;

    public NextProjectSuggestionTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
    }

    private void RunSessionFor(string project, DateTimeOffset start, string? nextAction = null)
    {
        _projects.SwitchActiveProject(project);
        _now = start;
        _sessions.StartSession("work");
        _now = start.AddMinutes(20);
        _sessions.EndSession(SessionOutcome.Completed, nextAction: nextAction);
    }

    [Test]
    public void No_active_projects_yields_an_empty_suggestion_list()
    {
        Check.Equal(0, _sessions.SuggestNextProject().Count, "nothing to suggest");
    }

    [Test]
    public void A_project_with_a_pending_next_action_ranks_first()
    {
        _projects.CreateProject("Alpha");
        _projects.CreateProject("Beta");
        // Beta worked more recently but has no next action; Alpha has a next action.
        RunSessionFor("Alpha", T0, nextAction: "write the adapter");
        RunSessionFor("Beta", T0.AddDays(1));
        _projects.SwitchActiveProject("Alpha");

        var ranked = _sessions.SuggestNextProject();
        Check.Equal("Alpha", ranked[0].Project, "clear next step wins over mere recency");
        Check.Equal("write the adapter", ranked[0].PendingNextAction, "surfaces the next action");
    }

    [Test]
    public void Among_equals_the_more_recently_worked_ranks_first()
    {
        _projects.CreateProject("Alpha");
        _projects.CreateProject("Beta");
        RunSessionFor("Alpha", T0, nextAction: "do A");
        RunSessionFor("Beta", T0.AddDays(1), nextAction: "do B"); // both have a next action; Beta newer

        var ranked = _sessions.SuggestNextProject();
        Check.Equal("Beta", ranked[0].Project, "more recent among equals ranks first");
        Check.Equal("Alpha", ranked[1].Project, "then the older one");
    }

    [Test]
    public void Never_worked_projects_sort_last_and_report_not_started()
    {
        _projects.CreateProject("Worked");
        _projects.CreateProject("Fresh");
        RunSessionFor("Worked", T0);
        _projects.SwitchActiveProject("Worked");

        var ranked = _sessions.SuggestNextProject();
        Check.Equal("Worked", ranked[0].Project, "worked project first");
        Check.Equal("Fresh", ranked[1].Project, "never-worked last");
        Check.Equal(null, ranked[1].LastWorkedUtc, "no last-worked time");
        Check.Equal("Not started yet.", ranked[1].Reason, "honest reason");
    }

    [Test]
    public void Archived_projects_are_excluded()
    {
        _projects.CreateProject("Alpha");
        _projects.CreateProject("Old");
        RunSessionFor("Old", T0, nextAction: "resume old");
        _projects.SwitchActiveProject("Alpha");
        _projects.ArchiveProject("Old");

        var ranked = _sessions.SuggestNextProject();
        Check.Equal(1, ranked.Count, "archived project is not suggested");
        Check.Equal("Alpha", ranked[0].Project, "only the active project remains");
    }

    [Test]
    public void The_active_project_is_flagged()
    {
        _projects.CreateProject("Alpha");
        _projects.CreateProject("Beta");
        _projects.SwitchActiveProject("Beta");

        var ranked = _sessions.SuggestNextProject();
        Check.Equal(true, ranked.First(s => s.Project == "Beta").IsActive, "active flagged");
        Check.Equal(false, ranked.First(s => s.Project == "Alpha").IsActive, "others not");
    }
}
