import math
from tabor_client import TaborClient
from tabor_client.data import (
    TaborFunctionGeneratorSegment,
    TaborFunctionGeneratorSegmentFType,
    TaborWaveform,
    TaborDataSegment,
)

if __name__ == "__main__":
    host = "134.74.27.64"
    port = "5025"
    client = TaborClient(host, port, keep_command_and_query_record=True)
    client.connect()

    freq = 1e7
    last_value = None

    dcl = 1024
    segment = TaborDataSegment(
        values=[v for v in [0.1, 1, 0, 1, 0.5, 0.3, 0] for _ in range(500)],
    )

    dc1 = TaborWaveform(
        channel=1,
        offset=0.2,
        values=segment,
    )

    dc2 = TaborWaveform(channel=2, values=[v for v in [0.5] for _ in range(1024)])

    wav1 = TaborWaveform(
        channel=1,
        values=TaborFunctionGeneratorSegment(
            freq=freq,
            last_value=last_value,
            amplitude=1,
            function=TaborFunctionGeneratorSegmentFType.square,
        ),
    )
    wav2 = TaborWaveform(
        channel=2,
        values=TaborFunctionGeneratorSegment(
            freq=freq,
            last_value=last_value,
            phase=math.pi * 1,
            amplitude=1,
            function=TaborFunctionGeneratorSegmentFType.square,
        ),
    )

    client.waveform_out(dc1, wav2)

    client.disconnect()
