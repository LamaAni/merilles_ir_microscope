import math
from tabor_client import TaborClient
from tabor_client.data import TaborSignDataSegment, TaborWaveform

if __name__ == "__main__":
    host = "134.74.27.64"
    port = "5025"
    client = TaborClient(host, port, keep_command_and_query_record=True)
    client.connect()

    freq = 1e7
    last_value = None

    wav1 = TaborWaveform(
        channel=1,
        values=TaborSignDataSegment(
            freq=freq,
            last_value=last_value,
        ),
    )
    wav2 = TaborWaveform(
        channel=2,
        values=TaborSignDataSegment(
            freq=freq,
            last_value=last_value,
            phase=math.pi * 1,
        ),
    )
    client.waveform_out(wav1, wav2)

    client.voltage_out(1, 0.5)
    client.voltage_out(2, 0.3)
    client.off(1, 2)

    client.disconnect()
