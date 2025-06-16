#!/usr/bin/env python3
"""SMCD14 Modbus RTU emulator.

This module exposes a tiny Modbus RTU server that mimics a subset of the
registers of the SMCD14 stepper motor controller.  Only holding registers are
implemented as most client interactions rely on them.  The emulator is useful
for testing software without the actual hardware attached.
"""

from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server.sync import StartSerialServer
from pymodbus.transaction import ModbusRtuFramer
import argparse
import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Register addresses from the manual (word addresses)
REG_MOTOR_ON = 14
REG_START_REQ = 15
REG_STOP_REQ = 16
REG_STATUS = 17
REG_ACTPOS = 18  # 2 registers (float)
REG_ERROR_CODE = 20
REG_CLEAR_REQ = 22
REG_RUN_FLAG = 41
REG_INPOS_FLAG = 42
REG_ENABLED_FLAG = 43
REG_FLS_FLAG = 45
REG_BLS_FLAG = 46
REG_DOG_FLAG = 47
REG_HOMED_FLAG = 50
REG_HOME_TYPE = 70
REG_BACKLASH = 72  # 2 registers (float)
REG_GAIN = 74       # 2 registers (float)
REG_OFFSET = 76     # 2 registers (float)
REG_MEMORY_CTRL = 499

# Default register values for the emulator. Only a subset of the
# controller's map is represented here.
DEFAULT_REG_VALUES = {
    REG_MOTOR_ON: 0,
    REG_START_REQ: 0,
    REG_STOP_REQ: 0,
    REG_STATUS: 0,
    REG_ACTPOS: 0,
    REG_ACTPOS + 1: 0,
    REG_ERROR_CODE: 0,
    REG_CLEAR_REQ: 0,
    REG_RUN_FLAG: 0,
    REG_INPOS_FLAG: 0,
    REG_ENABLED_FLAG: 0,
    REG_FLS_FLAG: 0,
    REG_BLS_FLAG: 0,
    REG_DOG_FLAG: 0,
    REG_HOMED_FLAG: 0,
    REG_HOME_TYPE: 0,
    REG_BACKLASH: 0,
    REG_BACKLASH + 1: 0,
    REG_GAIN: 0,
    REG_GAIN + 1: 0,
    REG_OFFSET: 0,
    REG_OFFSET + 1: 0,
    REG_MEMORY_CTRL: 0,
}


def build_context():
    """Return a ModbusServerContext populated with default values."""
    hr_values = [0] * 1000
    for addr, val in DEFAULT_REG_VALUES.items():
        hr_values[addr] = val
    store = ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, hr_values))
    return ModbusServerContext(slaves=store, single=True)


context = build_context()

# Identification information
identity = ModbusDeviceIdentification()
identity.VendorName = "SMCD14 Emulator"
identity.ProductCode = "EMUL"
identity.VendorUrl = "https://example.com"
identity.ProductName = "SMCD14 Modbus Emulator"
identity.ModelName = "SMCD14"
identity.MajorMinorRevision = "1.0"


def run_server(port: str, baudrate: int) -> None:
    """Run the Modbus RTU server on the given serial port."""
    StartSerialServer(
        context,
        identity=identity,
        port=port,
        framer=ModbusRtuFramer,
        stopbits=1,
        bytesize=8,
        parity="N",
        baudrate=baudrate,
    )


def parse_args() -> argparse.Namespace:
    """Return command line arguments."""
    parser = argparse.ArgumentParser(description="SMCD14 Modbus RTU emulator")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port")
    parser.add_argument("--baud", type=int, default=38400, help="Baud rate")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_server(args.port, args.baud)
