import math
from typing import List, Union
from tabor_client.consts import (
    TABOR_SEGMENT_MIN_LENGTH,
    TABOR_SEGMENT_STEP_SIZE,
    TaborWaveformDACModeFreq,
)


class TaborDataSegment(dict):
    def __init__(
        self,
        values: List[float] = None,
        segment_id: int = -1,
        last_value: float = None,
        min_value: float = 0,
        max_value: float = 1,
        min_length: int = TABOR_SEGMENT_MIN_LENGTH,
        from_data_segment: "TaborDataSegment" = None,
    ):
        super().__init__(from_data_segment or {})

        self.segment_id = segment_id
        self.min_value = min_value
        self.max_value = max_value
        self.last_value = last_value
        self.min_length = min_length

        if values:
            self["values"] = list(values)

    @property
    def segment_id(self) -> int:
        return self.get("segment_id", None)

    @segment_id.setter
    def segment_id(self, val: int):
        self["segment_id"] = val

    @property
    def last_value(self) -> float:
        return self.get("last_value", None)

    @last_value.setter
    def last_value(self, val: float):
        self["last_value"] = val

    @property
    def min_value(self) -> float:
        return self.get("min_value", 0)

    @min_value.setter
    def min_value(self, val: float):
        self["min_value"] = val

    @property
    def max_value(self) -> float:
        return self.get("max_value", 1)

    @max_value.setter
    def max_value(self, val: float):
        self["max_value"] = val

    @property
    def values(self) -> List[float]:
        if "values" not in self:
            self["values"] = []
        return self.get("values")

    @property
    def min_length(self) -> int:
        return self.get("min_length", TABOR_SEGMENT_MIN_LENGTH)

    @min_length.setter
    def min_length(self, val: int):
        self["min_length"] = val

    def to_segment_byte_data(self, values: List[float] = None):
        """Returns the data values as tabor transferrable data types

        Returns:
            List[byte8 | byte16] as numbers: The values converted to tabore
                digestable range
        """
        vals = list(values or self.values)
        vals_len = len(vals)
        if vals_len < self.min_length:
            vals_len = self.min_length

        if vals_len < TABOR_SEGMENT_MIN_LENGTH:
            vals_len = TABOR_SEGMENT_MIN_LENGTH

        # Adjust to step size
        val_len_leftover = vals_len % TABOR_SEGMENT_STEP_SIZE
        if val_len_leftover > 0:
            vals_len = vals_len - val_len_leftover + TABOR_SEGMENT_STEP_SIZE

        val_padding = vals_len - len(vals)

        if val_padding > 0:
            repeat_value = self.last_value if self.last_value is not None else vals[-1]
            vals += [repeat_value for _ in range(val_padding)]
        return vals

    def clone(self):
        """Creates a clone of the current data segment"""
        return TaborDataSegment(segment_id=self.segment_id, from_data_segment=self)


class TaborSignDataSegment(TaborDataSegment):
    def __init__(
        self,
        freq: float,
        phase: float = 0,
        repeate: int = 0,
        segment_id: int = -1,
        last_value: float = None,
        min_value: float = 0,
        max_value: float = 1,
        min_length: int = TABOR_SEGMENT_MIN_LENGTH,
        from_data_segment: TaborDataSegment = None,
        base_freq: float = TaborWaveformDACModeFreq.uint_16,
    ):
        super().__init__(
            segment_id=segment_id,
            values=None,
            last_value=last_value,
            min_value=min_value,
            max_value=max_value,
            min_length=min_length,
            from_data_segment=from_data_segment,
        )

        self.freq = freq
        self.repeat = repeate
        self.phase = phase
        self.base_freq = base_freq

    @property
    def base_freq(self) -> float:
        return self.get("base_freq", TaborWaveformDACModeFreq.uint_16)

    @base_freq.setter
    def base_freq(self, val: float):
        self["base_freq"] = val

    @property
    def freq(self) -> float:
        return self.get("freq", 1e5)

    @freq.setter
    def freq(self, val: float):
        self["freq"] = val

    @property
    def repeat(self) -> int:
        return self.get("repeat", -1)

    @repeat.setter
    def repeat(self, val: int):
        self["repeat"] = val

    @property
    def phase(self) -> float:
        return self.get("phase", 0)

    @phase.setter
    def phase(self, val: float):
        self["phase"] = val

    @property
    def values(self) -> List[float]:
        raise ValueError(
            "The values property cannot be accessed in TaborSignDataSegment"
        )

    @values.setter
    def values(self, val: List[float]):
        raise ValueError(
            "The values property cannot be accessed in TaborSignDataSegment"
        )

    def to_segment_byte_data(self):
        return super().to_segment_byte_data(
            values=self.create_sine_waveform(),
        )

    def create_sine_waveform(
        self,
    ):
        repeate = self.repeat
        signle_wave_steps = int(math.floor(self.base_freq / self.freq))

        if repeate <= 0:
            min_steps = (
                TABOR_SEGMENT_MIN_LENGTH
                if self.min_length < TABOR_SEGMENT_MIN_LENGTH
                else self.min_length
            )
            repeate = 1
            while signle_wave_steps * repeate < min_steps:
                repeate += 1

        range_steps = signle_wave_steps * repeate

        return [
            0.5 + 0.5 * math.sin(2.0 * math.pi * i / signle_wave_steps + self.phase)
            for i in range(range_steps)
        ]


class TaborWaveform(dict):
    """A waveform description, channel and segment data"""

    def __init__(
        self,
        channel: int,
        values: Union[TaborDataSegment, List[float]] = None,
    ) -> None:
        assert isinstance(channel, int) and channel > -1, ValueError(
            "Invalid segment type. Must be a positive integer"
        )

        self.channel = channel

        if not isinstance(values, TaborDataSegment):
            values = TaborDataSegment(segment_id=self.channel % 2 + 1, values=values)
        elif values.segment_id < 0:
            values.segment_id = self.channel % 2 + 1

        self.data_segment: TaborDataSegment = values

    @property
    def channel(self) -> int:
        return self.get("channel", -1)

    @channel.setter
    def channel(self, val: int):
        self["channel"] = val

    @property
    def data_segment(self) -> TaborDataSegment:
        return self.get("data_segment", None)

    @data_segment.setter
    def data_segment(self, val: TaborDataSegment):
        self["data_segment"] = val

    pass