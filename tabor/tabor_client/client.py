import enum
import re
from typing_extensions import deprecated
import pyvisa
import pyvisa.util
import pyvisa.constants

from ast import Tuple
from datetime import datetime
from typing import Callable, Iterable, List, Union
from pyvisa.resources.tcpip import TCPIPInstrument
from tabor.tabor_client.config import (
    TaborDefaultDeviceConfig,
    TaborDeviceConfig,
    TaborP9082DeviceConfig,
)

from tabor.tabor_client.exceptions import (
    TaborClientException,
    TaborClientSocketException,
)
from tabor.tabor_client.data import TaborWaveform, TaborDataSegment
from tabor.tabor_client.log import log


class TaborClientRequestType(enum.Enum):
    query = "query"
    command = "command"


class TaborClientRequest:
    REQUEST_REGEXP = TABOR_REGEXP = (
        r"\s*([*][a-zA-Z0-9]+)(\?*)\s*([;]|$)|\s*(([\:]\s*[a-zA-Z0-9]+)+(\?*))\s+([^;\n]+|)\s*([;]|$)"
    )

    def __init__(
        self, rtype: TaborClientRequestType, request: str, params: str | List[str]
    ) -> None:
        self.__rtype = rtype
        self.__request: str = request
        self.__params = [params] if isinstance(params, str) else params
        self.__as_string: str = None

    @property
    def rtype(self) -> TaborClientRequestType:
        return self.__rtype

    @property
    def params(self) -> List[str]:
        return self.__params

    @property
    def request(self) -> List[str]:
        return self.__request

    @property
    def as_string(self) -> str:
        if self.__as_string is None:
            self.__as_string = " ".join([self.request, *self.params])
        return self.__as_string

    @classmethod
    def parse(cls, *requests: str) -> List["TaborClientRequest"]:
        # Convert the requests to a string of requests.
        # Split
        requests = re.findall(
            cls.REQUEST_REGEXP,
            "\n".join(requests),
            flags=re.MULTILINE,
        )

        rslt: List[TaborClientRequest] = []
        for parsed in requests:
            request = parsed[0] or parsed[3]
            request = re.sub(r"[^A-Z0-9:]", "", request)
            rtype = TaborClientRequestType.command
            if parsed[1] == "?" or parsed[5] == "?":
                rtype = TaborClientRequestType.query
                request += "?"
            params = []
            if parsed[6]:
                # This may have params
                params = [parsed[6]]
            request = TaborClientRequest(
                rtype=rtype,
                request=request,
                params=params,
            )
            rslt.append(request)
        return rslt

    def __str__(self) -> str:
        return self.as_string

    def __repr__(self) -> str:
        return self.rtype.value + " " + self.__str__()


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
        reconnect_timeout: int = 1,
    ) -> None:
        self.resource_name = f"TCPIP0::{host}::{port}::SOCKET"
        self.resource_manager = pyvisa.ResourceManager("@py")
        self.__resource: TCPIPInstrument = None
        self.seperator = ";"
        self.raise_errors = raise_errors
        self.timeout = timeout
        self.reconnect_timeout = reconnect_timeout
        self.read_bytes_chunk = read_bytes_chunk
        self.keep_command_and_query_record = keep_command_and_query_record

        self.__command_record: List[Tuple] = []
        self.__device_config = device_config
        self.__channel_select_command = "INST:CHAN:SEL"
        self.__last_called = 0

    def __del__(self):
        if self.__resource is not None:
            self.disconnect()

    @property
    def last_called(self):
        return datetime.fromtimestamp(self.__last_called)

    @property
    def requires_reconnect(self) -> bool:
        return datetime.now().timestamp() - self.__last_called > self.reconnect_timeout

    @property
    def device_config(self):
        return self.__device_config

    @property
    def resource(self) -> TCPIPInstrument:
        return self.__resource

    @property
    def command_record(self) -> List[Tuple]:
        return self.__command_record

    # region Core client methods

    def __append_to_command_record(self, cmd_sent: str):
        if not self.keep_command_and_query_record:
            return

        self.__command_record.append((datetime.now(), cmd_sent))

    def print_command_record(self) -> List[str]:
        lns = []
        for rcd in self.__command_record:
            lns.append(f"[{rcd[0].isoformat()}] {rcd[1]}")
        return lns

    def __create_http_resource(self):
        if self.__resource:
            try:
                self.resource.close()
            except Exception:
                pass

        self.__resource = self.resource_manager.open_resource(
            self.resource_name,
            access_mode=pyvisa.constants.AccessModes.no_lock,
        )
        self.__resource.read_termination = "\n"
        self.__resource.write_termination = "\n"
        self.__resource.timeout = self.timeout
        return self.__resource

    def ping(self):
        start = datetime.now()
        model = self.query(":SYST:iNF:MODel?")
        dt = datetime.now() - start
        return dt, model

    def connect(self):
        self.__create_http_resource()
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

        return self

    def disconnect(self):
        self.__resource.close()
        self.__resource = None

    def __assert_connected(self):
        if not self.resource:
            self.connect()
        if self.requires_reconnect:
            self.__create_http_resource()

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
        rsp = self.raw_query(query).split(self.seperator)
        if not force_list and len(queries) < 2:
            return rsp[0]
        return rsp

    def raw_query(self, *queries: str):
        for q in queries:
            self.__append_to_command_record(queries)

        return self.resource.query(self.__compose_query(*queries))

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
        rsp = self.raw_query(query).split(self.seperator)
        err = self.__parse_error_response(rsp[-1])
        rsp = rsp[:-1]

        if err.code != 0:
            raise err from TaborClientException("Error sending command")
        if len(rsp) == 0:
            return None
        if force_list and len(queries) < 2:
            return rsp[0]
        return rsp

    @classmethod
    def parse(
        cls,
        *requests: str | TaborClientRequest,
    ):
        requests: List[str] = list(requests)

        parsed: List[TaborClientRequest] = []
        for rq in requests:
            if isinstance(rq, TaborClientRequest):
                parsed.append(rq)
            else:
                for r in TaborClientRequest.parse(rq):
                    parsed.append(r)
        return parsed

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

        err = self.__parse_error_response(self.raw_query(":SYST:ERR?"))
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

    # endregion

    # region Simple command methods
    # -------------------

    def clear_error_list(self):
        self.command("*CLS")

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
            *[
                self.__compose_query(
                    f":{self.__channel_select_command} {c}", ":OUTP OFF"
                )
                for c in channel
            ]
        )

    def select_channel(
        self,
        channel,
    ):
        self.command(f":{self.__channel_select_command} {channel}")

    def on(
        self,
        *channel,
    ):
        self.command(
            *[
                self.__compose_query(
                    f":{self.__channel_select_command} {c}", ":OUTP ON"
                )
                for c in channel
            ]
        )

    # endregion

    # region waveforms and voltage out

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

    def waveform_out(
        self,
        *wavs: Union[TaborWaveform, TaborDataSegment, List[float]],
        turn_output_off_before_starting: bool = True,
    ):
        def to_wav(wav: Union[TaborWaveform, TaborDataSegment, List[float]]):
            if isinstance(wav, TaborWaveform):
                return wav
            elif isinstance(wav, TaborDataSegment):
                return TaborWaveform()

        wavs = [to_wav(w) for w in wavs]
        for wav in wavs:
            self.write_segments(wav)

        for wav in wavs:
            self.command(
                f":{self.__channel_select_command} {wav.channel}",
                ":OUTP OFF" if turn_output_off_before_starting else None,
                ":MODE DIR",
                # ":INT NONE",
                # f":VOLT:AMPL {wav.amplitude}",
                f":VOLT:OFFS {wav.offset}",
                ":FUNC:MODE ARB",
                f":FUNC:MODE:SEGM {wav.data_segment.segment_id}",
                "*OPC?",
                ":OUTP ON",
            )

    def voltage_out(
        self,
        channel: int,
        data: Union[TaborWaveform, TaborDataSegment, List[float], float],
        turn_output_off_before_starting: bool = True,
    ):
        if isinstance(data, TaborWaveform):
            data.channel = channel
        else:
            data = TaborWaveform(channel, data)

        return self.waveform_out(
            data,
            turn_output_off_before_starting=turn_output_off_before_starting,
        )

    # endregion

    # region Counter in

    def counter_prepare(
        self,
        dt: float,
        *channels: int,
        trigger_level: float = 0.1,
    ):
        cmnd_list = []
        for channel in channels:
            cmnd_list += [
                f":DIG:CHAN CH{channel}",
                f":DIG:TRIG:SOUR CH{channel}",
                f":DIG:TRIG:LEV1 {trigger_level}",
                ":DIG:CHAN:STAT ENAB",
                ":DIG:TRIG:TYPE EDGE",
                f":DIG:PULS INT, FIX, {dt}",
            ]
        return self.command("*CLS", *cmnd_list)

    def counter_trigger(self):
        return self.command(":DIG:PULS:TRIG:IMM")

    def counter_read(
        self,
        *channels: int,
    ) -> List[int]:
        rslt = self.query(":DIG:PULS:COUN?")
        assert "," in rslt, Exception(f"Failed to read: {rslt}")
        rslt = rslt.strip()
        counts = [int(v) for v in re.split(r"[\s,]+", rslt)]
        if channels:
            counts = [counts[c] for c in channels]
        return counts

    # endregion

    # region marker data

    def marker_select(self, channel: int, marker: int, get_command: bool = False):
        command = [
            f":{self.__channel_select_command} {channel}",
            f":MARK:SEL {marker}",
        ]
        if get_command:
            return command
        return self.command(*command)

    def marker_on(self, channel: int, marker: int):
        self.command(
            self.marker_select(channel=channel, marker=marker, get_command=True),
            ":MARK ON",
        )

    def marker_off(self, channel: int, marker: int):
        self.command(
            self.marker_select(channel=channel, marker=marker, get_command=True),
            ":MARK OFF",
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
