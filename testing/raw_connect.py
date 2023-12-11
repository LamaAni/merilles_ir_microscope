import pyvisa

host = "134.74.27.64"
port = "5025"

rm = pyvisa.ResourceManager("@py")

inst = rm.open_resource(f"TCPIP0::{host}::{port}::SOCKET")
inst.read_termination = "\n"
inst.write_termination = "\n"

print(inst.query("*IDN?"))
