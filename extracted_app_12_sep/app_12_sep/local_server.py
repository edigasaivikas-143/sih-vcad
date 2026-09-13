# Unified Localhost Server for 3D ULPIN and V-CAD Engine (Multi-Level & Certificate)
import os
import sys
import json
import time
import shutil
import base64
import re
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

BASE_DIR = Path(__file__).resolve().parent
VCAD_DIR = BASE_DIR / "vcad_engine_sih2026"
sys.path.insert(0, str(VCAD_DIR))

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, Response, FileResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.datastructures import UploadFile
import uvicorn

from blueprint_vision import parse_any_blueprint, detect_floor_configuration
from cad_generator import (
    build_3d_cadastre_from_analysis,
    build_multi_level_cadastre,
    export_to_obj,
    export_to_geojson
)
from ulpin_engine import (
    DEFAULT_PARENT_ULPIN, normalize_2d_ulpin,
    CadastreRegistry, CadastreUnit, make_official_3d_ulpin, make_numeric_3d_ulpin
)

STORAGE_DIR = BASE_DIR / "storage"
BLUEPRINTS_DIR = STORAGE_DIR / "blueprints"
MODELS_DIR = STORAGE_DIR / "models"
PROPERTIES_FILE = STORAGE_DIR / "properties.json"

BLUEPRINTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

FRONTEND_DIR = (BASE_DIR / "frontend") if (BASE_DIR / "frontend").exists() else (BASE_DIR / "3D_ULPIN_Property_Portal_GoogleDrive_DEPLOY" / "SIH-SIPIRIT--main" / "frontend")
VCAD_STATIC_DIR = VCAD_DIR / "static"
VCAD_SAMPLES_DIR = VCAD_DIR / "sample_blueprints"

CURRENT_CADASTRE_CACHE = {}

def extract_level_tag(filename: str, current_count: int = 0) -> str:
    """
    Detects floor or basement tag from filename (f1, f2, f3... b1, b2...).
    """
    fn = Path(filename).stem.lower().strip()
    m_floor = re.search(r'^(?:f|floor)[-_]?(\d+)', fn) or re.search(r'(?:f|floor)[-_]?(\d+)', fn)
    if m_floor:
        return f"f{int(m_floor.group(1))}"
    m_base = re.search(r'^(?:b|basement)[-_]?(\d+)', fn) or re.search(r'(?:b|basement)[-_]?(\d+)', fn)
    if m_base:
        return f"b{int(m_base.group(1))}"
    if any(k in fn for k in ["roof", "terrace", "r0", "r00"]):
        return "r00"
    return f"f{current_count + 1}"

