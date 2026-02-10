"""
Precision validation harness for loudness metering.

Validates computed metrics against expected (golden) values with strict
tolerances aligned to professional audio measurement standards:

- LUFS: +/- 0.1 LU
- True Peak: +/- 0.2 dB
- LRA: +/- 0.2 LU
"""

import logging
import math
from dataclasses import dataclass, field

from api.models import OverallMetrics

logger = logging.getLogger(__name__)

# Tolerance constants
LUFS_TOLERANCE = 0.1   # +/- 0.1 LU
TRUE_PEAK_TOLERANCE = 0.2  # +/- 0.2 dB
LRA_TOLERANCE = 0.2    # +/- 0.2 LU


@dataclass
class ValidationResult:
    """Result of validating one set of computed metrics against expected values.

    Attributes:
        lufs_pass: Whether integrated LUFS is within tolerance.
        true_peak_pass: Whether true peak is within tolerance.
        lra_pass: Whether loudness range is within tolerance.
        lufs_diff: Absolute difference between computed and expected LUFS.
        true_peak_diff: Absolute difference for true peak.
        lra_diff: Absolute difference for LRA.
        lufs_computed: Actual computed LUFS value.
        true_peak_computed: Actual computed true peak value.
        lra_computed: Actual computed LRA value.
        overall_pass: True only when all three metrics pass.
    """

    lufs_pass: bool = False
    true_peak_pass: bool = False
    lra_pass: bool = False
    lufs_diff: float = float("inf")
    true_peak_diff: float = float("inf")
    lra_diff: float = float("inf")
    lufs_computed: float | None = None
    true_peak_computed: float | None = None
    lra_computed: float | None = None
    overall_pass: bool = field(init=False)

    def __post_init__(self) -> None:
        self.overall_pass = self.lufs_pass and self.true_peak_pass and self.lra_pass


