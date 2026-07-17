using System.Reflection;

namespace ContextSwitcher.Work.Tests;

/// <summary>Marks a public parameterless instance method as a test case.</summary>
[AttributeUsage(AttributeTargets.Method)]
public sealed class TestAttribute : Attribute { }

/// <summary>Minimal deterministic assertions (ADR-0008 pure-BCL policy).</summary>
public static class Check
{
    public static void That(bool condition, string because)
    {
        if (!condition)
        {
            throw new CheckFailedException(because);
        }
    }

    public static void Equal<T>(T expected, T actual, string what)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
        {
            throw new CheckFailedException($"{what}: expected '{expected}' but got '{actual}'");
        }
    }

    public static TException Throws<TException>(Action action, string what)
        where TException : Exception
    {
        try
        {
            action();
        }
        catch (TException expected)
        {
            return expected;
        }
        catch (Exception other)
        {
            throw new CheckFailedException(
                $"{what}: expected {typeof(TException).Name} but got {other.GetType().Name}: {other.Message}");
        }
        throw new CheckFailedException(
            $"{what}: expected {typeof(TException).Name} but nothing was thrown");
    }
}

public sealed class CheckFailedException : Exception
{
    public CheckFailedException(string message) : base(message) { }
}

/// <summary>
/// Reflection-based runner: instantiates every class in this assembly that
/// contains [Test] methods and runs each method. Exit code 0 = all passed.
/// </summary>
public static class TestRunner
{
    public static int RunAll()
    {
        var assembly = Assembly.GetExecutingAssembly();
        int passed = 0, failed = 0;

        var fixtures = assembly.GetTypes()
            .Where(t => t.IsClass && !t.IsAbstract
                        && t.GetMethods().Any(m => m.GetCustomAttribute<TestAttribute>() is not null))
            .OrderBy(t => t.FullName, StringComparer.Ordinal);

        foreach (var fixtureType in fixtures)
        {
            var methods = fixtureType.GetMethods(BindingFlags.Public | BindingFlags.Instance)
                .Where(m => m.GetCustomAttribute<TestAttribute>() is not null)
                .OrderBy(m => m.Name, StringComparer.Ordinal);

            foreach (var method in methods)
            {
                var label = $"{fixtureType.Name}.{method.Name}";
                try
                {
                    var fixture = Activator.CreateInstance(fixtureType)!;
                    try
                    {
                        method.Invoke(fixture, null);
                    }
                    finally
                    {
                        (fixture as IDisposable)?.Dispose();
                    }
                    Console.WriteLine($"PASS: {label}");
                    passed++;
                }
                catch (TargetInvocationException tie) when (tie.InnerException is not null)
                {
                    Console.WriteLine($"FAIL: {label}");
                    Console.WriteLine($"      {tie.InnerException.GetType().Name}: {tie.InnerException.Message}");
                    failed++;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"FAIL: {label}");
                    Console.WriteLine($"      {ex.GetType().Name}: {ex.Message}");
                    failed++;
                }
            }
        }

        Console.WriteLine();
        Console.WriteLine($"work-engine-tests: {passed} passed, {failed} failed");
        return failed == 0 && passed > 0 ? 0 : 1;
    }
}

public static class Program
{
    public static int Main() => TestRunner.RunAll();
}
