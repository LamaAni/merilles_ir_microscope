from ast import Tuple
from datetime import datetime
import math
import re
import time
from typing import Iterable, List, Union
from common.log import log
import pyvisa
import pyvisa.util
from pyvisa.resources.tcpip import TCPIPInstrument


class TaborSocketClientException(Exception):
    def __init__(self, *args: object, code: int = -1) -> None:
        if code is None:
            code = -1
        if not isinstance(code, int):
            try:
                code = int(code)
            except Exception:
                pass
        if code > -1:
            args = list(args) + [code]
        super().__init__(*args)
        self.code = code

    def __str__(self) -> str:
        val = super().__str__()
        if self.code > 0:
            val = f"{val} (code: {self.code})"
        return super().__str__()


class TaborWaveformDACMode:
    int_8 = 8
    int_16 = 16


class TaborWaveform(dict):
    TABOR_SEGMENT_MIN_LENGTH = 1024
    TABOR_SEGMENT_STEP_SIZE = 32

    def __init__(
        self,
        channel: int,
        values: List[float] = None,
        segment_id: int = None,
        repeat_last_value_in_padding: bool = True,
        min_value: float = 0,
        max_value: float = 1,
    ) -> None:
        assert isinstance(channel, int) and channel > -1, ValueError(
            "Invalid segment type. Must be a positive integer"
        )
        super()
        self.channel = channel
        self.values: List[float] = values or []
        self.repeat_last_value_in_padding = repeat_last_value_in_padding
        self.min_value = min_value
        self.max_value = max_value

        self.__segment_id = segment_id

    @property
    def segment_id(self) -> int:
        return (
            self.__segment_id if self.__segment_id is not None else self.channel % 2 + 1
        )

    @segment_id.setter
    def segment_id(self, val: int):
        self.__segment_id = val

    def to_segment_data(self):
        # returns the iterator for binary data conversion
        # curretnly very simple convert to array.
        vals = list(self.values)
        padding_length = 0
        if len(vals) < self.TABOR_SEGMENT_MIN_LENGTH:
            padding_length = self.TABOR_SEGMENT_MIN_LENGTH - len(vals)
        else:
            padding_length = self.TABOR_SEGMENT_STEP_SIZE - (
                len(vals) % self.TABOR_SEGMENT_STEP_SIZE
            )
        if padding_length > 0:
            repeat_value = vals[-1] if self.repeat_last_value_in_padding else 0
            vals += [repeat_value for _ in range(padding_length)]
        return vals


