from tabor.tabor_client.consts import (
    TABOR_SEGMENT_MIN_LENGTH,
    TABOR_SEGMENT_MIN_SIZE_STEP,
    TABOR_SEGMENT_VOLT_MAX,
    TABOR_SEGMENT_VOLT_MIN,
)


class TaborDeviceConfig:
    """Configuration class for a tabor device"""

    model = "any"

    # DAC
    freq = float(2.5e9)
    dac_is_16_bit = True
    min_voltage_out = TABOR_SEGMENT_VOLT_MIN
    max_voltage_out = TABOR_SEGMENT_VOLT_MAX

    # SEGMENT SETTINGS
    segment_min_length = TABOR_SEGMENT_MIN_LENGTH
    segment_min_size_step = TABOR_SEGMENT_MIN_SIZE_STEP

    @property
    def data_bits(self) -> int:
        return 16 if self.dac_is_16_bit else 8

    @property
    def dac_range(self) -> int:
        return 2**16 - 1 if self.dac_is_16_bit else 2**8 - 1

    @property
    def binary_data_type(self) -> str:
        return "H" if self.dac_is_16_bit else "b"

    @classmethod
    def set_as_global_default(cls, config: "TaborDeviceConfig" = None):
        tabor_set_default_device_config(config or cls())


class TaborDefaultDeviceConfig(TaborDeviceConfig):
    pass


class TaborP9082DeviceConfig(TaborDeviceConfig):
    dac_is_16_bit = False
    freq = int(9e9)
    model = "P9082?"


global TABOR_DEFAULT_DEVICE_CONFIG
TABOR_DEFAULT_DEVICE_CONFIG = TaborDefaultDeviceConfig()


def tabor_set_default_device_config(device_config: TaborDeviceConfig):
    assert isinstance(device_config, TaborDeviceConfig), ValueError(
        "device_config must be of type TaborDeviceConfig"
    )
    global TABOR_DEFAULT_DEVICE_CONFIG
    TABOR_DEFAULT_DEVICE_CONFIG = device_config
