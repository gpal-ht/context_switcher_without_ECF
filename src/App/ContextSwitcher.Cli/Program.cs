using ContextSwitcher.Work;

namespace ContextSwitcher.Cli;

/// <summary>
/// Interim CLI harness over the Work Engine (ADR-0008, ADR-0009).
///
/// Commands:
///   project add &lt;name&gt; [--description &lt;text&gt;]
///   project list
///   project switch &lt;name|id&gt;
///   project archive &lt;name|id&gt;
///   session start [--objective &lt;text&gt;]
///   session end --outcome &lt;outcome&gt; [--completed &lt;t&gt;] [--unfinished &lt;t&gt;]
///               [--blockers &lt;t&gt;] [--notes &lt;t&gt;] [--next &lt;t&gt;]
///   session list
///   resume
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
            var store = new JsonFileWorkspaceStore();
            var registry = new ProjectRegistry(store);
            var sessions = new WorkSessionService(store);
            return Run(registry, sessions, args);
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

    private static int Run(ProjectRegistry registry, WorkSessionService sessions, string[] args)
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
            case ["session", "start", .. var rest]:
                return StartSession(registry, sessions, rest);
            case ["session", "end", .. var rest]:
                return EndSession(sessions, rest);
            case ["session", "extend", .. var rest]:
                return ExtendSession(sessions, rest);
            case ["session", "list"]:
                return ListSessions(registry, sessions);
            case ["resume"]:
                return Resume(registry, sessions);
            case ["status"]:
                return Status(registry, sessions);
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
        if (!TryParseOptions(rest, new[] { "--description" }, out var opts, out var error))
        {
            Console.Error.WriteLine($"error: {error} Use: project add <name> [--description <text>]");
            return 2;
        }
        var project = registry.CreateProject(name, opts.GetValueOrDefault("--description"));
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

    private static int StartSession(ProjectRegistry registry, WorkSessionService sessions, string[] rest)
    {
        if (!TryParseOptions(rest, new[] { "--objective", "--minutes" }, out var opts, out var error))
        {
            Console.Error.WriteLine($"error: {error} Use: session start [--objective <text>] [--minutes <n>]");
            return 2;
        }
        TimeSpan? planned = null;
        if (opts.TryGetValue("--minutes", out var minutesText))
        {
            if (!double.TryParse(minutesText, out var minutes) || minutes <= 0)
            {
                Console.Error.WriteLine("error: --minutes must be a positive number.");
                return 2;
            }
            planned = TimeSpan.FromMinutes(minutes);
        }
        var session = sessions.StartSession(opts.GetValueOrDefault("--objective"), planned);
        var project = registry.GetActiveProject();
        var onProject = project is null ? "" : $" on '{project.Name}'";
        var objective = session.Objective.Length > 0 ? $" — {session.Objective}" : "";
        var timer = session.PlannedDuration is TimeSpan d ? $" (focus timer: {FormatDuration(d)})" : "";
        Console.WriteLine($"Started a work session{onProject}{objective}{timer}.");
        return 0;
    }

    private static int EndSession(WorkSessionService sessions, string[] rest)
    {
        var known = new[] { "--outcome", "--completed", "--unfinished", "--blockers", "--notes", "--next" };
        if (!TryParseOptions(rest, known, out var opts, out var error))
        {
            Console.Error.WriteLine($"error: {error}");
            PrintOutcomes(Console.Error);
            return 2;
        }
        if (!opts.TryGetValue("--outcome", out var outcomeText))
        {
            Console.Error.WriteLine("error: --outcome is required to end a session.");
            PrintOutcomes(Console.Error);
            return 2;
        }
        if (!TryParseOutcome(outcomeText, out var outcome))
        {
            Console.Error.WriteLine($"error: unknown outcome '{outcomeText}'.");
            PrintOutcomes(Console.Error);
            return 2;
        }

        var ended = sessions.EndSession(
            outcome,
            completedWork: opts.GetValueOrDefault("--completed"),
            unfinishedWork: opts.GetValueOrDefault("--unfinished"),
            blockers: opts.GetValueOrDefault("--blockers"),
            futureSelfNotes: opts.GetValueOrDefault("--notes"),
            nextAction: opts.GetValueOrDefault("--next"));

        var duration = ended.Duration ?? TimeSpan.Zero;
        Console.WriteLine($"Ended the session ({FormatOutcome(ended.WrapUp!.Outcome)}, " +
                          $"lasted {FormatDuration(duration)}).");
        if (ended.WrapUp!.NextAction.Length > 0)
        {
            Console.WriteLine($"Next action: {ended.WrapUp.NextAction}");
        }
        return 0;
    }

    private static int ListSessions(ProjectRegistry registry, WorkSessionService sessions)
    {
        var active = registry.GetActiveProject();
        if (active is null)
        {
            Console.WriteLine("No active project. Select one with: project switch <name>");
            return 0;
        }
        var history = sessions.ListSessionsForActiveProject();
        if (history.Count == 0)
        {
            Console.WriteLine($"No work sessions yet for '{active.Name}'. Start one with: session start");
            return 0;
        }
        Console.WriteLine($"Work sessions for '{active.Name}' (most recent first):");
        foreach (var session in history)
        {
            var when = session.StartedUtc.ToString("u");
            if (session.IsOpen)
            {
                Console.WriteLine($"  {when}  in progress" +
                                  (session.Objective.Length > 0 ? $" — {session.Objective}" : ""));
            }
            else
            {
                Console.WriteLine($"  {when}  {FormatOutcome(session.WrapUp!.Outcome)}, " +
                                  $"{FormatDuration(session.Duration ?? TimeSpan.Zero)}" +
                                  (session.Objective.Length > 0 ? $" — {session.Objective}" : ""));
            }
        }
        return 0;
    }

    private static int Resume(ProjectRegistry registry, WorkSessionService sessions)
    {
        var active = registry.GetActiveProject();
        if (active is null)
        {
            Console.WriteLine("No active project. Select one with: project switch <name>");
            return 0;
        }
        var brief = sessions.GetResumeBriefForActiveProject();
        Console.WriteLine($"Resuming '{active.Name}'.");
        if (brief is null)
        {
            Console.WriteLine("No previous wrap-up yet — this is a fresh start.");
            return 0;
        }
        Console.WriteLine($"Last session: {FormatOutcome(brief.Outcome)} ({brief.EndedUtc:u}).");
        WriteFieldIfPresent("Unfinished", brief.UnfinishedWork);
        WriteFieldIfPresent("Blockers", brief.Blockers);
        WriteFieldIfPresent("Notes to future you", brief.FutureSelfNotes);
        WriteFieldIfPresent("Next action", brief.NextAction);
        return 0;
    }

    private static int Status(ProjectRegistry registry, WorkSessionService sessions)
    {
        var active = registry.GetActiveProject();
        Console.WriteLine(active is null
            ? "No active project. Select one with: project switch <name>"
            : $"Active project: {active.Name}" +
              (active.Description.Length > 0 ? $" — {active.Description}" : ""));

        var open = sessions.GetOpenSession();
        if (open is not null)
        {
            var objective = open.Objective.Length > 0 ? $" — {open.Objective}" : "";
            Console.WriteLine($"Session in progress since {open.StartedUtc:u}{objective}.");
            var now = DateTimeOffset.UtcNow;
            if (open.RemainingAt(now) is TimeSpan remaining)
            {
                Console.WriteLine(remaining > TimeSpan.Zero
                    ? $"Focus timer: {FormatDuration(remaining)} left."
                    : $"Focus time is up ({FormatDuration(-remaining)} over) — wrap up and switch, "
                      + "or extend with: session extend --minutes <n>");
            }
            Console.WriteLine("End it with: session end --outcome <outcome>");
        }
        else
        {
            Console.WriteLine("No session in progress. Start one with: session start");
        }
        return 0;
    }

    private static int ExtendSession(WorkSessionService sessions, string[] rest)
    {
        if (!TryParseOptions(rest, new[] { "--minutes" }, out var opts, out var error)
            || !opts.TryGetValue("--minutes", out var minutesText))
        {
            Console.Error.WriteLine($"error: {(error.Length > 0 ? error + " " : "")}Use: session extend --minutes <n>");
            return 2;
        }
        if (!double.TryParse(minutesText, out var minutes) || minutes <= 0)
        {
            Console.Error.WriteLine("error: --minutes must be a positive number.");
            return 2;
        }
        var extended = sessions.ExtendActiveSession(TimeSpan.FromMinutes(minutes));
        var remaining = extended.RemainingAt(DateTimeOffset.UtcNow) ?? TimeSpan.Zero;
        Console.WriteLine($"Extended the session — {FormatDuration(remaining)} left.");
        return 0;
    }

    private static void WriteFieldIfPresent(string label, string value)
    {
        if (value.Length > 0)
        {
            Console.WriteLine($"  {label}: {value}");
        }
    }

    /// <summary>
    /// Parses a flat "--key value" option list. Every option takes exactly one
    /// value; only keys in <paramref name="allowed"/> are accepted. Returns
    /// false with a message on an unknown key, a missing value, or a duplicate.
    /// </summary>
    private static bool TryParseOptions(
        string[] tokens, string[] allowed,
        out Dictionary<string, string> options, out string error)
    {
        options = new Dictionary<string, string>(StringComparer.Ordinal);
        error = "";
        for (var i = 0; i < tokens.Length; i++)
        {
            var key = tokens[i];
            if (!allowed.Contains(key, StringComparer.Ordinal))
            {
                error = $"unrecognized argument '{key}'.";
                return false;
            }
            if (i + 1 >= tokens.Length)
            {
                error = $"option '{key}' requires a value.";
                return false;
            }
            if (!options.TryAdd(key, tokens[++i]))
            {
                error = $"option '{key}' was given more than once.";
                return false;
            }
        }
        return true;
    }

    private static bool TryParseOutcome(string text, out SessionOutcome outcome)
    {
        // Accept kebab-case (partially-completed) and the enum name form.
        var canonical = text.Replace("-", "").Replace("_", "");
        foreach (var value in Enum.GetValues<SessionOutcome>())
        {
            if (string.Equals(value.ToString(), canonical, StringComparison.OrdinalIgnoreCase))
            {
                outcome = value;
                return true;
            }
        }
        outcome = default;
        return false;
    }

    private static string FormatOutcome(SessionOutcome outcome)
    {
        // PascalCase enum -> "partially-completed" for display.
        var name = outcome.ToString();
        var chars = new List<char>(name.Length + 4);
        for (var i = 0; i < name.Length; i++)
        {
            if (i > 0 && char.IsUpper(name[i]))
            {
                chars.Add('-');
            }
            chars.Add(char.ToLowerInvariant(name[i]));
        }
        return new string(chars.ToArray());
    }

    private static string FormatDuration(TimeSpan d) =>
        d.TotalHours >= 1
            ? $"{(int)d.TotalHours}h {d.Minutes}m"
            : d.TotalMinutes >= 1 ? $"{d.Minutes}m" : $"{d.Seconds}s";

    private static void PrintOutcomes(TextWriter writer)
    {
        var names = Enum.GetValues<SessionOutcome>().Select(FormatOutcome);
        writer.WriteLine("valid outcomes: " + string.Join(", ", names));
    }

    private static void PrintUsage(TextWriter writer)
    {
        writer.WriteLine("Context Switcher — work engine (interim CLI harness)");
        writer.WriteLine();
        writer.WriteLine("usage:");
        writer.WriteLine("  context-switcher project add <name> [--description <text>]");
        writer.WriteLine("  context-switcher project list");
        writer.WriteLine("  context-switcher project switch <name|id>");
        writer.WriteLine("  context-switcher project archive <name|id>");
        writer.WriteLine("  context-switcher session start [--objective <text>] [--minutes <n>]");
        writer.WriteLine("  context-switcher session end --outcome <outcome> " +
                         "[--completed <t>] [--unfinished <t>] [--blockers <t>] [--notes <t>] [--next <t>]");
        writer.WriteLine("  context-switcher session extend --minutes <n>");
        writer.WriteLine("  context-switcher session list");
        writer.WriteLine("  context-switcher resume");
        writer.WriteLine("  context-switcher status");
        writer.WriteLine();
        PrintOutcomes(writer);
        writer.WriteLine();
        writer.WriteLine("Data is stored in %LOCALAPPDATA%\\ContextSwitcher\\workspace.json");
        writer.WriteLine($"(override the directory with {JsonFileWorkspaceStore.DataHomeEnvVar}).");
    }
}
