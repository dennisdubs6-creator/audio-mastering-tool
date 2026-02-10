"""
Text generation functions for the three recommendation verbosity levels.

Each function accepts a band name, metric category, delta value, and
direction, and returns a human-readable recommendation string.
"""

from recommendations.rules import BAND_FREQ_RANGES


def _freq_range(band_name: str) -> str:
    """Return a human-readable frequency range for the given band."""
    return BAND_FREQ_RANGES.get(band_name, band_name)


def _direction_word(delta: float) -> str:
    """Return 'louder' or 'quieter' based on delta sign."""
    return "louder" if delta > 0 else "quieter"


def _action_word(delta: float) -> str:
    """Return 'Reduce' or 'Boost' based on delta sign."""
    return "Reduce" if delta > 0 else "Boost"


def _gentle_action(delta: float) -> str:
    """Return 'reducing' or 'boosting' based on delta sign."""
    return "reducing" if delta > 0 else "boosting"


def generate_analytical_text(
    band_name: str,
    metric_category: str,
    delta: float,
) -> str:
    """Generate raw delta format text.

    Example: "Low band (20-200 Hz) is 3.2 dB louder than reference"
    """
    freq = _freq_range(band_name)
    direction = _direction_word(delta)
    abs_delta = abs(delta)

    if metric_category == "stereo_width":
        return (
            f"{band_name.replace('_', ' ').title()} band ({freq}) stereo width "
            f"is {abs_delta:.1f}% {'wider' if delta > 0 else 'narrower'} than reference"
        )

    if metric_category == "dynamic_range":
        return (
            f"{band_name.replace('_', ' ').title()} band ({freq}) dynamic range "
            f"is {abs_delta:.1f} dB {'greater' if delta > 0 else 'less'} than reference"
        )

    return (
        f"{band_name.replace('_', ' ').title()} band ({freq}) "
        f"is {abs_delta:.1f} dB {direction} than reference"
    )


def generate_suggestive_text(
    band_name: str,
    metric_category: str,
    delta: float,
) -> str:
    """Generate gentle suggestion text.

    Example: "Consider reducing low (20-200 Hz) by ~3 dB"
    """
    freq = _freq_range(band_name)
    action = _gentle_action(delta)
    abs_delta = abs(delta)

    if metric_category == "stereo_width":
        width_action = "narrowing" if delta > 0 else "widening"
        return (
            f"Consider {width_action} the {band_name.replace('_', ' ')} band ({freq}) "
            f"stereo image by ~{abs_delta:.0f}%"
        )

    if metric_category == "dynamic_range":
        dr_action = "compressing" if delta > 0 else "expanding"
        return (
            f"Consider {dr_action} the {band_name.replace('_', ' ')} band ({freq}) "
            f"by ~{abs_delta:.0f} dB"
        )

    return (
        f"Consider {action} {band_name.replace('_', ' ')} ({freq}) "
        f"by ~{abs_delta:.0f} dB"
    )


def generate_prescriptive_text(
    band_name: str,
    metric_category: str,
    delta: float,
) -> str:
    """Generate specific action text.

    Example: "Reduce 20-200 Hz by 3.2 dB using EQ"
    """
    freq = _freq_range(band_name)
    action = _action_word(delta)
    abs_delta = abs(delta)

    if metric_category == "stereo_width":
        width_action = "Narrow" if delta > 0 else "Widen"
        return (
            f"{width_action} {freq} stereo image by {abs_delta:.1f}% "
            f"using mid/side EQ or stereo imager"
        )

    if metric_category == "dynamic_range":
        dr_action = "Compress" if delta > 0 else "Expand"
        tool = "compressor" if delta > 0 else "transient shaper"
        return (
            f"{dr_action} {freq} by {abs_delta:.1f} dB using {tool}"
        )

    return f"{action} {freq} by {abs_delta:.1f} dB using EQ"


def generate_overall_analytical_text(
    metric_name: str,
    user_value: float,
    ref_value: float,
    unit: str,
) -> str:
    """Generate analytical text for an overall metric comparison."""
    delta = user_value - ref_value
    direction = "higher" if delta > 0 else "lower"
    return (
        f"{metric_name} is {abs(delta):.1f} {unit} {direction} than reference "
        f"({user_value:.1f} vs {ref_value:.1f} {unit})"
    )


def generate_overall_suggestive_text(
    metric_name: str,
    user_value: float,
    ref_value: float,
    unit: str,
) -> str:
    """Generate suggestive text for an overall metric comparison."""
    delta = user_value - ref_value
    action = "reducing" if delta > 0 else "increasing"
    return (
        f"Consider {action} {metric_name.lower()} by ~{abs(delta):.0f} {unit} "
        f"to match the reference"
    )


def generate_overall_prescriptive_text(
    metric_name: str,
    user_value: float,
    ref_value: float,
    unit: str,
) -> str:
    """Generate prescriptive text for an overall metric comparison."""
    delta = user_value - ref_value
    action = "Reduce" if delta > 0 else "Increase"
    return (
        f"{action} {metric_name.lower()} by {abs(delta):.1f} {unit} "
        f"to reach target of {ref_value:.1f} {unit}"
    )