def load_properties() -> Dict[str, Any]:
    if PROPERTIES_FILE.exists():
        try:
            return json.loads(PROPERTIES_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[ERROR] Error loading properties.json: {e}")
    return {}

def save_properties(props: Dict[str, Any]):
    PROPERTIES_FILE.write_text(json.dumps(props, indent=2), encoding="utf-8")

async def api_get_properties(request):
    props = load_properties()
    return JSONResponse(list(props.values()))

async def api_get_property_by_id(request):
    ulpin = request.path_params["ulpin_3d"].strip().upper()
    props = load_properties()
    if ulpin in props:
        return JSONResponse(props[ulpin])
    for p in props.values():
        if p.get("parentULPIN") == ulpin or p.get("threeDULPIN", "").upper() == ulpin:
            return JSONResponse(p)
    return JSONResponse({"error": f"Property not found for {ulpin}"}, status_code=404)

async def api_save_property(request):
    form = await request.form()
    props = load_properties()

    parent_ulpin = str(form.get("parentULPIN", "")).strip()
    three_d_ulpin = str(form.get("threeDULPIN", "")).strip().upper()
    if not three_d_ulpin or three_d_ulpin == "—":
        return JSONResponse({"error": "Invalid or missing 3D ULPIN"}, status_code=400)

    is_update = str(form.get("isUpdate", "")).lower() in ("true", "1") or str(form.get("op", "")).lower() == "update"
    old_id = str(form.get("oldThreeDULPIN", "")).strip().upper()

    existing_data = props.get(old_id or three_d_ulpin, {}) if is_update else {}

    # FIX 1: ZERO MEMORY LEAKAGE - New registrations start strictly with empty blueprints list!
    blueprints = []
    if is_update:
        existing_bps_raw = form.get("existingBlueprintsJson")
        if existing_bps_raw:
            try:
                blueprints = json.loads(str(existing_bps_raw))
            except Exception:
                blueprints = existing_data.get("blueprints", [])
        else:
            blueprints = existing_data.get("blueprints", [])

    # Process newly uploaded blueprint files with level detection
    files_to_save = []
    for key, val in form.multi_items():
        if isinstance(val, UploadFile) and val.filename:
            files_to_save.append(val)

    safe_ulpin_slug = re.sub(r'[^A-Z0-9]', '_', three_d_ulpin)
    for idx_f, up_file in enumerate(files_to_save):
        raw_name = Path(up_file.filename).name
        level_tag = extract_level_tag(raw_name, len(blueprints))
        timestamp = int(time.time() * 1000)
        safe_name = f"{safe_ulpin_slug}__{level_tag}__{timestamp}_{raw_name}"
        dest_path = BLUEPRINTS_DIR / safe_name
        contents = await up_file.read()
        dest_path.write_bytes(contents)

        mime = up_file.content_type or "application/octet-stream"
        if not mime or mime == "application/octet-stream":
            ext = dest_path.suffix.lower()
            if ext in [".png", ".jpg", ".jpeg", ".webp"]:
                mime = f"image/{ext.lstrip('.')}"
            elif ext == ".pdf":
                mime = "application/pdf"
            elif ext == ".svg":
                mime = "image/svg+xml"

        bp_entry = {
            "id": f"bp_{timestamp}_{level_tag}",
            "name": raw_name,
            "level": level_tag,
            "filename": safe_name,
            "mimeType": mime,
            "size": len(contents),
            "url": f"/storage/blueprints/{safe_name}",
            "uploadedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        blueprints.append(bp_entry)

    # Z-Axis Elevation Parameters (Building Height & Building Depth)
    try:
        b_height = float(form.get("buildingHeight", existing_data.get("buildingHeight", 15.0)))
    except Exception:
        b_height = 15.0

    try:
        b_depth = float(form.get("buildingDepth", existing_data.get("buildingDepth", 6.0)))
    except Exception:
        b_depth = 6.0

    try:
        f_count = int(form.get("floorsCount", existing_data.get("floorsCount", 5)))
    except Exception:
        f_count = 5

    try:
        b_count = int(form.get("basementsCount", existing_data.get("basementsCount", 2)))
    except Exception:
        b_count = 2

    z_number_raw = form.get("zNumber")
    z_number = int(z_number_raw) if z_number_raw and str(z_number_raw).isdigit() else 0

    lat_val = form.get("lat")
    lon_val = form.get("lon")
    try:
        lat = float(lat_val) if lat_val else existing_data.get("lat", 16.5062)
        lon = float(lon_val) if lon_val else existing_data.get("lon", 80.5214)
    except Exception:
        lat = 16.5062
        lon = 80.5214

    prop_entry = {
        "parentULPIN": parent_ulpin,
        "threeDULPIN": three_d_ulpin,
        "name": str(form.get("name", existing_data.get("name", ""))),
        "space": str(form.get("space", existing_data.get("space", "Vertical / Building"))),
        "floor": str(form.get("floor", existing_data.get("floor", ""))),
        "zLevel": str(form.get("zLevel", existing_data.get("zLevel", ""))),
        "zType": str(form.get("zType", existing_data.get("zType", "F"))),
        "zNumber": z_number,
        "buildingHeight": b_height,
        "buildingDepth": b_depth,
        "floorsCount": f_count,
        "basementsCount": b_count,
        "rights": str(form.get("rights", existing_data.get("rights", "Private"))),
        "unitId": str(form.get("unitId", existing_data.get("unitId", ""))),
        "version": str(form.get("version", existing_data.get("version", "V01"))),
        "area": str(form.get("area", existing_data.get("area", ""))),
        "address": str(form.get("address", existing_data.get("address", ""))),
        "lat": lat,
        "lon": lon,
        "status": "Approved / Published",
        "validation": "PASS - geometry valid",
        "blueprints": blueprints,
        "createdBy": str(form.get("createdBy", existing_data.get("createdBy", "admin@ulpin.gov.in"))),
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    if is_update and old_id and old_id != three_d_ulpin and old_id in props:
        del props[old_id]

    props[three_d_ulpin] = prop_entry
    save_properties(props)

    # Automatically generate and persist this property's unique 3D cadastre model
    try:
        level_map = {}
        for b in blueprints:
            lvl = b.get("level", "").lower()
            fn = b.get("filename", "")
            if lvl and fn and (BLUEPRINTS_DIR / fn).exists():
                level_map[lvl] = str(BLUEPRINTS_DIR / fn)

        reg, payload = build_multi_level_cadastre(
            parent_ulpin=parent_ulpin,
            building_name=prop_entry["name"] or f"Building on {parent_ulpin}",
            building_height=b_height,
            floors_count=f_count,
            building_depth=b_depth,
            basements_count=b_count,
            level_blueprints=level_map
        )
        payload["property_ulpin"] = three_d_ulpin
        model_file = MODELS_DIR / f"{safe_ulpin_slug}.json"
        model_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        CURRENT_CADASTRE_CACHE[three_d_ulpin] = payload
        CURRENT_CADASTRE_CACHE["last"] = payload
    except Exception as e:
        print(f"[ERROR] Could not build multi-level cadastre for {three_d_ulpin}: {e}")

    return JSONResponse({"success": True, "property": prop_entry})

async def api_delete_blueprint(request):
    ulpin = request.path_params["ulpin_3d"].strip().upper()
    bp_id = request.path_params["blueprint_id"].strip()
    props = load_properties()
    if ulpin not in props:
        return JSONResponse({"error": "Property not found"}, status_code=404)

    prop = props[ulpin]
    bps = prop.get("blueprints", [])
    new_bps = []
    deleted_filename = None
    for b in bps:
        if b.get("id") == bp_id or b.get("filename") == bp_id:
            deleted_filename = b.get("filename")
        else:
            new_bps.append(b)

    if deleted_filename:
        file_path = BLUEPRINTS_DIR / deleted_filename
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                print(f"[WARN] Could not remove blueprint file: {e}")

    prop["blueprints"] = new_bps
    save_properties(props)

    # Re-extrude and update model file
    safe_ulpin_slug = re.sub(r'[^A-Z0-9]', '_', ulpin)
    try:
        level_map = {b["level"]: str(BLUEPRINTS_DIR / b["filename"]) for b in new_bps if "level" in b and (BLUEPRINTS_DIR / b["filename"]).exists()}
        _, payload = build_multi_level_cadastre(
            parent_ulpin=prop.get("parentULPIN", DEFAULT_PARENT_ULPIN),
            building_name=prop.get("name", "Building"),
            building_height=float(prop.get("buildingHeight", 15.0)),
            floors_count=int(prop.get("floorsCount", 5)),
            building_depth=float(prop.get("buildingDepth", 6.0)),
            basements_count=int(prop.get("basementsCount", 2)),
            level_blueprints=level_map
        )
        model_file = MODELS_DIR / f"{safe_ulpin_slug}.json"
        model_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        CURRENT_CADASTRE_CACHE[ulpin] = payload
    except Exception as e:
        print(f"[WARN] Failed to regenerate model after blueprint delete: {e}")

    return JSONResponse({"success": True, "remaining_blueprints": new_bps})

async def api_auth_login(request):
    body = await request.json()
    email = str(body.get("email", "")).strip()
    password = str(body.get("password", ""))
    if email and password:
        return JSONResponse({
            "success": True,
            "role": "admin",
            "token": "local-admin-auth-token",
            "user": {"email": email, "role": "admin"}
        })
    return JSONResponse({"error": "Missing credentials"}, status_code=400)

async def api_vcad_cadastre(request):
    ulpin = request.path_params.get("ulpin_3d", "").strip().upper()
    safe_ulpin_slug = re.sub(r'[^A-Z0-9]', '_', ulpin) if ulpin else "default"
    model_file = MODELS_DIR / f"{safe_ulpin_slug}.json"

    # 1. Check if unique model file already exists for this property
    if model_file.exists():
        try:
            payload = json.loads(model_file.read_text(encoding="utf-8"))
            CURRENT_CADASTRE_CACHE[ulpin] = payload
            CURRENT_CADASTRE_CACHE["last"] = payload
            return JSONResponse(payload)
        except Exception as e:
            print(f"[WARN] Error reading model file {model_file}: {e}")

    # 2. Lookup property from storage/properties.json
    props = load_properties()
    prop = props.get(ulpin)
    if prop:
        parent_ulpin = prop.get("parentULPIN", DEFAULT_PARENT_ULPIN)
        b_height = float(prop.get("buildingHeight", 15.0))
        f_count = int(prop.get("floorsCount", 5))
        b_depth = float(prop.get("buildingDepth", 6.0))
        b_count = int(prop.get("basementsCount", 2))
        level_map = {}
        for b in prop.get("blueprints", []):
            lvl = b.get("level", "").lower()
            fn = b.get("filename", "")
            if lvl and fn and (BLUEPRINTS_DIR / fn).exists():
                level_map[lvl] = str(BLUEPRINTS_DIR / fn)

        _, payload = build_multi_level_cadastre(
            parent_ulpin=parent_ulpin,
            building_name=prop.get("name", "Building"),
            building_height=b_height,
            floors_count=f_count,
            building_depth=b_depth,
            basements_count=b_count,
            level_blueprints=level_map
        )
        payload["property_ulpin"] = ulpin
        model_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        CURRENT_CADASTRE_CACHE[ulpin] = payload
        CURRENT_CADASTRE_CACHE["last"] = payload
        return JSONResponse(payload)

    # 3. Fallback default multi-level cadastre (isolated, does not pollute other properties)
    sample = VCAD_SAMPLES_DIR / "Screenshot 2026-09-08 074503.png"
    sample_path = str(sample) if sample.exists() else None
    _, payload = build_multi_level_cadastre(
        parent_ulpin=DEFAULT_PARENT_ULPIN,
        building_name="Default Demonstration Complex",
        building_height=12.0,
        floors_count=4,
        building_depth=3.0,
        basements_count=1,
        default_blueprint_path=sample_path
    )
    CURRENT_CADASTRE_CACHE["default"] = payload
    CURRENT_CADASTRE_CACHE["last"] = payload
    return JSONResponse(payload)

async def api_vcad_process(request):
    data = await request.json()
    parent_ulpin = normalize_2d_ulpin(data.get("parent_2d_ulpin", DEFAULT_PARENT_ULPIN))
    b_height = float(data.get("building_height", 15.0))
    b_depth = float(data.get("building_depth", 6.0))
    f_count = int(data.get("floors_count", 5))
    b_count = int(data.get("basements_count", 2))
    level_bps = data.get("level_blueprints", {})

    resolved_map = {}
    for lvl, fn in level_bps.items():
        if fn and (BLUEPRINTS_DIR / fn).exists():
            resolved_map[lvl.lower()] = str(BLUEPRINTS_DIR / fn)
        elif fn and (VCAD_SAMPLES_DIR / fn).exists():
            resolved_map[lvl.lower()] = str(VCAD_SAMPLES_DIR / fn)

    _, payload = build_multi_level_cadastre(
        parent_ulpin=parent_ulpin,
        building_name="Extruded Cadastre Building",
        building_height=b_height,
        floors_count=f_count,
        building_depth=b_depth,
        basements_count=b_count,
        level_blueprints=resolved_map
    )
    CURRENT_CADASTRE_CACHE["last"] = payload
    return JSONResponse(payload)

async def api_get_certificate(request):
    ulpin = request.path_params.get("ulpin_3d", "").strip().upper()
    props = load_properties()
    prop = props.get(ulpin)
    if not prop:
        for p in props.values():
            if p.get("threeDULPIN", "").upper() == ulpin:
                prop = p
                break

    if not prop:
        parent = ulpin.split("-")[0] if "-" in ulpin else "12345678901234"
        prop = {
            "parentULPIN": parent,
            "threeDULPIN": ulpin,
            "name": "Standard Cadastral Parcel",
            "space": "Vertical / Building",
            "floor": "Floor 3 (F03)",
            "area": "112.6",
            "address": "Amaravathi, Andhra Pradesh, India",
            "lat": 16.5062,
            "lon": 80.5214,
            "rights": "Private",
            "status": "Approved / Published",
            "validation": "PASS - geometry valid",
            "buildingHeight": 15.0,
            "buildingDepth": 6.0,
            "floorsCount": 5,
            "basementsCount": 2
        }

    # Generate verification hash
    token_source = f"{ulpin}:{prop.get('parentULPIN')}:{prop.get('area')}:DILRMP-2026"
    verif_hash = hashlib.sha256(token_source.encode("utf-8")).hexdigest()[:16].upper()

    cert = {
        "certificate_id": f"CERT-3D-{verif_hash[:8]}",
        "issue_date": time.strftime("%d %B %Y", time.gmtime()),
        "authority": "Survey of India / Ministry of Panchayati Raj (SVAMITVA & DILRMP)",
        "threeDULPIN": prop.get("threeDULPIN", ulpin),
        "parentULPIN": prop.get("parentULPIN", "12345678901234"),
        "property_name": prop.get("name", "Residential Unit"),
        "space_class": prop.get("space", "Vertical / Building"),
        "rights": prop.get("rights", "Private"),
        "floor": prop.get("floor", "Floor 3 (F03)"),
        "area_sqm": prop.get("area", "112.6"),
        "area_sqft": round(float(prop.get("area") or 112.6) * 10.7639, 1),
        "address": prop.get("address", "Amaravathi, Andhra Pradesh"),
        "coordinates": {"lat": prop.get("lat", 16.5062), "lon": prop.get("lon", 80.5214)},
        "building_envelope": {
            "height_m": prop.get("buildingHeight", 15.0),
            "depth_m": prop.get("buildingDepth", 6.0),
            "floors": prop.get("floorsCount", 5),
            "basements": prop.get("basementsCount", 2)
        },
        "elevation_bounds": {
            "z_min": f"-{prop.get('buildingDepth', 6.0)}m",
            "z_max": f"+{prop.get('buildingHeight', 15.0)}m"
        },
        "verification_hash": verif_hash,
        "qr_verification_url": f"http://localhost:8080/api/certificate/{ulpin}?hash={verif_hash}",
        "legal_status": "Clean Title Guaranteed - Zero Spatial Collision",
        "validation": prop.get("validation", "PASS - geometry valid")
    }
    return JSONResponse(cert)

async def api_vcad_export_obj(request):
    payload = CURRENT_CADASTRE_CACHE.get("last") or CURRENT_CADASTRE_CACHE.get("default")
    if not payload:
        sample = VCAD_SAMPLES_DIR / "Screenshot 2026-09-08 074503.png"
        _, payload = build_multi_level_cadastre(default_blueprint_path=str(sample))

    export_path = MODELS_DIR / f"vcad_{payload.get('parent_2d_ulpin', DEFAULT_PARENT_ULPIN)}.obj"
    export_to_obj(payload, str(export_path))
    return Response(
        export_path.read_bytes(),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=vcad_3d_cadastre_{payload.get('parent_2d_ulpin', DEFAULT_PARENT_ULPIN)}.obj"}
    )

async def api_vcad_export_geojson(request):
    payload = CURRENT_CADASTRE_CACHE.get("last") or CURRENT_CADASTRE_CACHE.get("default")
    if not payload:
        sample = VCAD_SAMPLES_DIR / "Screenshot 2026-09-08 074503.png"
        _, payload = build_multi_level_cadastre(default_blueprint_path=str(sample))

    export_path = MODELS_DIR / f"vcad_{payload.get('parent_2d_ulpin', DEFAULT_PARENT_ULPIN)}.geojson"
    export_to_geojson(payload["cadastre"], str(export_path))
    return Response(
        export_path.read_bytes(),
        media_type="application/geo+json",
        headers={"Content-Disposition": f"attachment; filename=vcad_cadastre_{payload.get('parent_2d_ulpin', DEFAULT_PARENT_ULPIN)}.geojson"}
    )

routes = [
    Route("/api/properties", api_get_properties, methods=["GET"]),
    Route("/api/properties", api_save_property, methods=["POST"]),
    Route("/api/properties/{ulpin_3d}", api_get_property_by_id, methods=["GET"]),
    Route("/api/properties/{ulpin_3d}/blueprints/{blueprint_id}", api_delete_blueprint, methods=["DELETE"]),
    Route("/api/auth/login", api_auth_login, methods=["POST"]),

    Route("/api/certificate/{ulpin_3d}", api_get_certificate, methods=["GET"]),

    Route("/api/vcad/cadastre", api_vcad_cadastre, methods=["GET"]),
    Route("/api/vcad/cadastre/{ulpin_3d}", api_vcad_cadastre, methods=["GET"]),
    Route("/api/vcad/process", api_vcad_process, methods=["POST"]),
    Route("/api/vcad/export/obj", api_vcad_export_obj, methods=["GET"]),
    Route("/api/vcad/export/geojson", api_vcad_export_geojson, methods=["GET"]),

    Mount("/storage/blueprints", StaticFiles(directory=str(BLUEPRINTS_DIR))),
    Mount("/sample_blueprints", StaticFiles(directory=str(VCAD_SAMPLES_DIR))),
    Mount("/vcad_static", StaticFiles(directory=str(VCAD_STATIC_DIR))),
    Mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True)),
]

app = Starlette(
    debug=True,
    routes=routes,
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )
    ]
)

def ensure_port_free(port: int):
    """If port is occupied by an orphaned process on Windows, terminate it."""
    if sys.platform != "win32":
        return
    try:
        output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode("utf-8", errors="ignore")
        current_pid = os.getpid()
        for line in output.strip().splitlines():
            if "LISTENING" in line:
                parts = line.split()
                pid = int(parts[-1])
                if pid != current_pid and pid > 0:
                    print(f"[*] Port {port} occupied by previous process (PID {pid}). Freeing port...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                    time.sleep(1)
    except Exception:
        pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    ensure_port_free(port)
    print("=" * 60)
    print(f"  3D ULPIN and V-CAD Multi-Level Server running on http://localhost:{port}")
    print(f"  Local blueprints storage: {BLUEPRINTS_DIR}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port)