class TaborSocketClient:
    def __init__(
        self,
        host: str,
        port: int = 5025,
        raise_errors: bool = True,
        timeout: int = 30000,
        read_bytes_chunk: int = 4096,
        dac_mode: TaborWaveformDACMode = None,
        keep_command_and_query_record: bool = False,
    ) -> None:
        self.resource_name = f"TCPIP0::{host}::{port}::SOCKET"
        self.resource_manager = pyvisa.ResourceManager("@py")
        self.__resource: TCPIPInstrument = None
        self.seperator = ";"
        self.raise_errors = raise_errors
        self.timeout = timeout
        self.read_bytes_chunk = read_bytes_chunk
        self.dac_mode = dac_mode

        self._model = None
        self._freq = None
        self._max_dac_value = None
        self.keep_command_and_query_record = keep_command_and_query_record
        self.__command_record: List[Tuple] = []

    def __del__(self):
        if self.__resource is not None:
            self.disconnect()

    @property
    def resource(self) -> TCPIPInstrument:
        return self.__resource

    @property
    def model(self) -> str:
        return self._model

    @property
    def freq(self) -> float:
        return self._freq

    @property
    def command_record(self) -> List[Tuple]:
        return self.__command_record

    @property
    def dac_max_value(self) -> int:
        return self._max_dac_value

    def __append_to_command_record(self, cmd_sent: str):
        if not self.keep_command_and_query_record:
            return

        self.__command_record.append((datetime.now(), cmd_sent))

    def print_command_record(self) -> List[str]:
        lns = []
        for rcd in self.__command_record:
            lns.append(f"[{rcd[0].isoformat()}] {rcd[1]}")
        return lns

    def connect(self):
        self.__resource = self.resource_manager.open_resource(self.resource_name)
        self.__resource.read_termination = "\n"
        self.__resource.write_termination = "\n"
        self.__resource.timeout = self.timeout

        self.clear_error_list()

        self._model = self.query(":SYST:iNF:MODel?")

        log.debug(
            f"Connectd to Tabor model {self.model} @ {self.resource_name}, IDN: {self.query('*IDN?')}"
        )

        if "P9082" in self.model:
            self.dac_mode = TaborWaveformDACMode.int_8
            self._freq = 9e9
            self._max_dac_value = 2**8 - 1
        else:
            self.dac_mode = TaborWaveformDACMode.int_16
            self._freq = 2.5e9
            self._max_dac_value = 2**16 - 1

        # Setting interaction frequency
        self.command(f":FREQ:RAST {self.freq}")
        log.debug(
            f"Interaction frequency set, and retrived as: {self.query(':FREQ:RAST?')}"
        )

    def disconnect(self):
        self.__resource.close()
        self.__resource = None

    def __assert_connected(self):
        assert self.resource is not None, TaborSocketClientException(
            "Not connected, please run .connect()"
        )

    def __compose_query(self, *queries: str):
        queries = [q.strip() for q in queries]
        return self.seperator.join(queries)

    def __parse_error_response(self, rsp):
        [error_code, error_string] = re.split(r",\s*", rsp)
        return TaborSocketClientException(error_string, code=error_code)

    def query(self, *queries: str, force_list: bool = False):
        self.__assert_connected()
        assert len(queries) > 0, ValueError("At least one query must be sent")
        query = self.__compose_query(*queries)
        log.debug("Sending query: " + query)
        self.__append_to_command_record(query)
        rsp = self.resource.query(query).split(self.seperator)
        if not force_list and len(queries) < 2:
            return rsp[0]
        return rsp

    def clear_error_list(self):
        self.command("*CLS")

    def command(
        self,
        *queries: str,
        force_list: bool = False,
        raise_errors: bool = None,
        synchronize: bool = False,
    ):
        if synchronize:
            self.query("*OPC?")

        self.__assert_connected()
        assert len(queries) > 0, ValueError("At least one query must be sent")

        raise_errors = self.raise_errors if raise_errors is None else raise_errors

        compose = list(queries)
        if synchronize:
            compose.insert(0, "*OPC?")
            compose.append("*OPC?")
        compose.append(":SYST:ERR?")
        query = self.__compose_query(*compose)

        log.debug("Sending command: " + query)
        self.__append_to_command_record(query)
        rsp = self.resource.query(query).split(self.seperator)
        err = self.__parse_error_response(rsp[-1])
        rsp = rsp[:-1]

        if err.code != 0:
            raise err from TaborSocketClientException("Error sending command")
        if len(rsp) == 0:
            return None
        if force_list and len(queries) < 2:
            return rsp[0]
        return rsp

    def write_binary(
        self,
        command: str,
        data: Union[Iterable, bytes, List[float]],
        datatype: str = None,
    ):
        self.__assert_connected()
        query = self.__compose_query("*OPC?", command)

        try:
            if datatype is None:
                self.resource.write_binary_values(query, data)
            else:
                self.resource.write_binary_values(query, data, datatype=datatype)

            self.resource.read()
        except Exception as ex:
            raise ex from TaborSocketClientException("Error while writing binary data")

        err = self.__parse_error_response(self.resource.query(":SYST:ERR?"))
        if err.code != 0:
            raise err from TaborSocketClientException("Error writing binary data")

    def read_binary(
        self,
        command: str,
    ):
        self.__assert_connected()
        query = self.__compose_query(command)

        self.resource.write(query)

        # reading the byte response header
        buff = self.resource.read_bytes(1)
        assert buff == b"#", TaborSocketClientException(
            f"Expected bytes read header to be #, but found {buff}"
        )

        # reading the number of bytes
        buff = self.resource.read_bytes(1)
        assert b"0" <= buff <= b"9", TaborSocketClientException(
            f"Expected bytes digits to be an number, but found {buff}"
        )
        num_bytes_digits = int(buff.decode("utf-8"))
        num_bytes = int(
            self.resource.read_bytes(
                num_bytes_digits,
                chunk_size=1,
            ).decode("utf-8")
        )

        # reading bytes
        buff = self.resource.read_bytes(num_bytes, chunk_size=self.read_bytes_chunk)

        return buff

    def __waveform_values_to_data_values(self, vals: List[float], max_value, min_value):
        # normalizing and shifting data values
        assert max_value >= min_value, ValueError(
            "max_value must be larger or equal to min_value"
        )
        value_range = max_value - min_value

        def conert_data_value(val: Union[int, float]):
            if val < min_value:
                val = min_value
            elif val > max_value:
                val = max_value

            val = math.floor(
                (1.0 * (val - min_value) / value_range) * self.dac_max_value
            )

            return val

        return [conert_data_value(v) for v in vals]

    def write_waveform(self, *waveforms: TaborWaveform):
        for wav in waveforms:
            # self.query(":INST:CHAN 1", ":OUTP?")
            wav_data = wav.to_segment_data()

            # To data values
            self.command(
                f":TRAC:DEL {wav.segment_id}",
                f":TRAC:DEF {wav.segment_id}, {len(wav_data)}",  # Define the segment
                f":TRAC:SEL {wav.segment_id}",  # Select the segment
                f":TRAC:FORM U{self.dac_mode}",  # Set the data format
            )

            # Write the values data for the waveform
            wav_binary_data = self.__waveform_values_to_data_values(
                wav_data,
                wav.max_value,
                wav.min_value,
            )
            self.write_binary(
                ":TRAC:DATA",
                wav_binary_data,
                datatype="H" if self.dac_mode == TaborWaveformDACMode.int_16 else "b",
            )

    def trigger_waveform(self, *waveforms: TaborWaveform, synchronize: bool = True):
        queries = []

        for wav in waveforms:
            queries.append(f":INST:CHAN {wav.channel}")
            queries.append(":OUTP OFF")
            # queries.append(f":FUNC:MODE ARB {wav.segment_id}")
            queries.append(f":FUNC:MODE:SEGM {wav.segment_id}")
            queries.append(":OUTP ON")

        self.command(*queries, synchronize=synchronize)

    def waveform_out(self, *waveforms: TaborWaveform, synchronize: bool = True):
        # self.stop_channel(*waveforms)
        self.write_waveform(*waveforms)
        self.trigger_waveform(*waveforms, synchronize=synchronize)

    def stop_channel(self, *channel: Union[int, TaborWaveform]):
        queries = []
        for c in channel:
            if isinstance(c, TaborWaveform):
                c = c.channel
            queries.append(f":INST:CHAN {c}")
            queries.append(":OUTP OFF")

        self.command(*queries)
        self.query("*OPC?")

    def static_out(
        self,
        channel: int = 1,
        value: float = 1,
    ):
        return self.waveform_out(TaborWaveform(channel=channel, values=[value]))


if __name__ == "__main__":
    host = "134.74.27.64"
    port = "5025"
    client = TaborSocketClient(host, port, keep_command_and_query_record=True)
    client.connect()

    # log.info(client.query(":INST:CHAN 1", ":OUTP?"))
    # log.info(client.command(":INST:CHAN 1", ":FREQ 1e9", ":OUTP ON"))

    def preper_sin_waveform(freq=1e7):
        steps = int(math.floor(client.freq / freq))
        return [0.5 + 0.5 * math.sin(2.0 * math.pi * i / steps) for i in range(steps)]

    wav = TaborWaveform(1, preper_sin_waveform())
    log.info("STARTING")

    # client.static_out(wav.channel, 0)
    # time.sleep(5)
    client.waveform_out(wav)
    # time.sleep(10)
    # client.stop_channel(wav)-
    # client.static_out(wav.channel, 1)
    # time.sleep(5)

    log.info("DONE")

    client.disconnect()

    print()
    print("\n".join(client.print_command_record()))
