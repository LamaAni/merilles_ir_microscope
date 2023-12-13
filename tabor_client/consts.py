from enum import Enum


class TaborWaveformDACMode:
    """The tabor waveform DAC data transfer value size in bits"""

    uint_8 = 8
    uint_16 = 16


class TaborWaveformDACModeFreq:
    uint_8 = int(9e9)
    uint_16 = int(2.5e9)


TABOR_SEGMENT_MIN_LENGTH = 1024
TABOR_SEGMENT_STEP_SIZE = 32
