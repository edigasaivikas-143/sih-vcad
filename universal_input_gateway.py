"""
V-CAD Universal Input Gateway
Unified ingestion engine supporting:
1. Architectural Drawings & Blueprints (Hand sketches, phone photos, JPG, PNG, WEBP, TIFF, SVG, DXF, GeoJSON)
2. LiDAR 3D Point Clouds (LAS 1.1-1.4, XYZ, PTS)
3. Satellite Imagery & Terrain DEM/DSM (GeoTIFF, Orthophoto)
4. 2D ULPIN (Bhu-Aadhaar 14-digit) & Cadastral Coordinates
"""

from __future__ import annotations
import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import cv2
import numpy as np

from ulpin_engine import (
    CadastreRegistry, CadastreUnit, make_official_3d_ulpin, make_numeric_3d_ulpin,
    normalize_2d_ulpin, DEFAULT_PARENT_ULPIN
)
from cad_generator import build_3d_cadastre_from_analysis
from lidar_satellite_engine import (
    parse_las_lidar, parse_xyz_lidar, parse_satellite_dem, extract_3d_cadastre_from_lidar
)
from universal_cv import (
    preprocess_blueprint_image, extract_orthogonal_walls_and_rooms
)

def process_universal_input(
    file_path: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    filename: str = "input_blueprint.png",
    parent_2d_ulpin: str = DEFAULT_PARENT_ULPIN,
    floors_count: int = 1,
    floor_notes: str = "",
    target_building_width_m: float = 12.0,
    elevation_file_path: Optional[str] = None,
    cadastral_boundary_geojson: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Master dispatcher: automatically inspects input type and routes to the optimal processor.
    Returns the complete 3D Cadastre Payload with 3D geometries and official 3D ULPINs.
    """
    parent = normalize_2d_ulpin(parent_2d_ulpin)
    ext = Path(filename).suffix.lower()

    # If raw bytes provided without file path, save to temporary buffer
    if file_path is None and file_bytes is not None:
        temp_dir = Path("uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = str(temp_dir / f"gateway_{filename}")
        with open(file_path, "wb") as f:
            f.write(file_bytes)

    if file_path is None:
        raise ValueError("No input file or bytes provided")

    # ---------------------------------------------------------
    # Route 1: LiDAR Point Clouds (.las, .laz, .xyz, .pts)
    # ---------------------------------------------------------
    if ext in (".las", ".laz"):
        lidar_data = parse_las_lidar(file_path)
        analysis = extract_3d_cadastre_from_lidar(lidar_data, parent_2d_ulpin=parent, default_building_width_m=target_building_width_m)
        _, payload = build_3d_cadastre_from_analysis(analysis, parent_ulpin=parent)
        payload["input_modality"] = "LIDAR_POINT_CLOUD"
        payload["source_filename"] = filename
        return payload

    elif ext in (".xyz", ".pts", ".csv") and "point" in filename.lower():
        lidar_data = parse_xyz_lidar(file_path)
        analysis = extract_3d_cadastre_from_lidar(lidar_data, parent_2d_ulpin=parent, default_building_width_m=target_building_width_m)
        _, payload = build_3d_cadastre_from_analysis(analysis, parent_ulpin=parent)
        payload["input_modality"] = "LIDAR_POINT_CLOUD"
        payload["source_filename"] = filename
        return payload

    # ---------------------------------------------------------
    # Route 2: Satellite / Drone Orthophoto & DEM (.tif, .tiff, .dem)
    # ---------------------------------------------------------
    elif ext in (".tif", ".tiff", ".dem") or ("satellite" in filename.lower() and ext in (".jpg", ".png")):
        try:
            sat_data = parse_satellite_dem(file_path)
            structures = sat_data.get("detected_structures", [])
            est_floors = structures[0]["estimated_floors"] if structures else floors_count
            est_h = structures[0]["estimated_height_m"] if structures else 3.0 * floors_count

            img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
            if img is not None:
                if img.dtype != np.uint8:
                    img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
                    img = img_norm.astype(np.uint8)
                if img.ndim == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                _, bin_inv = preprocess_blueprint_image(img)
                analysis = extract_orthogonal_walls_and_rooms(
                    bin_inv, target_building_width_m=target_building_width_m,
                    floor_height_m=2.85, floors_count=max(1, est_floors)
                )
                analysis["satellite_elevation_stats"] = sat_data.get("elevation_stats")
                _, payload = build_3d_cadastre_from_analysis(analysis, parent_ulpin=parent)
                payload["input_modality"] = "SATELLITE_DEM"
                payload["source_filename"] = filename
                return payload
        except Exception as e:
            print(f"[WARN] Satellite DEM processing exception: {e}")
            pass

    # ---------------------------------------------------------
    # Route 3: Vector CAD / GIS (.svg, .json, .geojson)
    # ---------------------------------------------------------
    if ext == ".svg":
        from blueprint_vision import analyze_svg_blueprint
        analysis = analyze_svg_blueprint(file_path, floors_count=floors_count, floor_notes=floor_notes)
        _, payload = build_3d_cadastre_from_analysis(analysis, parent_ulpin=parent)
        payload["input_modality"] = "VECTOR_SVG"
        payload["source_filename"] = filename
        return payload

    elif ext in (".json", ".geojson"):
        from blueprint_vision import analyze_json_blueprint
        analysis = analyze_json_blueprint(file_path, floors_count=floors_count)
        if analysis.get("is_cadastre_registry") and "objects" in analysis.get("data", {}):
            # Parse structured cadastre JSON
            data = analysis["data"]
            reg = CadastreRegistry(parent)
            for obj in data["objects"]:
                unit = CadastreUnit(
                    id=obj["id"],
                    name=obj["name"],
                    type=obj["type"],
                    floor=obj["floor"],
                    space_class=obj["space_class"],
                    rights=obj["rights"],
                    unit_id=obj["unit_id"],
                    ulpin_3d=obj.get("ulpin_3d", make_official_3d_ulpin(parent, obj["floor"], obj["space_class"], obj["rights"], obj["unit_id"])),
                    ulpin_numeric=make_numeric_3d_ulpin(parent, 1, 1, 1),
                    owner=obj.get("owner", "Government Registry"),
                    description=obj.get("description", f"Cadastral unit {obj['unit_id']}"),
                    parent_2d_ulpin=parent
                )
                reg.add_unit(unit)
            _, payload = build_3d_cadastre_from_analysis(analysis, parent_ulpin=parent)
            payload["cadastre"] = reg.to_dict()
        else:
            _, payload = build_3d_cadastre_from_analysis(analysis, parent_ulpin=parent)
        payload["input_modality"] = "VECTOR_CADASTRE_JSON"
        payload["source_filename"] = filename
        return payload

    # ---------------------------------------------------------
    # Route 4: Hand Drawings, Phone Photos, & Raster Blueprints (.png, .jpg, .jpeg, .webp, .bmp)
    # ---------------------------------------------------------
    from blueprint_vision import parse_any_blueprint, detect_floor_configuration
    actual_floors = detect_floor_configuration(floor_notes, default_floors=floors_count)

    try:
        # First attempt: Multi-scale architectural wall & doorway closing
        analysis = parse_any_blueprint(file_path, floors_count=actual_floors, floor_notes=floor_notes)
        if len(analysis.get("rooms", [])) < 2:
            raise ValueError("Insufficient rooms found by standard blueprint parser")
    except Exception:
        # Second attempt: Hand drawings, pencil sketches & mobile camera photo normalization
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Unable to read drawing/image at: {file_path}")
        gray, bin_inv = preprocess_blueprint_image(img)
        analysis = extract_orthogonal_walls_and_rooms(
            bin_inv,
            target_building_width_m=target_building_width_m,
            floor_height_m=2.85,
            floors_count=actual_floors
        )

    analysis["filename"] = filename
    _, payload = build_3d_cadastre_from_analysis(analysis, parent_ulpin=parent)
    payload["input_modality"] = "RASTER_BLUEPRINT_CV"
    payload["source_filename"] = filename
    payload["analysis"] = analysis
    return payload
