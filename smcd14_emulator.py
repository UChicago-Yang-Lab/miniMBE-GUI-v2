#!/usr/bin/env python3
"""SMCD14 Modbus TCP emulator.

This module exposes a tiny Modbus TCP server that mimics a subset of the
registers of the SMCD14 stepper motor controller. Only holding registers are
implemented as most client interactions rely on them. The emulator is useful
for testing software without the actual hardware attached (no USB required).
"""

import argparse
import logging

from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import StartTcpServer

# ------- Register map (word addresses) ------- #
REG_MOTOR_ON      = 14
REG_START_REQ     = 15
REG_STOP_REQ      = 16
REG_STATUS        = 17
REG_ACTPOS        = 18  # 2 registers (float)
REG_ERROR_CODE    = 20
REG_CLEAR_REQ     = 22
REG_RUN_FLAG      = 41
REG_INPOS_FLAG    = 42
REG_ENABLED_FLAG  = 43
REG_FLS_FLAG      = 45
REG_BLS_FLAG      = 46
REG_DOG_FLAG      = 47
REG_HOMED_FLAG    = 50
REG_HOME_TYPE     = 70
REG_BACKLASH      = 72  # 2 registers (float)
REG_GAIN          = 74  # 2 registers (float)
REG_OFFSET        = 76  # 2 registers (float)
REG_MEMORY_CTRL   = 499
REG_POS_BASE      = 200  # start address for saved positions
NUM_POSITIONS     = 5

# Default values for those registers
DEFAULT_REG_VALUES = {
    REG_MOTOR_ON:      0,
    REG_START_REQ:     0,
    REG_STOP_REQ:      0,
    REG_STATUS:        0,
    REG_ACTPOS:        0,
    REG_ACTPOS + 1:    0,
    REG_ERROR_CODE:    0,
    REG_CLEAR_REQ:     0,
    REG_RUN_FLAG:      0,
    REG_INPOS_FLAG:    0,
    REG_ENABLED_FLAG:  0,
    REG_FLS_FLAG:      0,
    REG_BLS_FLAG:      0,
    REG_DOG_FLAG:      0,
    REG_HOMED_FLAG:    0,
    REG_HOME_TYPE:     0,
    REG_BACKLASH:      0,
    REG_BACKLASH + 1:  0,
    REG_GAIN:          0,
    REG_GAIN + 1:      0,
    REG_OFFSET:        0,
    REG_OFFSET + 1:    0,
    REG_MEMORY_CTRL:   0,
}

# initialize memory positions
for i in range(NUM_POSITIONS):
    DEFAULT_REG_VALUES[REG_POS_BASE + 2 * i] = 0
    DEFAULT_REG_VALUES[REG_POS_BASE + 2 * i + 1] = 0


def build_context() -> ModbusServerContext:
    """Build a ModbusServerContext with default register values."""
    hr = [0] * 1000
    for addr, val in DEFAULT_REG_VALUES.items():
        hr[addr] = val
    slave_ctx = ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, hr))
    return ModbusServerContext(slaves=slave_ctx, single=True)


def build_identity() -> ModbusDeviceIdentification:
    """Build Modbus device identity metadata."""
    identity = ModbusDeviceIdentification()
    identity.VendorName = "SMCD14 Emulator"
    identity.ProductCode = "EMUL"
    identity.VendorUrl = "https://example.com"
    identity.ProductName = "SMCD14 Modbus Emulator"
    identity.ModelName = "SMCD14"
    identity.MajorMinorRevision = "1.0"
    return identity


def run_tcp(port: int) -> None:
    """Start a Modbus TCP server on the given port."""
    context = build_context()
    identity = build_identity()
    logging.info(f"Starting Modbus TCP emulator on port {port}")
    # StartTcpServer handles its own serve-loop
    StartTcpServer(
        context,
        identity=identity,
        address=("0.0.0.0", port),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SMCD14 Modbus TCP emulator (no hardware needed)"
    )
    parser.add_argument(
        "--port", type=int, default=5020,
        help="TCP port to listen on (default: 5020)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    run_tcp(args.port)