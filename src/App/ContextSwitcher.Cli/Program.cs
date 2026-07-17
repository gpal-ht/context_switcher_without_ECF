using ContextSwitcher.Work;

namespace ContextSwitcher.Cli;

/// <summary>
/// Interim CLI harness over the Work Engine (ADR-0008).
///
/// Commands:
///   project add &lt;name&gt; [--description &lt;text&gt;]
///   project list
///   project switch &lt;name|id&gt;
///   project archive &lt;name|id&gt;
///   status
///
/// Exit codes: 0 ok; 1 unexpected error; 2 usage/validation error;
/// 3 not found; 4 workspace store corrupt.
/// Output is plain text (no color-only communication); errors go to stderr.
/// </summary>
public static class Program
{
    public static int Main(string[] args)
    {
        try
        {
            var registry = new ProjectRegistry(new JsonFileWorkspaceStore());
            return Run(registry, args);
        }
        catch (ValidationException ex)
        {
            Console.Error.WriteLine($"error: {ex.Message}");
            return 2;
        }
        catch (NotFoundException ex)
        {
            Console.Error.WriteLine($"error: {ex.Message}");
            return 3;
        }
        catch (StoreCorruptException ex)
        {
            Console.Error.WriteLine($"error: {ex.Message}");
            return 4;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"unexpected error: {ex.Message}");
            return 1;
        }
    }

    private static int Run(ProjectRegistry registry, string[] args)
    {
        switch (args)
        {
            case ["project", "add", var name, .. var rest]:
                return AddProject(registry, name, rest);
            case ["project", "list"]:
                return ListProjects(registry);
            case ["project", "switch", var reference]:
                var switched = registry.SwitchActiveProject(reference);
                Console.WriteLine($"Active project is now '{switched.Name}'.");
                return 0;
            case ["project", "archive", var reference]:
                var archived = registry.ArchiveProject(reference);
                Console.WriteLine($"Archived '{archived.Name}'.");
                return 0;
            case ["status"]:
                return Status(registry);
            case ["--help"] or ["-h"] or ["help"] or []:
                PrintUsage(Console.Out);
                return args.Length == 0 ? 2 : 0;
            default:
                Console.Error.WriteLine("error: unknown command.");
                PrintUsage(Console.Error);
                return 2;
        }
    }

    private static int AddProject(ProjectRegistry registry, string name, string[] rest)
    {
        string? description = null;
        if (rest is ["--description", var text])
        {
            description = text;
        }
        else if (rest.Length > 0)
        {
            Console.Error.WriteLine("error: unrecognized arguments after the project name. " +
                                    "Use: project add <name> [--description <text>]");
            return 2;
        }
        var project = registry.CreateProject(name, description);
        var activeNote = registry.GetActiveProject()?.Id == project.Id
            ? " It is now the active project."
            : "";
        Console.WriteLine($"Created project '{project.Name}' ({project.Id}).{activeNote}");
        return 0;
    }

    private static int ListProjects(ProjectRegistry registry)
    {
        var projects = registry.ListProjects();
        if (projects.Count == 0)
        {
            Console.WriteLine("No projects yet. Create one with: project add <name>");
            return 0;
        }
        var activeId = registry.GetActiveProject()?.Id;
        foreach (var project in projects)
        {
            var marker = project.Id == activeId ? "* " : "  ";
            var status = project.Status == ProjectStatus.Archived ? " [archived]" : "";
            var description = project.Description.Length > 0 ? $" — {project.Description}" : "";
            Console.WriteLine($"{marker}{project.Name}{status}{description}");
        }
        Console.WriteLine();
        Console.WriteLine("* marks the active project.");
        return 0;
    }

    private static int Status(ProjectRegistry registry)
    {
        var active = registry.GetActiveProject();
        Console.WriteLine(active is null
            ? "No active project. Select one with: project switch <name>"
            : $"Active project: {active.Name}" +
              (active.Description.Length > 0 ? $" — {active.Description}" : ""));
        return 0;
    }

    private static void PrintUsage(TextWriter writer)
    {
        writer.WriteLine("Context Switcher — project registry (interim CLI harness)");
        writer.WriteLine();
        writer.WriteLine("usage:");
        writer.WriteLine("  context-switcher project add <name> [--description <text>]");
        writer.WriteLine("  context-switcher project list");
        writer.WriteLine("  context-switcher project switch <name|id>");
        writer.WriteLine("  context-switcher project archive <name|id>");
        writer.WriteLine("  context-switcher status");
        writer.WriteLine();
        writer.WriteLine($"Data is stored in %LOCALAPPDATA%\\ContextSwitcher\\workspace.json");
        writer.WriteLine($"(override the directory with {JsonFileWorkspaceStore.DataHomeEnvVar}).");
    }
}
