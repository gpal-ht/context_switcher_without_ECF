namespace ContextSwitcher.Work.Tests;

/// <summary>Tests for browsing any project's history without switching (ADR-0014).</summary>
public sealed class CrossProjectHistoryTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 17, 09, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;

    public CrossProjectHistoryTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
    }

    private void RunSessionFor(string project, string objective)
    {
        _projects.SwitchActiveProject(project);
        _sessions.StartSession(objective);
        _now = _now.AddMinutes(10);
        _sessions.EndSession(SessionOutcome.Completed);
    }

    [Test]
    public void Lists_another_projects_history_without_switching_active()
    {
        var alpha = _projects.CreateProject("Alpha"); // active
        _projects.CreateProject("Beta");
        RunSessionFor("Alpha", "alpha work");
        RunSessionFor("Beta", "beta work");
        // Leave Alpha active.
        _projects.SwitchActiveProject("Alpha");

        var betaHistory = _sessions.ListSessions("Beta");
        Check.Equal(1, betaHistory.Count, "Beta history is visible");
        Check.Equal("beta work", betaHistory[0].Objective, "correct project's sessions");
        Check.Equal("Alpha", _projects.GetActiveProject()!.Name, "active project unchanged by browsing");
        Check.Equal(alpha.Id, _projects.GetActiveProject()!.Id, "active project id unchanged");
    }

    [Test]
    public void Lists_by_id_and_orders_newest_first()
    {
        _projects.CreateProject("Alpha");
        var beta = _projects.CreateProject("Beta");
        RunSessionFor("Beta", "first");
        RunSessionFor("Beta", "second");
        _projects.SwitchActiveProject("Alpha");

        var byId = _sessions.ListSessions(beta.Id.ToString());
        Check.Equal(2, byId.Count, "both Beta sessions");
        Check.Equal("second", byId[0].Objective, "newest first");
    }

    [Test]
    public void A_project_with_no_sessions_lists_empty()
    {
        _projects.CreateProject("Alpha");
        _projects.CreateProject("Beta");
        Check.Equal(0, _sessions.ListSessions("Beta").Count, "empty history for a fresh project");
    }

    [Test]
    public void Unknown_or_blank_project_is_rejected()
    {
        _projects.CreateProject("Alpha");
        Check.Throws<NotFoundException>(() => _sessions.ListSessions("Nope"), "unknown name");
        Check.Throws<NotFoundException>(
            () => _sessions.ListSessions(Guid.NewGuid().ToString()), "unknown id");
        Check.Throws<ValidationException>(() => _sessions.ListSessions("   "), "blank reference");
    }

    [Test]
    public void Registry_resolution_still_works_after_the_refactor()
    {
        // ProjectLookup now backs both services (ADR-0014); confirm ProjectRegistry
        // behaviour is unchanged for name, id, and the not-found messages.
        var alpha = _projects.CreateProject("Alpha");
        _projects.CreateProject("Beta");
        Check.Equal(alpha.Id, _projects.SwitchActiveProject("alpha").Id, "resolve by case-insensitive name");
        Check.Equal(alpha.Id, _projects.SwitchActiveProject(alpha.Id.ToString()).Id, "resolve by id");
        Check.Throws<NotFoundException>(() => _projects.SwitchActiveProject("ghost"), "unknown still not found");
    }
}
