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
import struct
import threading
import time

# ------- Register map (word addresses) ------- #
REG_MOVETYPE      = 0
REG_TARGET        = 2  # 2 registers (float)
REG_ACC           = 4  # 2 registers (float)
REG_VELOCITY      = 8  # 2 registers (float)
REG_CALIBVEL      = 10 # 2 registers (float)
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
    REG_MOVETYPE:     0,
    REG_TARGET:       0,
    REG_TARGET + 1:   0,
    REG_ACC:          0,
    REG_ACC + 1:      0,
    REG_VELOCITY:     0,
    REG_VELOCITY + 1: 0,
    REG_CALIBVEL:     0,
    REG_CALIBVEL + 1: 0,
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


def _regs_to_float(values) -> float:
    """Convert two 16-bit register values to a float."""
    hi, lo = values
    raw = struct.pack(">HH", hi, lo)
    return struct.unpack(">f", raw)[0]


def _float_to_regs(value: float) -> list[int]:
    """Convert a float to two 16-bit register values."""
    hi, lo = struct.unpack(">HH", struct.pack(">f", value))
    return [hi, lo]


def _motion_task(context: ModbusServerContext, period: float = 0.1) -> None:
    """Background task that simulates axis motion."""
    slave = 0x00
    prev_start = context[slave].getValues(3, REG_START_REQ, 1)[0]
    moving = False
    while True:
        start = context[slave].getValues(3, REG_START_REQ, 1)[0]
        stop = context[slave].getValues(3, REG_STOP_REQ, 1)[0]

        if moving and stop:
            moving = False
        if start and not prev_start:
            moving = True

        if moving:
            target = _regs_to_float(
                context[slave].getValues(3, REG_TARGET, 2)
            )
            velocity = _regs_to_float(
                context[slave].getValues(3, REG_VELOCITY, 2)
            )
            pos = _regs_to_float(
                context[slave].getValues(3, REG_ACTPOS, 2)
            )
            step = velocity * period
            diff = target - pos
            if abs(diff) <= step:
                pos = target
                moving = False
            else:
                pos += step if diff > 0 else -step
            context[slave].setValues(3, REG_ACTPOS, _float_to_regs(pos))

        prev_start = start
        time.sleep(period)


def run_tcp(port: int) -> None:
    """Start a Modbus TCP server on the given port."""
    context = build_context()
    identity = build_identity()
    threading.Thread(target=_motion_task, args=(context,), daemon=True).start()
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
