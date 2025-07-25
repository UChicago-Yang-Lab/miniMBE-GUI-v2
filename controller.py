#!/usr/bin/env python3
"""Simple controller for SMCD14 manipulator.

This module provides a small helper class that connects to a Modbus
TCP server and reads the actual position register from three axes of
an SMCD14 controller.  Each axis uses a separate Modbus slave ID.
"""

import struct
from typing import Tuple

from pymodbus.client.tcp import ModbusTcpClient

REG_ACTPOS = 18  # two registers (float)


class ManipulatorController:
    """Handle Modbus communication with the manipulator."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5020):
        self.client = ModbusTcpClient(host, port=port)
        self.client.connect()

    def close(self) -> None:
        self.client.close()

    def _read_axis(self, slave_id: int) -> float:
        rr = self.client.read_holding_registers(REG_ACTPOS, count=2, slave=slave_id)
        if rr.isError():
            raise IOError(f"Modbus error reading axis {slave_id}")
        raw = struct.pack(">HH", rr.registers[0], rr.registers[1])
        return struct.unpack(">f", raw)[0]

    def read_all_axes(self) -> Tuple[float, float, float]:
        """Return the positions (x, y, z)."""
        x = self._read_axis(1)
        y = self._read_axis(2)
        z = self._read_axis(3)
        return x, y, z
