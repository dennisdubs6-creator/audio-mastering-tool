"""
Analysis package for computing per-band audio metrics.

Provides the ``AnalysisEngine`` orchestrator and individual metric modules
for level, dynamics, spectral, stereo, harmonics, and transient analysis.

Also provides standards-compliant overall loudness metering via the
``loudness`` sub-package.
"""

from .engine import AnalysisEngine
from .loudness.standards import StandardsMetering
from .loudness.validator import PrecisionValidator, ValidationResult

__all__ = [
    "AnalysisEngine",
    "StandardsMetering",
    "PrecisionValidator",
    "ValidationResult",
]
