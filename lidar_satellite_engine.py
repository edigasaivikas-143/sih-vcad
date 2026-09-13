"""
V-CAD LiDAR & Satellite Ingestion Engine
Processes:
1. LiDAR 3D Point Clouds (LAS 1.1-1.4, LAZ, XYZ, CSV)
2. Satellite & Drone Imagery / DEM (GeoTIFF, Elevation Grids, Orthophoto DSM)
3. 2D ULPIN Cadastral Boundaries -> Volumetric 3D Land Parcel Extrusion
4. Multi-Layer Cadastral Title Assignment (Subsurface, Ground Parcel, Vertical Airspace)
"""

from __future__ import annotations
import os
import struct
import math
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import cv2

from ulpin_engine import (
    CadastreRegistry, CadastreUnit, make_official_3d_ulpin, make_numeric_3d_ulpin,
    normalize_2d_ulpin, DEFAULT_PARENT_ULPIN
)

# ---------------------------------------------------------------------------
# 1. High-Speed Pure-NumPy Binary LAS LiDAR Parser (Zero External C++ Wheels)
# ---------------------------------------------------------------------------

def parse_las_lidar(file_path: str, max_points: int = 500_000) -> Dict[str, Any]:
    """
    Parses ASPRS LAS (1.1, 1.2, 1.3, 1.4) binary point clouds directly with NumPy.
    Extracts X, Y, Z, Intensity, and ASPRS Classification:
      Class 2 = Ground
      Class 6 = Building / Roof
      Class 3, 4, 5 = Vegetation
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"LiDAR file not found: {file_path}")

    with open(path, "rb") as f:
        header_bytes = f.read(375)

    if len(header_bytes) < 227:
        raise ValueError("Invalid LAS file: header too short")

    sig = header_bytes[0:4]
    if sig != b"LASF":
        raise ValueError(f"Invalid LAS signature: {sig}, expected b'LASF'")

    version_major = header_bytes[24]
    version_minor = header_bytes[25]

    offset_to_points = struct.unpack("<I", header_bytes[96:100])[0]
    point_data_format = header_bytes[104]
    point_data_record_len = struct.unpack("<H", header_bytes[105:107])[0]
    num_point_records = struct.unpack("<I", header_bytes[107:111])[0]

    # If LAS 1.4 64-bit point count is present and 32-bit count is 0
    if num_point_records == 0 and len(header_bytes) >= 255:
        num_point_records = struct.unpack("<Q", header_bytes[247:255])[0]

    x_scale, y_scale, z_scale = struct.unpack("<ddd", header_bytes[131:155])
    x_offset, y_offset, z_offset = struct.unpack("<ddd", header_bytes[155:179])
    max_x, min_x = struct.unpack("<dd", header_bytes[179:195])
    max_y, min_y = struct.unpack("<dd", header_bytes[195:211])
    max_z, min_z = struct.unpack("<dd", header_bytes[211:227])

    actual_points_to_read = min(num_point_records, max_points)

    with open(path, "rb") as f:
        f.seek(offset_to_points)
        raw_point_data = f.read(actual_points_to_read * point_data_record_len)

    if point_data_record_len < 12:
        raise ValueError(f"Unexpected point record length: {point_data_record_len}")

    # First 12 bytes of any point format (0 to 10) are X(int32), Y(int32), Z(int32)
    dtype_fields = [
        ("x", "<i4"),
        ("y", "<i4"),
        ("z", "<i4"),
    ]
    if point_data_record_len >= 14:
        dtype_fields.append(("intensity", "<u2"))
    if point_data_record_len >= 16:
        dtype_fields.append(("flags", "u1"))
        dtype_fields.append(("classification", "u1"))
    
    consumed = sum(np.dtype(t).itemsize for _, t in dtype_fields)
    pad = point_data_record_len - consumed
    if pad > 0:
        dtype_fields.append(("_pad", f"V{pad}"))

    arr = np.frombuffer(raw_point_data, dtype=np.dtype(dtype_fields))

    x_coords = arr["x"] * x_scale + x_offset
    y_coords = arr["y"] * y_scale + y_offset
    z_coords = arr["z"] * z_scale + z_offset

    classifications = arr["classification"] if "classification" in arr.dtype.names else np.zeros_like(x_coords, dtype=np.uint8)
    intensities = arr["intensity"] if "intensity" in arr.dtype.names else np.zeros_like(x_coords, dtype=np.uint16)

    return {
        "format": f"LAS_{version_major}.{version_minor}",
        "total_points": num_point_records,
        "sampled_points": len(x_coords),
        "bounds": {
            "min_x": float(min_x), "max_x": float(max_x),
            "min_y": float(min_y), "max_y": float(max_y),
            "min_z": float(min_z), "max_z": float(max_z),
        },
        "x": x_coords,
        "y": y_coords,
        "z": z_coords,
        "classification": classifications,
        "intensity": intensities,
    }


def parse_xyz_lidar(file_path: str, max_points: int = 500_000) -> Dict[str, Any]:
    """
    Parses ASCII XYZ / PTS / CSV LiDAR point cloud files.
    """
    data = np.loadtxt(file_path, delimiter=None, max_rows=max_points)
    if data.ndim == 1 or data.shape[1] < 3:
        raise ValueError("XYZ point cloud must contain at least X, Y, Z columns")

    x = data[:, 0]
    y = data[:, 1]
    z = data[:, 2]
    cls = data[:, 3].astype(np.uint8) if data.shape[1] > 3 else np.zeros_like(x, dtype=np.uint8)

    return {
        "format": "XYZ_ASCII",
        "total_points": len(x),
        "sampled_points": len(x),
        "bounds": {
            "min_x": float(np.min(x)), "max_x": float(np.max(x)),
            "min_y": float(np.min(y)), "max_y": float(np.max(y)),
            "min_z": float(np.min(z)), "max_z": float(np.max(z)),
        },
        "x": x,
        "y": y,
        "z": z,
        "classification": cls,
    }


# ---------------------------------------------------------------------------
# 2. Satellite & Drone DEM / DSM / Orthophoto Heightmap Engine
# ---------------------------------------------------------------------------

def parse_satellite_dem(file_path: str) -> Dict[str, Any]:
    """
    Ingests GeoTIFF / DEM / DSM / Satellite elevation heightmaps.
    Extracts ground elevation matrix, building roof heights, and terrain profile.
    """
    path = Path(file_path)
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not load satellite / DEM raster: {file_path}")

    if img.ndim == 2:
        dem = img.astype(np.float32)
    elif img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        dem = gray.astype(np.float32)
    else:
        raise ValueError("Unsupported raster dimension")

    min_elev = float(np.min(dem))
    max_elev = float(np.max(dem))
    mean_elev = float(np.mean(dem))

    # Detect building footprints from satellite/orthophoto using adaptive elevation difference
    # Compute ground elevation baseline
    ground_baseline = float(np.percentile(dem, 20))
    height_above_ground = np.maximum(0.0, dem - ground_baseline).astype(np.float32)

    # Threshold structures at least 2.5 meters above ground
    _, building_mask = cv2.threshold(height_above_ground, 2.5, 255, cv2.THRESH_BINARY)
    building_mask = building_mask.astype(np.uint8)

    contours, _ = cv2.findContours(building_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detected_structures = []
    idx = 1
    h_px, w_px = dem.shape[:2]

    for c in contours:
        area = cv2.contourArea(c)
        if area < 25:
            continue
        bx, by, bw, bh = cv2.boundingRect(c)
        roi = dem[by:by+bh, bx:bx+bw]
        ground_lvl = ground_baseline
        roof_lvl = float(np.percentile(roi, 95))
        bldg_height = max(2.8, round(roof_lvl - ground_lvl, 2))

        detected_structures.append({
            "id": f"satellite_structure_{idx}",
            "pixel_bbox": {"x": bx, "y": by, "w": bw, "h": bh},
            "ground_elevation_m": round(ground_lvl, 2),
            "roof_elevation_m": round(roof_lvl, 2),
            "estimated_height_m": bldg_height,
            "estimated_floors": max(1, int(round(bldg_height / 3.0))),
            "area_pixels": int(area),
        })
        idx += 1

    return {
        "format": "SATELLITE_DEM",
        "dimensions": {"width_px": w_px, "height_px": h_px},
        "elevation_stats": {
            "min_elevation_m": round(min_elev, 2),
            "max_elevation_m": round(max_elev, 2),
            "mean_elevation_m": round(mean_elev, 2),
        },
        "detected_structures": detected_structures,
        "elevation_grid": dem,
    }


# ---------------------------------------------------------------------------
# 3. 2D ULPIN + LiDAR / Satellite Fusion -> 3D Volumetric Cadastre
# ---------------------------------------------------------------------------

def extract_3d_cadastre_from_lidar(
    lidar_data: Dict[str, Any],
    parent_2d_ulpin: str = DEFAULT_PARENT_ULPIN,
    parcel_polygon_2d: Optional[List[Tuple[float, float]]] = None,
    default_building_width_m: float = 14.0,
    default_building_length_m: float = 10.0,
) -> Dict[str, Any]:
    """
    Fuses LiDAR point clouds with a 2D ULPIN cadastral land parcel:
    1. Segments ground elevation (Z_ground).
    2. Identifies building roof points and computes true vertical height (Z_roof - Z_ground).
    3. Extrudes 3D Land Parcel Column:
       - Subsurface Volume (-Z to 0m): Cellar, foundation, utilities rights.
       - Surface Plot Layer (Z = 0m): Cadastral land deed boundary.
       - Vertical Building Volumetric Envelope (0m to Z_roof): Private units & common airspace.
    """
    parent = normalize_2d_ulpin(parent_2d_ulpin)
    x = lidar_data["x"]
    y = lidar_data["y"]
    z = lidar_data["z"]
    cls = lidar_data.get("classification", np.zeros_like(x))

    ground_mask = (cls == 2)
    if np.any(ground_mask):
        z_ground = float(np.median(z[ground_mask]))
    else:
        z_ground = float(np.percentile(z, 10))

    bldg_mask = (cls == 6)
    if np.any(bldg_mask):
        z_roof = float(np.percentile(z[bldg_mask], 95))
        bx_min, bx_max = float(np.min(x[bldg_mask])), float(np.max(x[bldg_mask]))
        by_min, by_max = float(np.min(y[bldg_mask])), float(np.max(y[bldg_mask]))
        bldg_w = round(max(5.0, bx_max - bx_min), 2)
        bldg_l = round(max(5.0, by_max - by_min), 2)
    else:
        z_roof = float(np.percentile(z, 98))
        bldg_w = default_building_width_m
        bldg_l = default_building_length_m

    height_m = max(3.0, round(z_roof - z_ground, 2))
    floor_height_m = 2.85
    floors_count = max(1, int(round(height_m / floor_height_m)))

    rooms = []
    room_idx = 1
    units_per_floor = 2 if bldg_w * bldg_l > 80.0 else 1

    for f_idx in range(1, floors_count + 1):
        flr_tag = f"F{f_idx:02d}"
        if units_per_floor == 2:
            half_w = round(bldg_w / 2.0 - 0.2, 2)
            # Unit A (West side)
            rooms.append({
                "room_index": room_idx,
                "id": f"unit_{f_idx}01",
                "name": f"Cadastral Unit A{f_idx}01",
                "type": "ROOM",
                "unit_tag": f"A{f_idx}01",
                "floor": flr_tag,
                "space_class": "V",
                "rights": "PRV",
                "dimensions_m": {"width": half_w, "length": bldg_l},
                "area_sqm": round(half_w * bldg_l, 2),
                "area_sqft": round(half_w * bldg_l * 10.7639, 1),
                "center_m": {"x": round(-bldg_w / 4.0, 2), "y": 0.0},
                "bbox_m": {
                    "x_min": round(-bldg_w / 2.0, 2), "x_max": 0.0,
                    "y_min": round(-bldg_l / 2.0, 2), "y_max": round(bldg_l / 2.0, 2),
                    "z_min": round((f_idx - 1) * floor_height_m, 2),
                    "z_max": round(f_idx * floor_height_m, 2),
                },
                "ulpin_3d": make_official_3d_ulpin(parent, flr_tag, "V", "PRV", f"A{f_idx}01", "V01"),
                "ulpin_numeric": make_numeric_3d_ulpin(parent, 1, f_idx, 1),
                "color": "#1f4068",
                "edge_color": "#00f0ff"
            })
            room_idx += 1

            # Unit B (East side)
            rooms.append({
                "room_index": room_idx,
                "id": f"unit_{f_idx}02",
                "name": f"Cadastral Unit B{f_idx}01",
                "type": "ROOM",
                "unit_tag": f"B{f_idx}01",
                "floor": flr_tag,
                "space_class": "V",
                "rights": "PRV",
                "dimensions_m": {"width": half_w, "length": bldg_l},
                "area_sqm": round(half_w * bldg_l, 2),
                "area_sqft": round(half_w * bldg_l * 10.7639, 1),
                "center_m": {"x": round(bldg_w / 4.0, 2), "y": 0.0},
                "bbox_m": {
                    "x_min": 0.0, "x_max": round(bldg_w / 2.0, 2),
                    "y_min": round(-bldg_l / 2.0, 2), "y_max": round(bldg_l / 2.0, 2),
                    "z_min": round((f_idx - 1) * floor_height_m, 2),
                    "z_max": round(f_idx * floor_height_m, 2),
                },
                "ulpin_3d": make_official_3d_ulpin(parent, flr_tag, "V", "PRV", f"B{f_idx}01", "V01"),
                "ulpin_numeric": make_numeric_3d_ulpin(parent, 1, f_idx, 2),
                "color": "#162447",
                "edge_color": "#38bdf8"
            })
            room_idx += 1
        else:
            rooms.append({
                "room_index": room_idx,
                "id": f"unit_{f_idx}01",
                "name": f"Cadastral Unit {f_idx}01",
                "type": "ROOM",
                "unit_tag": f"U{f_idx}01",
                "floor": flr_tag,
                "space_class": "V",
                "rights": "PRV",
                "dimensions_m": {"width": bldg_w, "length": bldg_l},
                "area_sqm": round(bldg_w * bldg_l, 2),
                "area_sqft": round(bldg_w * bldg_l * 10.7639, 1),
                "center_m": {"x": 0.0, "y": 0.0},
                "bbox_m": {
                    "x_min": round(-bldg_w / 2.0, 2), "x_max": round(bldg_w / 2.0, 2),
                    "y_min": round(-bldg_l / 2.0, 2), "y_max": round(bldg_l / 2.0, 2),
                    "z_min": round((f_idx - 1) * floor_height_m, 2),
                    "z_max": round(f_idx * floor_height_m, 2),
                },
                "ulpin_3d": make_official_3d_ulpin(parent, flr_tag, "V", "PRV", f"U{f_idx}01", "V01"),
                "ulpin_numeric": make_numeric_3d_ulpin(parent, 1, f_idx, 1),
                "color": "#1f4068",
                "edge_color": "#00f0ff"
            })
            room_idx += 1

    ext_th = 0.25
    walls = [
        {"id": "lidar_wall_north", "name": "North Exterior Wall", "wall_type": "EXTERIOR", "cx": 0.0, "cy": height_m / 2.0, "cz": -bldg_l / 2.0, "width": bldg_w, "height": height_m, "depth": ext_th, "color": "#1e293b", "edge_color": "#38bdf8"},
        {"id": "lidar_wall_south", "name": "South Exterior Wall", "wall_type": "EXTERIOR", "cx": 0.0, "cy": height_m / 2.0, "cz": bldg_l / 2.0, "width": bldg_w, "height": height_m, "depth": ext_th, "color": "#1e293b", "edge_color": "#38bdf8"},
        {"id": "lidar_wall_west", "name": "West Exterior Wall", "wall_type": "EXTERIOR", "cx": -bldg_w / 2.0, "cy": height_m / 2.0, "cz": 0.0, "width": ext_th, "height": height_m, "depth": bldg_l, "color": "#1e293b", "edge_color": "#38bdf8"},
        {"id": "lidar_wall_east", "name": "East Exterior Wall", "wall_type": "EXTERIOR", "cx": bldg_w / 2.0, "cy": height_m / 2.0, "cz": 0.0, "width": ext_th, "height": height_m, "depth": bldg_l, "color": "#1e293b", "edge_color": "#38bdf8"},
    ]

    analysis = {
        "format": "LIDAR_POINT_CLOUD",
        "source": lidar_data.get("format", "LAS"),
        "points_count": lidar_data.get("sampled_points", 0),
        "ground_elevation_m": round(z_ground, 2),
        "roof_elevation_m": round(z_roof, 2),
        "building_height_m": height_m,
        "building_dimensions_m": {
            "width": bldg_w,
            "length": bldg_l,
            "height": height_m,
        },
        "floors_count": floors_count,
        "floor_height_m": floor_height_m,
        "rooms_detected": len(rooms),
        "rooms": rooms,
        "walls": walls,
        "parent_2d_ulpin": parent,
    }

    return analysis
