import pyvisa as visa
import socket

# -------------------------------------------------
# Name:     proteus_visa_raw_socket_example.py
#
# Description:
#   This script shows and example of how to connect to
#   the LAN interface provided by the Proteus Benchtop.
#
#   The script uses pyvisa. Install is it by:
#
#   $ pip install pyvisa
#
#   The script has been tested using:
#       - Windows 10 and Python3
#       - Ubuntu linux and Python3
#
# Author:   Tabor Electronics @ 2022
#
# -------------------------------------------------


def send_scpi_cmd(dev, cmd):
    try:
        resourceManager = visa.ResourceManager()
        session = resourceManager.open_resource(dev)

        # Need to define the termination string
        session.write_termination = "\n"
        session.read_termination = "\n"

        session.write(cmd)
        session.close()

    except Exception as e:
        print("[!] Exception: " + str(e))


def send_scpi_query(dev, query):
    try:
        resourceManager = visa.ResourceManager()
        session = resourceManager.open_resource(dev)

        # Need to define the termination string
        session.write_termination = "\n"
        session.read_termination = "\n"

        # print('IDN: ' + str(session.query(query)))
        response = str(session.query(query))
        session.close()
        return response

    except Exception as e:
        print("[!] Exception: " + str(e))


# --- MAIN ---

# Set the IP Address and port
proteus_device = "TCPIP0::192.168.0.74::5025::SOCKET"


# Query device ID
print("IDN: " + send_scpi_query(proteus_device, "*IDN?"))
