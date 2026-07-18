namespace ContextSwitcher.Work;

/// <summary>Base type for all Work Engine domain failures (ADR-0008).</summary>
public abstract class WorkEngineException : Exception
{
    protected WorkEngineException(string message) : base(message) { }
    protected WorkEngineException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>Invalid input or an operation that would violate a domain invariant.</summary>
public sealed class ValidationException : WorkEngineException
{
    public ValidationException(string message) : base(message) { }
}

/// <summary>The referenced entity does not exist in the workspace.</summary>
public sealed class NotFoundException : WorkEngineException
{
    public NotFoundException(string message) : base(message) { }
}

/// <summary>
/// The persisted workspace exists but cannot be read (malformed content or an
/// unsupported schema version). User data is never silently reset or
/// overwritten in response to this failure (ADR-0008).
/// </summary>
public sealed class StoreCorruptException : WorkEngineException
{
    public StoreCorruptException(string message) : base(message) { }
    public StoreCorruptException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>
/// The store could not be locked exclusively for a guarded update within the
/// configured timeout — another process or thread holds it. User data is left
/// untouched; the operation was not applied and can be retried (ADR-0026).
/// </summary>
public sealed class StoreLockedException : WorkEngineException
{
    public StoreLockedException(string message) : base(message) { }
    public StoreLockedException(string message, Exception inner) : base(message, inner) { }
}
