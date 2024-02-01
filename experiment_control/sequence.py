from typing import Any, Dict, List
from experiment_control.interfaces import DeviceInterface
from experiment_control.sequence_channel import SequenceChannel


class Sequence:
    """Implements an experiment sequence to be executed. The sequnce
    contains the full IO configuration for an experiment.
    """

    def __init__(
        self,
        freqeuency: float = None,
    ) -> None:
        self.__channels: Dict[str, SequenceChannel] = {}
        self.__devices: Dict[str, DeviceInterface] = {}
        self.__t: float = 0
        self.freqeuency = freqeuency

    @property
    def channels(self):
        """Holds the channel by name implementation for the sequence"""
        return self.__channels

    @property
    def devices(self):
        """A list of active devices"""
        return self.__devices

    @property
    def t(self) -> float:
        """The current experiment time, in seconds, from the experiment start time"""
        return self.__t

    # region Device and channel control
    def add_device(
        self,
        name: str,
        device: DeviceInterface,
    ):
        self.__devices[name] = device

    def add_channel(
        self,
        name: str,
        device_name: str,
        physical_address: str | Any,
        allow_missing_device: bool = False,
    ):
        assert allow_missing_device or device_name in self.devices, Exception(
            "Device not configured: " + device_name
        )

        if name in self.channels:
            raise Exception("Channel already exists: " + name)

        self.channels[name] = SequenceChannel(
            name=name,
            device_name=device_name,
            physical_address=physical_address,
        )

    def __validate_channels(self, channels: List[str]):
        for c in channels:
            if c not in self.channels:
                raise ValueError("Channel not found: " + c)

    # endregion

    # region Timing and timeline

    def wait(self, dt: float):
        assert self.__t + dt > 0, Exception(
            "Invalid time. The operation would result in time lower the zero"
        )
        self.__t += dt

    def goto(self, t: float):
        assert t > 0, Exception("Cannot set a time lower then zero")
        self.__t = t

    # endregion
    def write(
        self,
        channel: str | List[str],
        data: int | float | List[int | float],
        frequency: float = None,
        timedeltas: List[float] = None,
        overwrite: bool = True,
    ):
        self.__validate_channels(channel)
        frequency = frequency or self.freqeuency

        assert timedeltas is not None or frequency is not None, ValueError(
            "You must provide either a frequency or timedelats (no default frequency defined)"
        )

        if not isinstance(data, list):
            data = [data]

        assert len(data) > 0, ValueError("You must send at least one value to write")

        if timedeltas is None:
            # Using freqeuency to determine the time offset in seconds
            dt = 1 / frequency
            timedeltas = [dt for _ in range(len(data))]

        # Converted timedeltas to timestamps
        timestamps = []
        cur_t = 0
        for dt in timedeltas:
            timestamps.append(cur_t)
            cur_t += dt

        # Writing to the channel.
        for c in channel:
            self.channels[c].write_values(
                timestamps=timestamps,
                values=data,
                overwrite=overwrite,
            )

    def delete(
        self,
        channel: str | List[str],
        duration: float,
    ):
        self.__validate_channels(channel)

        from_t = self.t
        to_t = self.t + duration

        for c in channel:
            self.channels[c].delete_events(from_t, to_t)

    def get_plot_data(self) -> Dict[str, tuple[float, float]]:
        rslt = {}
        for c in self.channels:
            ts, vals = self.channels[c].get_plot_data()
            rslt[c] = {
                "t": ts,
                "v": vals,
            }

    def plot(self, *channel: str):
        if len(channel) == 0:
            channel = list(self.channels.keys())

        import matplotlib.pyplot as plt

        plt.figure()
        for c in self.channels:
            ts, vals = self.channels[c].get_plot_data()
            plt.plot(ts, vals)