class PrecisionValidator:
    """Validate computed loudness metrics against golden expected values."""

    def validate_against_expected(
        self,
        computed: OverallMetrics,
        expected: dict,
    ) -> ValidationResult:
        """Compare *computed* metrics to *expected* dict values.

        Args:
            computed: ``OverallMetrics`` instance from ``StandardsMetering``.
            expected: Dict with keys ``integrated_lufs``, ``loudness_range_lu``,
                ``true_peak_dbfs``.  Values may be ``None`` (meaning the
                metric is undefined, e.g. silence LUFS).

        Returns:
            A ``ValidationResult`` describing pass/fail for each metric.
        """
        # --- LUFS ---
        lufs_pass, lufs_diff = self._check_metric(
            computed.integrated_lufs,
            expected.get("integrated_lufs"),
            LUFS_TOLERANCE,
        )

        # --- True Peak ---
        tp_pass, tp_diff = self._check_metric(
            computed.true_peak_dbfs,
            expected.get("true_peak_dbfs"),
            TRUE_PEAK_TOLERANCE,
        )

        # --- LRA ---
        lra_pass, lra_diff = self._check_metric(
            computed.loudness_range_lu,
            expected.get("loudness_range_lu"),
            LRA_TOLERANCE,
        )

        result = ValidationResult(
            lufs_pass=lufs_pass,
            true_peak_pass=tp_pass,
            lra_pass=lra_pass,
            lufs_diff=lufs_diff,
            true_peak_diff=tp_diff,
            lra_diff=lra_diff,
            lufs_computed=computed.integrated_lufs,
            true_peak_computed=computed.true_peak_dbfs,
            lra_computed=computed.loudness_range_lu,
        )

        logger.info(
            "Validation – LUFS: %s (diff=%.3f), TP: %s (diff=%.3f), "
            "LRA: %s (diff=%.3f) => %s",
            "PASS" if lufs_pass else "FAIL",
            lufs_diff,
            "PASS" if tp_pass else "FAIL",
            tp_diff,
            "PASS" if lra_pass else "FAIL",
            lra_diff,
            "PASS" if result.overall_pass else "FAIL",
        )

        return result

    def generate_validation_report(
        self, results: dict[str, ValidationResult], expected_data: dict
    ) -> str:
        """Generate a Markdown validation report.

        Args:
            results: Mapping of test file name to ``ValidationResult``.
            expected_data: Full expected-values dict keyed by file name.

        Returns:
            Markdown-formatted report string.
        """
        lines: list[str] = [
            "# Loudness Metering Precision Validation Report",
            "",
            "## Summary",
            "",
        ]

        total = len(results)
        passed = sum(1 for r in results.values() if r.overall_pass)
        lines.append(f"- **Total test vectors:** {total}")
        lines.append(f"- **Passed:** {passed}")
        lines.append(f"- **Failed:** {total - passed}")
        lines.append(f"- **Pass rate:** {passed / total * 100:.0f}%" if total else "- N/A")
        lines.append("")

        # Tolerance table
        lines.extend([
            "## Tolerances",
            "",
            "| Metric | Tolerance |",
            "|--------|-----------|",
            f"| Integrated LUFS | +/- {LUFS_TOLERANCE} LU |",
            f"| True Peak | +/- {TRUE_PEAK_TOLERANCE} dB |",
            f"| Loudness Range | +/- {LRA_TOLERANCE} LU |",
            "",
        ])

        # Detailed results table
        lines.extend([
            "## Detailed Results",
            "",
            "| Test File | Metric | Expected | Computed | Delta | Status |",
            "|-----------|--------|----------|----------|-------|--------|",
        ])

        for filename, result in results.items():
            exp = expected_data.get(filename, {})
            # LUFS row
            exp_lufs = exp.get("integrated_lufs")
            lines.append(
                f"| {filename} | LUFS | {self._fmt(exp_lufs)} | "
                f"{self._fmt(result.lufs_computed)} | "
                f"{result.lufs_diff:.3f} | {'PASS' if result.lufs_pass else 'FAIL'} |"
            )
            # True Peak row
            exp_tp = exp.get("true_peak_dbfs")
            lines.append(
                f"| | True Peak | {self._fmt(exp_tp)} | "
                f"{self._fmt(result.true_peak_computed)} | "
                f"{result.true_peak_diff:.3f} | {'PASS' if result.true_peak_pass else 'FAIL'} |"
            )
            # LRA row
            exp_lra = exp.get("loudness_range_lu")
            lines.append(
                f"| | LRA | {self._fmt(exp_lra)} | "
                f"{self._fmt(result.lra_computed)} | "
                f"{result.lra_diff:.3f} | {'PASS' if result.lra_pass else 'FAIL'} |"
            )

        lines.append("")

        # Overall verdict
        overall = "PASS" if all(r.overall_pass for r in results.values()) else "FAIL"
        lines.extend([
            "## Overall Verdict",
            "",
            f"**{overall}** – {'All' if overall == 'PASS' else 'Not all'} test vectors "
            "are within professional-grade tolerances.",
            "",
        ])

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_metric(
        computed_value: float | None,
        expected_value: float | None,
        tolerance: float,
    ) -> tuple[bool, float]:
        """Check a single metric against its expected value.

        Returns:
            (passed, absolute_difference).  When both values are ``None``
            the check passes with diff 0.0.
        """
        # Both undefined → pass (e.g. silence LUFS)
        if computed_value is None and expected_value is None:
            return True, 0.0

        # One defined, other not → fail
        if computed_value is None or expected_value is None:
            return False, float("inf")

        # Handle non-finite values
        if not math.isfinite(computed_value) or not math.isfinite(expected_value):
            return False, float("inf")

        diff = abs(computed_value - expected_value)
        return diff <= tolerance, diff

    @staticmethod
    def _fmt(value: float | None) -> str:
        """Format a metric value for display."""
        if value is None:
            return "N/A"
        return f"{value:.2f}"
