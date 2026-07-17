namespace ContextSwitcher.Work;

/// <summary>
/// Application service for the project registry and active-project selection
/// (docs/features/project_context_switch.md, MVP requirements 1-2).
///
/// Invariants (ADR-0008):
///   * project names are unique case-insensitively across the workspace;
///   * at most one project is active at a time;
///   * an archived project cannot become the active project;
///   * the active project cannot be archived while it is active.
///
/// Persistence goes exclusively through <see cref="IWorkspaceStore"/>; every
/// mutating operation loads, mutates, and saves atomically. UI/CLI layers
/// call this service and never touch the store directly.
/// </summary>
public sealed class ProjectRegistry
{
    private readonly IWorkspaceStore _store;
    private readonly Func<DateTimeOffset> _clock;

    public ProjectRegistry(IWorkspaceStore store, Func<DateTimeOffset>? clock = null)
    {
        _store = store;
        _clock = clock ?? (() => DateTimeOffset.UtcNow);
    }

    /// <summary>Creates a project. The first project ever created becomes active.</summary>
    /// <exception cref="ValidationException">Blank/over-length/duplicate name.</exception>
    public Project CreateProject(string? name, string? description = null)
    {
        var normalizedName = Project.NormalizeName(name);
        var normalizedDescription = Project.NormalizeDescription(description);

        var state = _store.Load();
        if (FindByName(state, normalizedName) is not null)
        {
            throw new ValidationException(
                $"A project named '{normalizedName}' already exists (names are case-insensitive).");
        }

        var now = _clock();
        var project = new Project
        {
            Id = Guid.NewGuid(),
            Name = normalizedName,
            Description = normalizedDescription,
            Status = ProjectStatus.Active,
            CreatedUtc = now,
            UpdatedUtc = now,
        };
        state.Projects.Add(project);
        state.ActiveProjectId ??= project.Id; // first project becomes active
        _store.Save(state);
        return project;
    }

    /// <summary>All projects, active-status first, then by name.</summary>
    public IReadOnlyList<Project> ListProjects()
    {
        var state = _store.Load();
        return state.Projects
            .OrderBy(p => p.Status)
            .ThenBy(p => p.Name, StringComparer.OrdinalIgnoreCase)
            .ToList();
    }

    /// <summary>The active project, or null when none is selected.</summary>
    public Project? GetActiveProject()
    {
        var state = _store.Load();
        return state.ActiveProjectId is Guid id
            ? state.Projects.FirstOrDefault(p => p.Id == id)
            : null;
    }

    /// <summary>Makes the referenced project the active project.</summary>
    /// <exception cref="NotFoundException">No project matches.</exception>
    /// <exception cref="ValidationException">The project is archived.</exception>
    public Project SwitchActiveProject(string nameOrId)
    {
        var state = _store.Load();
        var project = Resolve(state, nameOrId);
        if (project.Status == ProjectStatus.Archived)
        {
            throw new ValidationException(
                $"'{project.Name}' is archived and cannot be made active.");
        }
        state.ActiveProjectId = project.Id;
        _store.Save(state);
        return project;
    }

    /// <summary>Archives the referenced project.</summary>
    /// <exception cref="NotFoundException">No project matches.</exception>
    /// <exception cref="ValidationException">The project is active or already archived.</exception>
    public Project ArchiveProject(string nameOrId)
    {
        var state = _store.Load();
        var project = Resolve(state, nameOrId);
        if (project.Status == ProjectStatus.Archived)
        {
            throw new ValidationException($"'{project.Name}' is already archived.");
        }
        if (state.ActiveProjectId == project.Id)
        {
            throw new ValidationException(
                $"'{project.Name}' is the active project. Switch to another project before archiving it.");
        }

        var archived = project with { Status = ProjectStatus.Archived, UpdatedUtc = _clock() };
        state.Projects[state.Projects.FindIndex(p => p.Id == project.Id)] = archived;
        _store.Save(state);
        return archived;
    }

    private static Project? FindByName(WorkspaceState state, string name) =>
        state.Projects.FirstOrDefault(
            p => string.Equals(p.Name, name, StringComparison.OrdinalIgnoreCase));

    /// <summary>Resolves a project by exact id or case-insensitive name.</summary>
    private static Project Resolve(WorkspaceState state, string nameOrId)
    {
        var query = (nameOrId ?? "").Trim();
        if (query.Length == 0)
        {
            throw new ValidationException("A project name or id is required.");
        }
        if (Guid.TryParse(query, out var id))
        {
            return state.Projects.FirstOrDefault(p => p.Id == id)
                ?? throw new NotFoundException($"No project has the id '{query}'.");
        }
        return FindByName(state, query)
            ?? throw new NotFoundException($"No project is named '{query}'.");
    }
}
