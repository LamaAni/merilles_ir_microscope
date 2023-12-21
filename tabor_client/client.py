import re
import pyvisa
import pyvisa.util

from ast import Tuple
from datetime import datetime
from typing import Iterable, List, Union
from pyvisa.resources.tcpip import TCPIPInstrument
from tabor_client.config import (
    TaborDefaultDeviceConfig,
    TaborDeviceConfig,
    TaborP9082DeviceConfig,
)

from tabor_client.exceptions import TaborClientException, TaborClientSocketException
from tabor_client.data import TaborWaveform, TaborDataSegment
from tabor_client.log import log


class TaborClient:
    def __init__(
        self,
        host: str,
        port: int = 5025,
        raise_errors: bool = True,
        timeout: int = 30000,
        read_bytes_chunk: int = 4096,
        keep_command_and_query_record: bool = False,
        device_config: TaborDeviceConfig = None,
    ) -> None:
        self.resource_name = f"TCPIP0::{host}::{port}::SOCKET"
        self.resource_manager = pyvisa.ResourceManager("@py")
        self.__resource: TCPIPInstrument = None
        self.seperator = ";"
        self.raise_errors = raise_errors
        self.timeout = timeout
        self.read_bytes_chunk = read_bytes_chunk
        self.keep_command_and_query_record = keep_command_and_query_record

        self.__command_record: List[Tuple] = []
        self.__device_config = device_config

    def __del__(self):
        if self.__resource is not None:
            self.disconnect()

    @property
    def device_config(self):
        return self.__device_config

    @property
    def resource(self) -> TCPIPInstrument:
        return self.__resource

    @property
    def command_record(self) -> List[Tuple]:
        return self.__command_record

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

        model = self.query(":SYST:iNF:MODel?")

        log.debug(
            f"Connectd to Tabor model {model} @ {self.resource_name}, IDN: {self.query('*IDN?')}"
        )

        if self.device_config is None:
            if "P9082" in model:
                self.__device_config = TaborP9082DeviceConfig()
            else:
                self.__device_config = TaborDefaultDeviceConfig()
            self.__device_config.model = model

        # Setting interaction frequency
        self.command(f":FREQ:RAST {self.device_config.freq}")
        log.debug(
            f"Interaction frequency set, and retrived as: {self.query(':FREQ:RAST?')}"
        )

    def disconnect(self):
        self.__resource.close()
        self.__resource = None

    def __assert_connected(self):
        assert self.resource is not None, TaborClientException(
            "Not connected, please run .connect()"
        )

    def __clean_queries(self, queries: Iterable[str]):
        return [q.strip() for q in queries if q is not None and len(q.strip()) > 0]

    def __compose_query(self, *queries: str):
        return self.seperator.join(self.__clean_queries(queries))

    def __parse_error_response(self, rsp):
        [error_code, error_string] = re.split(r",\s*", rsp)
        return TaborClientSocketException(error_string, code=error_code)

    def query(
        self,
        *queries: str,
        force_list: bool = False,
        sync: bool = False,
    ):
        self.__assert_connected()
        queries = self.__clean_queries(queries)

        assert len(queries) > 0, ValueError("At least one query must be sent")
        queries: List[str] = list(queries)
        if sync:
            queries.insert(0, "*OPC?")
            queries.append("*OPC?")
        query = self.__compose_query(*queries)
        log.debug("Sending query: " + query)
        self.__append_to_command_record(query)
        rsp = self.resource.query(query).split(self.seperator)
        if not force_list and len(queries) < 2:
            return rsp[0]
        return rsp

    def command(
        self,
        *queries: str,
        force_list: bool = False,
        raise_errors: bool = None,
        sync: bool = False,
    ):
        if sync:
            self.query("*OPC?")

        self.__assert_connected()
        queries = self.__clean_queries(queries)

        assert len(queries) > 0, ValueError("At least one query must be sent")

        raise_errors = self.raise_errors if raise_errors is None else raise_errors

        compose = list(queries)
        if sync:
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
            raise err from TaborClientException("Error sending command")
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
            raise ex from TaborClientException("Error while writing binary data")

        err = self.__parse_error_response(self.resource.query(":SYST:ERR?"))
        if err.code != 0:
            raise err from TaborClientException("Error writing binary data")

    def read_binary(
        self,
        command: str,
    ):
        self.__assert_connected()
        query = self.__compose_query(command)

        self.resource.write(query)

        # reading the byte response header
        buff = self.resource.read_bytes(1)
        assert buff == b"#", TaborClientException(
            f"Expected bytes read header to be #, but found {buff}"
        )

        # reading the number of bytes
        buff = self.resource.read_bytes(1)
        assert b"0" <= buff <= b"9", TaborClientException(
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

    def write_segments(self, *segments: Union[TaborDataSegment, TaborWaveform]):
        assert all(
            isinstance(
                (seg.data_segment if isinstance(seg, TaborWaveform) else seg),
                TaborDataSegment,
            )
            for seg in segments
        ), ValueError(
            "All segments or waveform.data_segment must be of instance TaborDataSegment"
        )

        for seg in segments:
            if isinstance(seg, TaborWaveform):
                seg = seg.data_segment

            # self.query(":INST:CHAN 1", ":OUTP?")
            seg_dac_data = seg.to_dac_values(
                device_config=self.device_config,
            )

            # To data values
            self.command(
                f":TRAC:DEL {seg.segment_id}",
                f":TRAC:DEF {seg.segment_id}, {len(seg_dac_data)}",  # Define the segment
                f":TRAC:SEL {seg.segment_id}",  # Select the segment
                f":TRAC:FORM U{self.device_config.data_bits}",  # Set the data format
            )

            log.debug(
                (
                    f"WRITING SEGMENT {seg.segment_id} of length {len(seg_dac_data)}"
                    " (x{self.device_config.data_bits} bits)"
                )
            )
            self.write_binary(
                ":TRAC:DATA",
                seg_dac_data,
                datatype=self.device_config.binary_data_type,
            )

    # region Simple methods
    # -------------------

    def clear_error_list(self):
        self.command("*CLS")

    # endregion

    # region Simple command methods
    # -------------------

    def waveform_out(
        self,
        *wavs: TaborWaveform,
        turn_output_off_before_starting: bool = True,
    ):
        for wav in wavs:
            self.write_segments(wav)

        for wav in wavs:
            self.command(
                f":INST:CHAN:SEL {wav.channel}",
                ":OUTP OFF" if turn_output_off_before_starting else None,
                ":MODE DIR",
                # ":INT NONE",
                f":VOLT:AMPL {wav.amplitude}",
                f":VOLT:OFFS {wav.offset}",
                ":FUNC:MODE ARB",
                f":FUNC:MODE:SEGM {wav.data_segment.segment_id}",
                "*OPC?",
                ":OUTP ON",
            )
        # self.query("*OPC?")

    def voltage_out(
        self,
        channel: int,
        value: float,
        turn_output_off_before_starting: bool = True,
    ):
        wav = TaborWaveform(channel=channel, values=[value])

        self.waveform_out(
            wav,
            turn_output_off_before_starting=turn_output_off_before_starting,
        )

    def reset(self):
        self.command(
            "*CLS",
            "*RST",
            "*OPC?",
        )

    def off(
        self,
        *channel,
    ):
        self.command(
            *[self.__compose_query(f":INST:CHAN:SEL {c}", ":OUTP OFF") for c in channel]
        )

    def select_channel(
        self,
        channel,
    ):
        self.command(f":INST:CHAN:SEL {channel}")

    def on(
        self,
        *channel,
    ):
        self.command(
            *[self.__compose_query(f":INST:CHAN:SEL {c}", ":OUTP ON") for c in channel]
        )

    # endregion


if __name__ == "__main__":
    from time import sleep

    host = "134.74.27.64"
    port = "5025"
    client = TaborClient(host, port, keep_command_and_query_record=True)
    client.connect()

    log.info("Setting channel 1")
    client.voltage_out(1, 0.5)
    sleep(1)
    log.info("Setting channel 2")
    client.voltage_out(2, 0.3)

    client.disconnect()
