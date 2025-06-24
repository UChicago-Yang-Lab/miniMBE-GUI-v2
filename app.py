#!/usr/bin/env python3
"""SMCD14 manipulator controller for real hardware.

This module provides a small wrapper around ``pymodbus`` for talking to the
SMCD14 stepper controller over Modbus TCP.  It implements a handful of
convenience methods for absolute and relative moves and exposes helper
functions used to enforce basic motion limits.  Register addresses and
behaviour were taken from the SMCD14 manual.
"""

import struct
import time
from threading import Lock
from typing import Sequence

from pymodbus.client.tcp import ModbusTcpClient

# ---------------------------------------------------------------------------
# Default connection parameters (point this at your physical controller)
# ---------------------------------------------------------------------------
DEFAULT_HOST     = "169.254.151.255"   # SMCD14’s IP
DEFAULT_PORT     = 502               # standard Modbus-TCP port
DEFAULT_TIMEOUT  = 10                # seconds
DEFAULT_SLAVE_ID = 1                 # your device’s Modbus unit ID

# ---------------------------------------------------------------------------
# Register map (word-based)
# ---------------------------------------------------------------------------
MOVE_TYPE_ADDR    = 0
TARGET_POS_ADDR   = 2   # two registers → float
TARGET_VEL_ADDR   = 8   # two registers → float
MOTOR_ON_ADDR     = 14
START_REQ_ADDR    = 15
STOP_REQ_ADDR     = 16
STATUS_ADDR       = 17
ACTUAL_POS_ADDR   = 18  # two registers → float
ERROR_CODE_ADDR   = 20
CLEAR_REQ_ADDR    = 22
BACKLASH_ADDR     = 72  # two registers → float

# ---------------------------------------------------------------------------
# Physical limits
# ---------------------------------------------------------------------------
MIN_AXIS_VELOCITY = 1e-4   # mm/s
MAX_AXIS_VELOCITY = 1.0    # mm/s
VELOCITY_THRESHOLD = 5e-5

# ---------------------------------------------------------------------------
# Helpers: float ↔ register conversions
# ---------------------------------------------------------------------------
def _float_to_regs(value: float) -> list[int]:
    packed = struct.pack('>f', value)
    hi, lo = struct.unpack('>HH', packed)
    # note: SMCD14 wants little-endian pair [lo, hi]
    return [lo, hi]

def _regs_to_float(regs: Sequence[int]) -> float:
    if len(regs) != 2:
        raise ValueError("Expected exactly two registers for a float")
    packed = struct.pack('>HH', regs[1], regs[0])
    return struct.unpack('>f', packed)[0]

# ---------------------------------------------------------------------------
# Velocity validation / component splitting (unchanged)
# ---------------------------------------------------------------------------
def validate_velocity(velocity: float) -> None:
    if velocity < MIN_AXIS_VELOCITY:
        raise ValueError(f"Velocity too slow (min {MIN_AXIS_VELOCITY} mm/s)")
    theoretical_max = (3 ** 0.5) * MAX_AXIS_VELOCITY
    if velocity > theoretical_max:
        raise ValueError(
            f"Velocity {velocity} mm/s exceeds diagonal limit {theoretical_max:.3f} mm/s"
        )

def _adjust_axis_velocity(v: float) -> float:
    if abs(v) < VELOCITY_THRESHOLD:
        return 0.0
    if abs(v) < MIN_AXIS_VELOCITY:
        return (MIN_AXIS_VELOCITY if v >= 0 else -MIN_AXIS_VELOCITY)
    if abs(v) > MAX_AXIS_VELOCITY:
        return (MAX_AXIS_VELOCITY if v >= 0 else -MAX_AXIS_VELOCITY)
    return v

def calculate_velocity_components(
    start_pos: Sequence[float],
    end_pos: Sequence[float],
    total_velocity: float,
) -> tuple[float, float, float]:
    validate_velocity(total_velocity)
    dx, dy, dz = (e - s for s, e in zip(start_pos, end_pos))
    distance = (dx*dx + dy*dy + dz*dz) ** 0.5
    if distance == 0:
        return (0.0, 0.0, 0.0)
    ux, uy, uz = dx/distance, dy/distance, dz/distance
    vx = _adjust_axis_velocity(ux * total_velocity)
    vy = _adjust_axis_velocity(uy * total_velocity)
    vz = _adjust_axis_velocity(uz * total_velocity)
    actual = (vx*vx + vy*vy + vz*vz) ** 0.5
    if 0 < actual < total_velocity:
        scale = total_velocity / actual
        vx = _adjust_axis_velocity(vx * scale)
        vy = _adjust_axis_velocity(vy * scale)
        vz = _adjust_axis_velocity(vz * scale)
    return vx, vy, vz

