"""Lightweight DXF loading helper."""
from __future__ import annotations

from typing import Iterable, List
import numpy as np
import ezdxf


def load_dxf(path: str) -> list[np.ndarray]:
    """Load a DXF file and return a list of ``(N, 2)`` arrays."""
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    shapes: list[np.ndarray] = []

    for entity in msp:
        kind = entity.dxftype()
        if kind in {"LWPOLYLINE", "POLYLINE"}:
            try:
                points = entity.get_points("xy")
            except AttributeError:
                points = [(v.dxf.x, v.dxf.y) for v in entity.vertices()]
            arr = np.array([[p[0], p[1]] for p in points], dtype=float)
            shapes.append(arr)
        elif kind == "ARC":
            center = np.array(entity.dxf.center[0:2], dtype=float)
            radius = float(entity.dxf.radius)
            start = np.radians(float(entity.dxf.start_angle))
            end = np.radians(float(entity.dxf.end_angle))
            # ensure correct direction and resolution
            steps = max(int(abs(end - start) / (np.pi / 90)), 2)
            angles = np.linspace(start, end, steps)
            x = center[0] + radius * np.cos(angles)
            y = center[1] + radius * np.sin(angles)
            shapes.append(np.column_stack([x, y]))
        elif kind == "CIRCLE":
            center = np.array(entity.dxf.center[0:2], dtype=float)
            radius = float(entity.dxf.radius)
            angles = np.linspace(0, 2 * np.pi, 90)
            x = center[0] + radius * np.cos(angles)
            y = center[1] + radius * np.sin(angles)
            shapes.append(np.column_stack([x, y]))
    return shapes
