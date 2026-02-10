# Create a test script: test_my_audio.py
from pathlib import Path
from analysis.engine import AnalysisEngine
from dsp.audio_loader import AudioLoader
from dsp.stft_processor import STFTProcessor
from dsp.band_integrator import BandIntegrator

# Load your WAV file
audio_path = Path("path/to/your/audio.wav")
loader = AudioLoader()
audio_data = loader.load(audio_path)

# Create analysis engine
stft_processor = STFTProcessor()
band_integrator = BandIntegrator()
engine = AnalysisEngine(stft_processor, band_integrator)

# Run analysis
results = engine.analyze(audio_data)

# Print results
print(f"Overall LUFS: {results['overall_metrics']['lufs']:.2f}")
print(f"True Peak: {results['overall_metrics']['true_peak']:.2f}")
print(f"LRA: {results['overall_metrics']['lra']:.2f}")

# Print per-band results
for band_name, metrics in results['band_metrics'].items():
    print(f"\n{band_name}:")
    print(f"  RMS: {metrics['level']['rms_db']:.2f} dB")
    print(f"  Dynamic Range: {metrics['dynamics']['dynamic_range_db']:.2f} dB")
