namespace ContextSwitcher.Work.Tests;

/// <summary>Domain-invariant tests for <see cref="ProjectRegistry"/> (in-memory store).</summary>
public sealed class ProjectRegistryTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 16, 12, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _registry;

    public ProjectRegistryTests()
    {
        _registry = new ProjectRegistry(_store, () => _now);
    }

    [Test]
    public void Create_assigns_required_data_fields()
    {
        var project = _registry.CreateProject("  Context Switcher  ", " my app ");
        Check.Equal("Context Switcher", project.Name, "trimmed name");
        Check.Equal("my app", project.Description, "trimmed description");
        Check.Equal(ProjectStatus.Active, project.Status, "initial status");
        Check.Equal(T0, project.CreatedUtc, "created timestamp");
        Check.Equal(T0, project.UpdatedUtc, "updated timestamp");
        Check.That(project.Id != Guid.Empty, "a non-empty id is assigned");
    }

    [Test]
    public void First_project_becomes_active_automatically()
    {
        var first = _registry.CreateProject("Alpha");
        _registry.CreateProject("Beta");
        Check.Equal(first.Id, _registry.GetActiveProject()!.Id, "first project is active");
    }

    [Test]
    public void Blank_name_is_rejected()
    {
        Check.Throws<ValidationException>(() => _registry.CreateProject("   "), "blank name");
        Check.Throws<ValidationException>(() => _registry.CreateProject(null), "null name");
    }

    [Test]
    public void Overlong_name_and_description_are_rejected()
    {
        Check.Throws<ValidationException>(
            () => _registry.CreateProject(new string('x', Project.MaxNameLength + 1)),
            "over-length name");
        Check.Throws<ValidationException>(
            () => _registry.CreateProject("ok", new string('x', Project.MaxDescriptionLength + 1)),
            "over-length description");
    }

    [Test]
    public void Duplicate_names_are_rejected_case_insensitively()
    {
        _registry.CreateProject("Alpha");
        Check.Throws<ValidationException>(() => _registry.CreateProject("alpha"), "duplicate name");
        Check.Throws<ValidationException>(() => _registry.CreateProject(" ALPHA "), "duplicate after trim");
    }

    [Test]
    public void Switch_changes_the_active_project_by_name_or_id()
    {
        _registry.CreateProject("Alpha");
        var beta = _registry.CreateProject("Beta");

        _registry.SwitchActiveProject("beta"); // case-insensitive name
        Check.Equal(beta.Id, _registry.GetActiveProject()!.Id, "switch by name");

        _registry.SwitchActiveProject(beta.Id.ToString()); // exact id
        Check.Equal(beta.Id, _registry.GetActiveProject()!.Id, "switch by id");
    }

    [Test]
    public void Switch_to_unknown_project_is_not_found()
    {
        _registry.CreateProject("Alpha");
        Check.Throws<NotFoundException>(() => _registry.SwitchActiveProject("Nope"), "unknown name");
        Check.Throws<NotFoundException>(
            () => _registry.SwitchActiveProject(Guid.NewGuid().ToString()), "unknown id");
        Check.Throws<ValidationException>(() => _registry.SwitchActiveProject("  "), "blank reference");
    }

    [Test]
    public void Archived_project_cannot_become_active()
    {
        _registry.CreateProject("Alpha");
        _registry.CreateProject("Beta");
        _registry.ArchiveProject("Beta");
        Check.Throws<ValidationException>(() => _registry.SwitchActiveProject("Beta"), "activate archived");
    }

    [Test]
    public void Active_project_cannot_be_archived()
    {
        _registry.CreateProject("Alpha");
        Check.Throws<ValidationException>(() => _registry.ArchiveProject("Alpha"), "archive active");
    }

    [Test]
    public void Archive_sets_status_and_updated_timestamp()
    {
        _registry.CreateProject("Alpha");
        _registry.CreateProject("Beta");
        _now = T0.AddHours(2);
        var archived = _registry.ArchiveProject("Beta");
        Check.Equal(ProjectStatus.Archived, archived.Status, "archived status");
        Check.Equal(T0.AddHours(2), archived.UpdatedUtc, "updated timestamp moved");
        Check.Equal(T0, archived.CreatedUtc, "created timestamp preserved");
        Check.Throws<ValidationException>(() => _registry.ArchiveProject("Beta"), "double archive");
    }

    [Test]
    public void List_orders_active_before_archived_then_by_name()
    {
        _registry.CreateProject("Charlie");
        _registry.CreateProject("alpha");
        _registry.CreateProject("Beta");
        _registry.ArchiveProject("Beta");

        var names = _registry.ListProjects().Select(p => p.Name).ToArray();
        Check.Equal("alpha", names[0], "active alphabetical first");
        Check.Equal("Charlie", names[1], "active alphabetical second");
        Check.Equal("Beta", names[2], "archived last");
    }

    [Test]
    public void No_active_project_reports_null_not_a_fake()
    {
        Check.Equal(null, _registry.GetActiveProject(), "empty workspace has no active project");
    }
}