# ---------------------------------------------------------------------------
# Controller class
# ---------------------------------------------------------------------------
class SMCD14Controller:
    def __init__(
        self,
        host: str     = DEFAULT_HOST,
        port: int     = DEFAULT_PORT,
        timeout: int  = DEFAULT_TIMEOUT,
        slave_id: int = DEFAULT_SLAVE_ID
    ):
        self.host     = host
        self.port     = port
        self.timeout  = timeout
        self.slave_id = slave_id

        self._client: ModbusTcpClient | None = None
        self._lock   = Lock()

    def connect(self) -> bool:
        """Establish Modbus-TCP connection to the SMCD14."""
        with self._lock:
            self._client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            return self._client.connect()

    def disconnect(self) -> None:
        """Close the Modbus connection."""
        with self._lock:
            if self._client:
                self._client.close()
            self._client = None

    def _check(self) -> None:
        if not self._client:
            raise RuntimeError("Controller not connected")

    def _write_registers(self, addr: int, regs: Sequence[int]) -> None:
        self._check()
        with self._lock:
            res = self._client.write_registers(addr, list(regs), slave=self.slave_id)
        if res.isError():
            raise RuntimeError(f"Write to address {addr} failed")

    def _write_register(self, addr: int, val: int) -> None:
        self._check()
        with self._lock:
            res = self._client.write_register(addr, val, slave=self.slave_id)
        if res.isError():
            raise RuntimeError(f"Write to address {addr} failed")

    def _read_registers(self, addr: int, count: int) -> list[int]:
        self._check()
        with self._lock:
            res = self._client.read_holding_registers(addr, count=count, slave=self.slave_id)
        if res.isError():
            raise RuntimeError(f"Read from address {addr} failed")
        return res.registers

    # -- High-level commands ---------------------------------------------

    def motor_on(self) -> None:
        self._write_register(MOTOR_ON_ADDR, 1)

    def motor_off(self) -> None:
        self._write_register(MOTOR_ON_ADDR, 0)

    def move_absolute(self, position: float, velocity: float) -> None:
        self._write_register(MOVE_TYPE_ADDR, 1)
        self._write_registers(TARGET_POS_ADDR, _float_to_regs(position))
        self._write_registers(TARGET_VEL_ADDR, _float_to_regs(velocity))
        self._write_register(START_REQ_ADDR, 1)

    def move_relative(self, distance: float, velocity: float) -> None:
        self._write_register(MOVE_TYPE_ADDR, 2)
        self._write_registers(TARGET_POS_ADDR, _float_to_regs(distance))
        self._write_registers(TARGET_VEL_ADDR, _float_to_regs(velocity))
        self._write_register(START_REQ_ADDR, 1)

    def emergency_stop(self) -> None:
        self._write_register(STOP_REQ_ADDR, 1)

    def clear_error(self) -> None:
        self._write_register(CLEAR_REQ_ADDR, 1)
        time.sleep(0.1)
        self._write_register(CLEAR_REQ_ADDR, 0)

    def wait_until_in_position(self, timeout: float = 15.0) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if self.in_position():
                return True
            time.sleep(0.5)
        return False

    def read_position(self) -> float:
        regs = self._read_registers(ACTUAL_POS_ADDR, 2)
        return _regs_to_float(regs)

    def read_error_code(self) -> int:
        return self._read_registers(ERROR_CODE_ADDR, 1)[0]

    def set_backlash(self, value: float) -> None:
        self._write_registers(BACKLASH_ADDR, _float_to_regs(value))

    def get_backlash(self) -> float:
        regs = self._read_registers(BACKLASH_ADDR, 2)
        return _regs_to_float(regs)

    def in_position(self) -> bool:
        status = self._read_registers(STATUS_ADDR, 1)[0]
        return bool(status & (1 << 4))


# ---------------------------------------------------------------------------
# Quick test when run stand‐alone
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ctrl = SMCD14Controller()
    print(f"Connecting to {ctrl.host}:{ctrl.port} ...", end="")
    if ctrl.connect():
        print(" OK")
        print("Current position:", ctrl.read_position())
        ctrl.disconnect()
    else:
        print(" FAILED")
