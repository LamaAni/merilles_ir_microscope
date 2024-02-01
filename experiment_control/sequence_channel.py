from typing import Any, List
from experiment_control.collections import SortedDict


class SequenceChannelEvent:
    def __init__(
        self,
        t: float,
        value: Any = None,
        number_of_samples: int = 1,
    ) -> None:
        self.t = t
        self.value = value
        self.number_of_samples: int = number_of_samples


class SequenceChannel:
    def __init__(
        self,
        name: str,
        device_name: str,
        physical_address: str | Any,
    ) -> None:
        self.__timeline: SortedDict = SortedDict()
        self.name = name
        self.device_name = device_name
        self.physical_address = physical_address

    def write_values(
        self,
        timestamps: List[float],
        values: List[float],
        overwrite: bool = True,
    ):
        assert len(timestamps) == len(values), Exception(
            "The number of values must match the number of timestamps"
        )
        # Convert to events.
        events = [
            SequenceChannelEvent(t=timestamps[i], value=values[i])
            for i in range(len(timestamps))
        ]
        return self.set_events(events=events, overwrite=overwrite)

    def read_values(
        self,
        timestamps: List[float],
        number_of_samples: int | List[int],
        overwrite: bool = True,
    ):
        if isinstance(number_of_samples, int):
            number_of_samples = [number_of_samples for _ in range(timestamps)]

        assert len(timestamps) == len(number_of_samples), Exception(
            "The number of values must match the number of timestamps"
        )
        events = [
            SequenceChannelEvent(
                t=timestamps[i], number_of_samples=number_of_samples[i]
            )
            for i in range(len(timestamps))
        ]
        return self.set_events(events=events, overwrite=overwrite)

    def set_events(self, events: List[SequenceChannelEvent], overwrite: bool = True):
        # Deleting old.
        if overwrite:
            times = [e.t for e in events]
            self.delete_events(min(times), max(times))

        for e in events:
            self.__timeline[e.t] = e

    def delete_events(self, from_t: float, to_t: float):
        for k in self.__timeline.unsorted_keys():
            if k > to_t or k < from_t:
                continue
            del self.__timeline[k]

    def get_plot_data(self):
        timestamps = []
        values = []
        e: SequenceChannelEvent = None
        for e in self.__timeline.values():
            timestamps.append(e.t)
            values.append(e.value)
        return timestamps, values
