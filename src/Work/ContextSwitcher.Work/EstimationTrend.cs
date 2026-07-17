namespace ContextSwitcher.Work;

/// <summary>Which way a person's time estimates lean (ADR-0017).</summary>
public enum EstimationBias
{
    /// <summary>Sessions tend to run over — estimates are too short.</summary>
    UnderEstimates,

    /// <summary>Sessions tend to finish early — estimates are too long.</summary>
    OverEstimates,

    /// <summary>Estimates are close to actual (within tolerance).</summary>
    WellCalibrated,
}

/// <summary>
/// A derived estimation-accuracy summary over closed, timed sessions for a
/// scope (ADR-0017). Pure data — produced by
/// <see cref="WorkSessionService.ComputeEstimationTrend"/>.
/// </summary>
public sealed record EstimationTrend
{
    /// <summary>Human-readable scope ("all projects" or a project name).</summary>
    public required string Scope { get; init; }

    /// <summary>Number of closed, timed sessions considered.</summary>
    public required int TimedCount { get; init; }

    /// <summary>Mean estimate quality as a percentage (0–100); 0 when none.</summary>
    public required double AverageAccuracyPercent { get; init; }

    /// <summary>Mean signed error (actual − planned): positive = ran over.</summary>
    public required TimeSpan AverageError { get; init; }

    /// <summary>Which way estimates lean.</summary>
    public required EstimationBias Bias { get; init; }

    /// <summary>Average accuracy % of the more recent half, or null when &lt; 2 timed sessions.</summary>
    public double? RecentAccuracyPercent { get; init; }

    /// <summary>Average accuracy % of the earlier half, or null when &lt; 2 timed sessions.</summary>
    public double? EarlierAccuracyPercent { get; init; }

    /// <summary>True when the recent half is more accurate than the earlier half; null when &lt; 2.</summary>
    public bool? Improving { get; init; }
}
