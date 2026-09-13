"""
V-CAD Server: Production Starlette + Uvicorn Engine
Supports uploading blueprints (JPG, JPEG, PNG, SVG, JSON),
running computer vision & 3D extrusion, assigning 3D ULPINs,
and streaming 3D OBJ / GeoJSON exports.
"""

from __future__ import annotations
import base64
import json
import time
from pathlib import Path
from typing import Dict, Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
import uvicorn

from blueprint_vision import parse_any_blueprint, detect_floor_configuration
from cad_generator import build_3d_cadastre_from_analysis, export_to_obj, export_to_geojson
from ulpin_engine import (
    DEFAULT_PARENT_ULPIN, normalize_2d_ulpin,
    CadastreRegistry, CadastreUnit, make_official_3d_ulpin, make_numeric_3d_ulpin
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"
SAMPLE_DIR = BASE_DIR / "sample_blueprints"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# State cache
CURRENT_PAYLOAD = None

def get_default_payload():
    global CURRENT_PAYLOAD
    if CURRENT_PAYLOAD is None:
        # Check for user uploaded blueprints first
        upload_stairs = UPLOAD_DIR / "Screenshot 2026-09-08 074503.png"
        sample_stairs = SAMPLE_DIR / "Screenshot 2026-09-08 074503.png"
        user_cottage = SAMPLE_DIR / "user_test_blueprint.png"

        target_file = None
        if upload_stairs.exists():
            target_file = upload_stairs
        elif sample_stairs.exists():
            target_file = sample_stairs
        elif user_cottage.exists():
            target_file = user_cottage
        else:
            target_file = SAMPLE_DIR / "sample_floor_2unit.jpg"

        if target_file and target_file.exists():
            analysis = parse_any_blueprint(str(target_file), floors_count=1)
            _, CURRENT_PAYLOAD = build_3d_cadastre_from_analysis(analysis, DEFAULT_PARENT_ULPIN)
            CURRENT_PAYLOAD["source_filename"] = target_file.name
        else:
            from ulpin_engine import build_default_sih_cadastre
            reg = build_default_sih_cadastre(DEFAULT_PARENT_ULPIN)
            CURRENT_PAYLOAD = {"cadastre": reg.to_dict(), "geometries": [], "parent_2d_ulpin": DEFAULT_PARENT_ULPIN, "floors_count": 1, "source_filename": "SIH-Default-Plan"}
    return CURRENT_PAYLOAD

async def get_cadastre(request):
    payload = get_default_payload()
    return JSONResponse(payload)

async def set_parent_ulpin(request):
    global CURRENT_PAYLOAD
    data = await request.json()
    new_parent = normalize_2d_ulpin(data.get("parent_2d_ulpin", DEFAULT_PARENT_ULPIN))

    payload = get_default_payload()
    current_floors = payload.get("floors_count", 1)

    upload_stairs = UPLOAD_DIR / "Screenshot 2026-09-08 074503.png"
    user_cottage = SAMPLE_DIR / "user_test_blueprint.png"
    target_file = upload_stairs if upload_stairs.exists() else user_cottage

    analysis = parse_any_blueprint(str(target_file), floors_count=current_floors)
    _, CURRENT_PAYLOAD = build_3d_cadastre_from_analysis(analysis, new_parent)
    return JSONResponse(CURRENT_PAYLOAD)

async def upload_blueprint(request):
    global CURRENT_PAYLOAD
    data = await request.json()
    parent_ulpin = normalize_2d_ulpin(data.get("parent_2d_ulpin", DEFAULT_PARENT_ULPIN))
    filename = data.get("filename", "blueprint.jpg")
    file_content_b64 = data.get("content_base64", "")
    floor_notes = data.get("floor_notes", "")
    elevation_b64 = data.get("vertical_elevation_base64", "")

    # Determine requested floor count (strictly default to 1 floor for 2D blueprint uploads)
    raw_floors = int(data.get("floors_count", 1))
    floors_count = detect_floor_configuration(floor_notes, default_floors=raw_floors)

    # If optional vertical elevation blueprint was uploaded, save it
    if elevation_b64:
        try:
            elev_bytes = base64.b64decode(elevation_b64.split(",")[-1])
            elev_path = UPLOAD_DIR / f"elevation_{filename}"
            with open(elev_path, "wb") as f:
                f.write(elev_bytes)
        except Exception as e:
            print(f"[WARN] Failed to save elevation blueprint: {e}")

    if data.get("is_cadastre_json") and "objects" in data:
        reg = CadastreRegistry(parent_ulpin)
        for obj in data["objects"]:
            unit = CadastreUnit(
                id=obj["id"],
                name=obj["name"],
                type=obj["type"],
                floor=obj["floor"],
                space_class=obj["space_class"],
                rights=obj["rights"],
                unit_id=obj["unit_id"],
                ulpin_3d=obj.get("ulpin_3d", make_official_3d_ulpin(parent_ulpin, obj["floor"], obj["space_class"], obj["rights"], obj["unit_id"])),
                ulpin_numeric=make_numeric_3d_ulpin(parent_ulpin, 1, 1, 1),
                owner=obj.get("owner", "Owner"),
                description=obj.get("description", ""),
                parent_2d_ulpin=parent_ulpin
            )
            reg.add_unit(unit)
        for r in data.get("relationships", []):
            reg.add_relationship(r["source_id"], r["target_id"], r["type"])
        rooms_list = []
        for idx_u, u in enumerate(reg.units.values(), start=1):
            if u.type in ("ROOM", "FLAT"):
                bb = u.bbox or {"x_min": -3.0, "x_max": 3.0, "y_min": -2.0, "y_max": 2.0}
                w = round(bb.get("x_max", 3.0) - bb.get("x_min", -3.0), 2)
                l = round(bb.get("y_max", 2.0) - bb.get("y_min", -2.0), 2)
                cx = round((bb.get("x_min", -3.0) + bb.get("x_max", 3.0)) / 2.0, 2)
                cy = round((bb.get("y_min", -2.0) + bb.get("y_max", 2.0)) / 2.0, 2)
                rooms_list.append({
                    "id": u.id, "room_index": idx_u, "name": u.name, "type": "ROOM", "unit_tag": u.unit_id,
                    "space_class": u.space_class, "rights": u.rights, "owner": u.owner,
                    "dimensions_m": {"width": max(1.0, w), "length": max(1.0, l)},
                    "area_sqm": u.carpet_area_sqm or round(max(1.0, w) * max(1.0, l), 2),
                    "area_sqft": u.carpet_area_sqft or round(max(1.0, w) * max(1.0, l) * 10.76, 1),
                    "center_m": {"x": cx, "y": cy}, "bbox_m": bb
                })
        analysis = {
            "format": "JSON_CADASTRE",
            "building_dimensions_m": {"width": 12.0, "length": 8.0, "height": 2.80 * floors_count},
            "floors_count": floors_count,
            "rooms_detected": len(rooms_list),
            "rooms": rooms_list
        }
        _, CURRENT_PAYLOAD = build_3d_cadastre_from_analysis(analysis, parent_ulpin)
        CURRENT_PAYLOAD["cadastre"] = reg.to_dict()
    elif file_content_b64:
        raw_bytes = base64.b64decode(file_content_b64.split(",")[-1])
        timestamp = int(time.time() * 1000)
        safe_name = f"{timestamp}_{filename}"
        save_path = UPLOAD_DIR / safe_name
        with open(save_path, "wb") as f:
            f.write(raw_bytes)
        analysis = parse_any_blueprint(str(save_path), floors_count=floors_count, floor_notes=floor_notes)
        _, CURRENT_PAYLOAD = build_3d_cadastre_from_analysis(analysis, parent_ulpin)
        CURRENT_PAYLOAD["source_filename"] = filename
    else:
        return JSONResponse({"error": "No file content provided for blueprint processing"}, status_code=400)

    return JSONResponse(CURRENT_PAYLOAD)

async def export_obj(request):
    payload = get_default_payload()
    export_path = UPLOAD_DIR / f"vcad_{payload['parent_2d_ulpin']}.obj"
    export_to_obj(payload, str(export_path))
    with open(export_path, "rb") as f:
        content = f.read()
    return Response(
        content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=vcad_3d_model_{payload['parent_2d_ulpin']}.obj"}
    )

async def export_geojson(request):
    payload = get_default_payload()
    export_path = UPLOAD_DIR / f"vcad_{payload['parent_2d_ulpin']}.geojson"
    export_to_geojson(payload["cadastre"], str(export_path))
    with open(export_path, "rb") as f:
        content = f.read()
    return Response(
        content,
        media_type="application/geo+json",
        headers={"Content-Disposition": f"attachment; filename=vcad_cadastre_{payload['parent_2d_ulpin']}.geojson"}
    )

async def analyze_blueprint_endpoint(request):
    data = await request.json()
    filename = data.get("filename", "blueprint.jpg")
    file_content_b64 = data.get("content_base64", "")
    floor_notes = data.get("floor_notes", "")
    raw_floors = int(data.get("floors_count", 1))
    floors_count = detect_floor_configuration(floor_notes, default_floors=raw_floors)

    if file_content_b64:
        raw_bytes = base64.b64decode(file_content_b64.split(",")[-1])
        save_path = UPLOAD_DIR / f"temp_{filename}"
        with open(save_path, "wb") as f:
            f.write(raw_bytes)
        analysis = parse_any_blueprint(str(save_path), floors_count=floors_count, floor_notes=floor_notes)
        return JSONResponse({"success": True, "analysis": analysis})
    return JSONResponse({"success": False, "error": "No file content provided"}, status_code=400)

routes = [
    Route("/api/cadastre", get_cadastre, methods=["GET"]),
    Route("/api/set-parent-ulpin", set_parent_ulpin, methods=["POST"]),
    Route("/api/analyze-blueprint", analyze_blueprint_endpoint, methods=["POST"]),
    Route("/api/upload", upload_blueprint, methods=["POST"]),
    Route("/api/export/obj", export_obj, methods=["GET"]),
    Route("/api/export/geojson", export_geojson, methods=["GET"]),
    Mount("/sample_blueprints", StaticFiles(directory=str(SAMPLE_DIR))),
    Mount("/", StaticFiles(directory=str(STATIC_DIR), html=True)),
]

from starlette.middleware.base import BaseHTTPMiddleware

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
    Middleware(NoCacheMiddleware),
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print(f"[OK] Starting V-CAD Starlette + Uvicorn server at http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
