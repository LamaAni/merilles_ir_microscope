from abc import abstractmethod


class DeviceInterface:
    @abstractmethod
    def on_prepare():
        pass

    @abstractmethod
    def on_execute():
        pass
