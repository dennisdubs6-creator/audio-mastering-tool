"""
Standalone precision validation script for loudness metering.

Loads all test vectors from the golden corpus, computes metrics using
``StandardsMetering``, validates against expected values using
``PrecisionValidator``, and generates a Markdown validation report.

Usage::

    cd backend
    python -m analysis.loudness.validate_precision

Exit codes:
    0 – All test vectors pass within tolerance.
    1 – One or more test vectors failed validation.
"""

import json
import logging
import os
import sys

from analysis.loudness.standards import StandardsMetering
from analysis.loudness.validator import PrecisionValidator
from dsp.audio_loader import AudioLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_TEST_VECTORS_DIR = os.path.join(_MODULE_DIR, "test_vectors")
_EXPECTED_VALUES_PATH = os.path.join(_TEST_VECTORS_DIR, "expected_values.json")
_REPORT_OUTPUT_PATH = os.path.join(_MODULE_DIR, "VALIDATION_REPORT.md")


def main() -> int:
    """Run precision validation and generate report.

    Returns:
        0 if all vectors pass, 1 otherwise.
    """
    # Load expected values
    with open(_EXPECTED_VALUES_PATH, "r") as f:
        expected_data: dict = json.load(f)

    # Discover test WAV files
    wav_files = sorted(
        f for f in os.listdir(_TEST_VECTORS_DIR) if f.endswith(".wav")
    )
    if not wav_files:
        logger.error("No WAV test vectors found in %s", _TEST_VECTORS_DIR)
        logger.error("Run the test vector generation script first.")
        return 1

    logger.info("Found %d test vectors in %s", len(wav_files), _TEST_VECTORS_DIR)

    loader = AudioLoader()
    metering = StandardsMetering()
    validator = PrecisionValidator()

    results: dict = {}

    for fname in wav_files:
        if fname not in expected_data:
            logger.warning("No expected values for %s – skipping", fname)
            continue

        path = os.path.join(_TEST_VECTORS_DIR, fname)
        logger.info("Processing: %s", fname)

        try:
            audio = loader.load_wav(path)
            metrics = metering.compute_overall_metrics(audio)
            result = validator.validate_against_expected(
                metrics, expected_data[fname]
            )
            results[fname] = result

            status = "PASS" if result.overall_pass else "FAIL"
            logger.info(
                "  %s – LUFS diff=%.3f (%s), TP diff=%.3f (%s), "
                "LRA diff=%.3f (%s)",
                status,
                result.lufs_diff,
                "PASS" if result.lufs_pass else "FAIL",
                result.true_peak_diff,
                "PASS" if result.true_peak_pass else "FAIL",
                result.lra_diff,
                "PASS" if result.lra_pass else "FAIL",
            )
        except Exception:
            logger.exception("Error processing %s", fname)
            return 1

    # Generate validation report
    report = validator.generate_validation_report(results, expected_data)
    with open(_REPORT_OUTPUT_PATH, "w") as f:
        f.write(report)
    logger.info("Validation report written to %s", _REPORT_OUTPUT_PATH)

    # Summary
    total = len(results)
    passed = sum(1 for r in results.values() if r.overall_pass)
    failed = total - passed

    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY: %d/%d passed, %d failed", passed, total, failed)
    logger.info("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
