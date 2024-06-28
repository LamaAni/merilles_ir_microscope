import numpy as np
from typing import Callable

from tabor.tabor_client.config import TaborDeviceConfig
from tabor.tabor_client.data import TaborDataSegment


class TaborFunctionSegment(TaborDataSegment):
    def __init__(
        self,
        duration: float,
        func: Callable,
        segment_id: int = -1,
        last_value: float = None,
        config: TaborDeviceConfig = None,
        from_data_segment: TaborDataSegment = None,
    ):
        super().__init__(
            [],
            segment_id,
            last_value,
            config,
            from_data_segment,
        )

        self.duration = duration
        self.func = func

    @property
    def number_of_points(self):
        return self.ceil_to_segment_step_size(
            int(self.duration * self.config.freq), self.config.segment_min_size_step
        )

    def get_values(self):
        points = self.number_of_points
        return self.func(np.linspace(0, points / self.config.freq, points))
