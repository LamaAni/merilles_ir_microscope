from enum import Enum
import math
from typing import List, Union
from tabor.tabor_client.config import (
    TABOR_DEFAULT_DEVICE_CONFIG,
    TaborDeviceConfig,
)
from tabor.tabor_client.consts import (
    TABOR_SEGMENT_MIN_LENGTH,
    TABOR_SEGMENT_MIN_SIZE_STEP,
)


class TaborDataSegment(dict):
    def __init__(
        self,
        values: List[float] = None,
        segment_id: int = -1,
        last_value: float = None,
        is_binary: bool = False,
        config: TaborDeviceConfig = None,
        from_data_segment: "TaborDataSegment" = None,
    ):
        """Describes the tabor data segment to be uploaded as waveform

        Args:
            values (List[float], optional): The data generation voltage values. Defaults to None.
            segment_id (int, optional): The segment ID to be used in the tabor server (may overwrite old). Defaults to -1.
            last_value (float, optional): The last value, incase the segment is shorted then the min length. Defaults to None.
            min_value (float, optional): The min value of the segment range. Defaults to TABOR_SEGMENT_VOLT_MIN.
            max_value (float, optional): The max value of the segment range. Defaults to TABOR_SEGMENT_VOLT_MAX.
            min_length (int, optional): The min length of a tabor segment. Defaults to TABOR_SEGMENT_MIN_LENGTH.
            from_data_segment (TaborDataSegment, optional): Load from another tabor segment. Defaults to None.
        """
        super().__init__(from_data_segment or {})

        self.segment_id = segment_id
        self.last_value = last_value
        self.is_binary = is_binary
        self.config = config or (
            from_data_segment.config
            if from_data_segment
            else TABOR_DEFAULT_DEVICE_CONFIG
        )

        if values:
            self["values"] = list(values)

    @property
    def is_binary(self) -> bool:
        return self.get("is_binary", None)

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
    def values(self) -> List[float]:
        if "values" not in self:
            self["values"] = []
        return self.get("values")

    def get_values(self):
        return self.values

    @classmethod
    def ceil_to_segment_step_size(
        cls, seg_len: int, step_size: int = TABOR_SEGMENT_MIN_SIZE_STEP
    ):
        leftover = seg_len % step_size
        if leftover > 0:
            seg_len += step_size - leftover
        return seg_len

    def to_segment_values(self, values: List[float] = None):
        """Returns the data values as tabor proper segment values

        Returns:
            List[float] as numbers: The values converted to tabore
                digestable range
        """
        vals = list(values or self.get_values())
        vals_len = len(vals)

        if vals_len < self.config.segment_min_length:
            vals_len = self.config.segment_min_length

        # Adjust to step size
        vals_len = self.ceil_to_segment_step_size(
            vals_len, self.config.segment_min_size_step
        )

        # Add the padding
        val_padding = vals_len - len(vals)

        if val_padding > 0:
            # TODO: add interpolation?
            repeat_value = self.last_value if self.last_value is not None else vals[-1]
            vals += [repeat_value for _ in range(val_padding)]

        return vals

    def to_dac_values(
        self,
        device_config: TaborDeviceConfig = None,
        values: List[float] = None,
    ):
        values = self.to_segment_values(values)
        if self.is_binary:
            return [1 if val > 0 else 0 for val in values]

        device_config = device_config or TABOR_DEFAULT_DEVICE_CONFIG
        max_value = self.config.max_voltage_out
        min_value = self.config.min_voltage_out

        assert max_value >= min_value, ValueError(
            "max_value must be larger or equal to min_value"
        )

        value_range = max_value - min_value
        dac_range = device_config.dac_range

        def conert_data_value(val: Union[int, float]):
            if val < min_value:
                val = min_value
            elif val > max_value:
                val = max_value

            val = int((1.0 * (val - min_value) / value_range) * dac_range)

            return val

        return [conert_data_value(v) for v in values]

    def to_plot_data(
        self,
        values: List[float] = None,
        as_dac_values: bool = False,
    ):
        y_vals = (
            self.to_segment_values(values=values)
            if not as_dac_values
            else self.to_dac_values(values=values)
        )
        x_vals = [i * 1.0 / self.config.freq for i in range(len(y_vals))]
        return x_vals, y_vals

    def clone(self):
        """Creates a clone of the current data segment"""
        return TaborDataSegment(segment_id=self.segment_id, from_data_segment=self)


class TaborWaveform(dict):
    """A waveform description, channel and segment data"""

    def __init__(
        self,
        channel: int,
        values: Union[TaborDataSegment, List[float], float] = None,
        offset: float = 0,
        amplitude: float = 1,
    ) -> None:
        assert isinstance(channel, int) and channel > -1, ValueError(
            "Invalid segment type. Must be a positive integer"
        )

        self.channel = channel
        if isinstance(values, (float, int)):
            values = [values]
        if not isinstance(values, TaborDataSegment):
            values = TaborDataSegment(segment_id=self.channel % 2 + 1, values=values)
        elif values.segment_id < 0:
            values.segment_id = self.channel % 2 + 1

        self.data_segment: TaborDataSegment = values
        self.amplitude = amplitude
        self.offset = offset

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

    @property
    def offset(self) -> float:
        return self.get("offset", 0)

    @offset.setter
    def offset(self, val: float):
        self["offset"] = val

    @property
    def amplitude(self) -> float:
        return self.get("amplitude", 0.5)

    @amplitude.setter
    def amplitude(self, val: float):
        self["amplitude"] = val

    def to_plot_data(
        self,
        values: List[float] = None,
        freq: float = None,
    ):
        freq = freq or TABOR_DEFAULT_DEVICE_CONFIG.freq
        return self.data_segment.to_plot_data(values=values)
