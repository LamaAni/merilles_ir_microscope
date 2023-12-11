import re
from typing import List
from common.log import log
import pyvisa
from pyvisa.resources.tcpip import TCPIPInstrument


class TaborSocketClientException(Exception):
    def __init__(self, *args: object, code: int = -1) -> None:
        if code > -1:
            args = list(args) + [code]
        super().__init__(*args)
        self.code = code

    def __str__(self) -> str:
        val = super().__str__()
        if self.code > 0:
            val = f"{val} (code: {self.code})"
        return super().__str__()


class TaborSocketClient:
    def __init__(
        self,
        host: str,
        port: int = 5025,
        raise_errors: bool = True,
        timeout: int = 30000,
        read_bytes_chunk: int = 4096,
    ) -> None:
        self.resource_name = f"TCPIP0::{host}::{port}::SOCKET"
        self.resource_manager = pyvisa.ResourceManager("@py")
        self.__resource: TCPIPInstrument = None
        self.seperator = ";"
        self.raise_errors = raise_errors
        self.timeout = timeout
        self.read_bytes_chunk = read_bytes_chunk

    def __del__(self):
        if self.__resource is not None:
            self.disconnect()

    @property
    def resource(self) -> TCPIPInstrument:
        return self.__resource

    def connect(self):
        self.__resource = self.resource_manager.open_resource(self.resource_name)
        self.__resource.read_termination = "\n"
        self.__resource.write_termination = "\n"
        self.__resource.timeout = self.timeout
        self.query("*IDN?")

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
        rsp = self.resource.query(query).split(self.seperator)
        if not force_list and len(queries) < 2:
            return rsp[0]
        return rsp

    def command(
        self,
        *queries: str,
        force_list: bool = False,
        raise_errors: bool = None,
    ):
        self.__assert_connected()
        assert len(queries) > 0, ValueError("At least one query must be sent")
        assert all([q.strip().startswith(":") for q in queries]), ValueError(
            "Command queries myst start with ':'"
        )

        raise_errors = self.raise_errors if raise_errors is None else raise_errors
        query = self.__compose_query("*CLS", *queries, ":SYST:ERR?")

        log.debug("Sending command: " + query)
        rsp = self.resource.query(query).split(self.seperator)
        err = self.__parse_error_response(rsp[-1])
        rsp = rsp[:-1]

        if err.code != 0:
            raise TaborSocketClientException("Error sending command") from err
        if len(rsp) == 0:
            return None
        if force_list and len(queries) < 2:
            return rsp[0]
        return rsp

    def write_binary(
        self,
        command: str,
        data: bytes,
    ):
        self.__assert_connected()
        query = self.__compose_query("*CLS", command)

        try:
            self.resource.write_binary_values(
                query,
                data,
            )

            self.resource.read()
        except Exception as ex:
            raise TaborSocketClientException("Error while writing binary data") from ex

        err = self.__parse_error_response(self.resource.query(":SYST:ERR?"))
        if err.code != 0:
            raise TaborSocketClientException("Error writing binary data") from err

    def read_binary(
        self,
        command: str,
    ):
        self.__assert_connected()
        query = self.__compose_query("*CLS", command)

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

    def write_waveform(self, channel: int, wave: List[float]):
        self.query("*CLS")
        self.query(f":INST:CHAN {channel}", )

        waveform_segment = channel % 2 + 1
        pass

    def static_out(
        self,
        channel: int = 1,
        up: bool = True,
        voltage: float = 1,
    ):
        pass


host = "134.74.27.64"
port = "5025"
client = TaborSocketClient(host, port)
client.connect()

log.info(client.query("*IDN?", "*IDN?"))
log.info(client.query(":INST:CHAN 1", ":OUTP?"))
log.info(client.command(":INST:CHAN 1", ":FREQ 1e9", ":OUTP ON"))

client.disconnect()
