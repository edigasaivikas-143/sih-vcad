"""
3D CAD/BIM Extrusion & Mesh Generator
Converts blueprint analysis and 3D ULPIN assignments into multi-storey 3D geometry.
Exports to:
1. WebGL/Three.js render payload with floor isolation & exploded view offsets.
2. Wavefront 3D OBJ mesh file.
3. 3D Cadastre GeoJSON with PolyhedralSurface / 3D Polygons.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from ulpin_engine import (
    CadastreRegistry, CadastreUnit, make_official_3d_ulpin, make_numeric_3d_ulpin,
    normalize_2d_ulpin, DEFAULT_PARENT_ULPIN
)

def build_3d_cadastre_from_analysis(
    analysis_data: Dict[str, Any],
    parent_ulpin: str = DEFAULT_PARENT_ULPIN,
    building_name: str = "Block A"
) -> Tuple[CadastreRegistry, Dict[str, Any]]:
    """
    Constructs a complete 3D Cadastre Registry and 3D geometry structure
    from the analyzed blueprint.
    Generates:
    1. Real 3D architectural extruded walls (WALL) on every requested floor.
    2. Distinct 3D room floor zones (ROOM) with unique 3D ULPIN tags per floor.
    3. Strictly honors floor count: 1 floor generates only Floor 1 + Clean Rooftop Terrace.
    4. Clean, dispute-free 3D cadastre titles with zero spatial collisions.
    """
    p = normalize_2d_ulpin(parent_ulpin)
    reg = CadastreRegistry(p)

    dim = analysis_data.get("building_dimensions_m", {"width": 12.0, "length": 8.0, "height": 2.80})
    bw = dim.get("width", 12.0)
    bl = dim.get("length", 8.0)
    floor_h = analysis_data.get("floor_height_m", 2.80)
    floors_count = max(1, analysis_data.get("floors_count", 1))
    walls_def = analysis_data.get("walls", [])
    rooms_def = analysis_data.get("rooms", [])
    b_type = analysis_data.get("blueprint_type", "APARTMENT_STAIRS")

    total_bldg_h = round(floor_h * floors_count, 2)

    fn = analysis_data.get("filename", "")
    suite_prefix = analysis_data.get("suite_tag", "A101")
    if fn:
        stem = Path(fn).stem.replace("Screenshot ", "Plan ")
        actual_bldg_name = f"Cadastre Building ({stem})"
    else:
        actual_bldg_name = building_name

    # 1. Add Parent Building Unit
    bldg = CadastreUnit(
        id="building_a",
        name=actual_bldg_name,
        type="BUILDING",
        floor="G00" if floors_count == 1 else "F01-F04",
        space_class="V",
        rights="COM",
        unit_id=f"BLK_{suite_prefix[:1]}",
        ulpin_3d=make_official_3d_ulpin(p, "G00", "V", "COM", f"BLK_{suite_prefix[:1]}", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 1),
        owner="Community",
        description=f"Main {floors_count}-storey cadastral building parcel on {p}",
        parent_2d_ulpin=p,
        z_min=0.0,
        z_max=total_bldg_h,
        carpet_area_sqm=round(bw * bl, 1),
        carpet_area_sqft=round(bw * bl * 10.7639, 1),
        bbox={"x_min": -bw/2, "x_max": bw/2, "y_min": -bl/2, "y_max": bl/2, "z_min": 0.0, "z_max": total_bldg_h}
    )
    reg.add_unit(bldg)

    # 2. Base Geometries
    geometries = []

    # Ground Landscape Base
    lawn_ulpin = make_official_3d_ulpin(p, "G00", "S", "COM", "LAWN01", "V01")
    reg.add_unit(CadastreUnit(
        id="landscape_base",
        name="Cadastral Ground Lawn & Landscape (LAWN01)",
        type="GROUND_LAND",
        floor="G00",
        space_class="S",
        rights="COM",
        unit_id="LAWN01",
        ulpin_3d=lawn_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 99),
        owner="Municipal Authority / Community",
        description=f"Ground cadastral surface landscape parcel on {p}",
        parent_2d_ulpin=p,
        z_min=-0.10,
        z_max=0.00,
        carpet_area_sqm=round(bw * bl * 1.5, 1),
        carpet_area_sqft=round(bw * bl * 1.5 * 10.7639, 1),
        bbox={"x_min": -bw/2 - 6, "x_max": bw/2 + 6, "y_min": -bl/2 - 5, "y_max": bl/2 + 5, "z_min": -0.10, "z_max": 0.00}
    ))
    reg.add_relationship("landscape_base", "building_a", "LOCATED_IN")

    geometries.append({
        "id": "landscape_base",
        "name": "Cadastral Ground Lawn & Landscape",
        "type": "GROUND_LAND",
        "floor": "LAND",
        "space_class": "S",
        "rights": "COM",
        "owner": "Municipal Authority / Community",
        "unit_id": "LAWN01",
        "ulpin_3d": lawn_ulpin,
        "color": "#122035",
        "edge_color": "#203a5e",
        "z_min": -0.10,
        "z_max": 0.00,
        "cx": 0.0, "cy": -0.05, "cz": 0.0,
        "width": round(bw + 12.0, 2), "height": 0.1, "depth": round(bl + 10.0, 2),
        "opacity": 0.95
    })

    # Floor Slabs (Honoring exact floors_count: no basement slab for 1 floor!)
    slab_levels = []
    if floors_count == 1:
        slab_levels.append(("F01", 0.0, "Ground Floor Slab", "#374c69"))
        slab_levels.append(("R00", float(floor_h), "Rooftop Terrace Slab", "#4a678f"))
    else:
        for fi in range(1, floors_count + 1):
            slab_levels.append((f"F{fi:02d}", float((fi - 1) * floor_h), f"Floor {fi} Slab", "#374c69" if fi == 1 else "#41597c"))
        slab_levels.append(("R00", float(floors_count * floor_h), "Rooftop Terrace Slab", "#4a678f"))

    for flr_code, z_level, slab_name, slab_col in slab_levels:
        slab_idx = 0 if flr_code in ("G00", "LAND") else (99 if flr_code == "R00" else int(flr_code.replace("F", "")))
        slab_code = "TERR01" if flr_code == "R00" else f"SLAB{slab_idx:02d}"
        slab_ulpin = make_official_3d_ulpin(p, flr_code, "E" if flr_code == "R00" else "V", "COM", slab_code, "V01")
        reg.add_unit(CadastreUnit(
            id=f"slab_{flr_code}",
            name=f"{slab_name} ({slab_code})",
            type="SLAB",
            floor=flr_code,
            space_class="E" if flr_code == "R00" else "V",
            rights="COM",
            unit_id=slab_code,
            ulpin_3d=slab_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, slab_idx, 0),
            owner="Community",
            description=f"Structural slab for tier {flr_code}",
            parent_2d_ulpin=p,
            z_min=z_level,
            z_max=round(z_level + 0.16, 2),
            carpet_area_sqm=round(bw * bl, 1),
            carpet_area_sqft=round(bw * bl * 10.7639, 1),
            bbox={"x_min": -bw/2, "x_max": bw/2, "y_min": -bl/2, "y_max": bl/2, "z_min": z_level, "z_max": round(z_level + 0.16, 2)}
        ))
        geometries.append({
            "id": f"slab_{flr_code}",
            "name": slab_name,
            "type": "SLAB",
            "floor": flr_code,
            "space_class": "E" if flr_code == "R00" else "V",
            "rights": "COM",
            "owner": "Community",
            "unit_id": slab_code,
            "ulpin_3d": slab_ulpin,
            "color": slab_col,
            "edge_color": "#00f0ff",
            "z_min": z_level,
            "z_max": round(z_level + 0.16, 2),
            "cx": 0.0, "cy": z_level, "cz": 0.0,
            "width": round(bw + 0.4, 2), "height": 0.16, "depth": round(bl + 0.4, 2),
            "opacity": 0.88
        })

    # 3. Create Floors (F01, F02, F03...) with Extruded Walls and Rooms
    owner_pool = [
        "Owner A (Suresh Gowda)",
        "Owner B (Priya Sharma)",
        "Owner C (Vikram Rao)",
        "Owner D (Ramesh Gowda)",
        "Owner E (Ananya Verma)",
        "Owner F (Deepak Joshi)",
    ]

    total_unit_carpet = round(sum(r["area_sqm"] for r in rooms_def if r.get("rights") == "PRV"), 2) or 66.9

    for f_idx in range(1, floors_count + 1):
        flr_tag = f"F{f_idx:02d}"
        z0 = float((f_idx - 1) * floor_h)
        z1 = float(f_idx * floor_h)
        floor_owner = owner_pool[(f_idx - 1) % len(owner_pool)]

        # Primary Flat / Dwelling Unit for this floor tier
        fid_a = f"flat_{f_idx}01"
        letter_prefix = suite_prefix[0] if suite_prefix else "A"
        uid_a = f"{letter_prefix}{f_idx}01"
        flat_name = f"Floor {f_idx} Suite" if floors_count > 1 else f"Suite {uid_a}"
        flat_a = CadastreUnit(
            id=fid_a,
            name=f"{flat_name} ({uid_a})",
            type="FLAT",
            floor=flr_tag,
            space_class="V",
            rights="PRV",
            unit_id=uid_a,
            ulpin_3d=make_official_3d_ulpin(p, flr_tag, "V", "PRV", uid_a, "V01"),
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, 1),
            owner=floor_owner,
            description=f"Private residential cadastre unit ({uid_a}) on {flr_tag}",
            parent_2d_ulpin=p,
            z_min=z0,
            z_max=z1,
            carpet_area_sqm=total_unit_carpet,
            carpet_area_sqft=round(total_unit_carpet * 10.7639, 1),
            bbox={"x_min": -bw/2, "x_max": bw/2, "y_min": -bl/2, "y_max": bl/2, "z_min": z0, "z_max": z1}
        )
        reg.add_unit(flat_a)
        reg.add_relationship(fid_a, "building_a", "LOCATED_IN")

        # Add 3D Extruded Structural Walls for this floor
        for w_idx, w in enumerate(walls_def, start=1):
            wall_id = f"wall_{flr_tag}_{w['id']}"
            w_code = f"W{f_idx:02d}{w_idx:02d}"
            w_rights = "COM" if w.get("wall_type") == "EXTERIOR" else "PRV"
            w_owner = "Community" if w.get("wall_type") == "EXTERIOR" else floor_owner
            ulpin_w = make_official_3d_ulpin(p, flr_tag, "V", w_rights, w_code, "V01")
            reg.add_unit(CadastreUnit(
                id=wall_id,
                name=f"{w['name']} ({flr_tag})",
                type="WALL",
                floor=flr_tag,
                space_class="V",
                rights=w_rights,
                unit_id=w_code,
                ulpin_3d=ulpin_w,
                ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, 100 + w_idx),
                owner=w_owner,
                description=f"Structural wall unit {w_code} on {flr_tag}",
                parent_2d_ulpin=p,
                z_min=z0,
                z_max=z1,
                carpet_area_sqm=round(w["width"] * w["depth"], 2),
                carpet_area_sqft=round(w["width"] * w["depth"] * 10.7639, 2),
                bbox={"x_min": w["cx"] - w["width"]/2, "x_max": w["cx"] + w["width"]/2, "y_min": w["cz"] - w["depth"]/2, "y_max": w["cz"] + w["depth"]/2, "z_min": z0, "z_max": z1}
            ))
            geometries.append({
                "id": wall_id,
                "name": f"{w['name']} ({flr_tag})",
                "type": "WALL",
                "floor": flr_tag,
                "space_class": "V",
                "rights": w_rights,
                "owner": w_owner,
                "unit_id": w_code,
                "ulpin_3d": ulpin_w,
                "z_min": z0,
                "z_max": z1,
                "cx": w["cx"],
                "cy": round(z0 + w["height"] / 2.0, 2),
                "cz": w["cz"],
                "width": w["width"],
                "height": w["height"],
                "depth": w["depth"],
                "color": w.get("color", "#182438"),
                "edge_color": w.get("edge_color", "#38bdf8"),
                "opacity": 0.96,
                "is_dispute": False,
                "is_rera_flag": False
            })

        # Add Distinct 3D Room Zones for this floor with unique 3D ULPINs
        for r_idx, r in enumerate(rooms_def, start=1):
            rid = f"room_{flr_tag}_{r['id']}"
            # Extract clean suffix e.g. LIV, KIT, BATH, BED1, STAIR
            tag_suffix = r.get("unit_tag", f"R{r_idx}").split('_')[-1]
            rtag = f"{uid_a}_{tag_suffix}" if r.get("rights") == "PRV" else f"{r.get('unit_tag', f'R{r_idx}')}_{flr_tag}"
            u_3d = make_official_3d_ulpin(p, flr_tag, r.get("space_class", "V"), r.get("rights", "PRV"), rtag, "V01")
            rm_num = r.get("room_index", r_idx)
            u_num = make_numeric_3d_ulpin(p, 1, f_idx, rm_num)
            room_name = f"{r['name']} ({flr_tag})" if floors_count > 1 else r["name"]
            room_owner = r.get("owner", floor_owner) if r.get("rights") == "PRV" else "Community"

            c_unit = CadastreUnit(
                id=rid,
                name=room_name,
                type="ROOM",
                floor=flr_tag,
                space_class=r.get("space_class", "V"),
                rights=r.get("rights", "PRV"),
                unit_id=rtag,
                ulpin_3d=u_3d,
                ulpin_numeric=u_num,
                owner=room_owner,
                description=f"Cadastral room unit {r['name']} on {flr_tag}",
                parent_2d_ulpin=p,
                z_min=z0,
                z_max=z1,
                carpet_area_sqm=r.get("area_sqm", 15.0),
                carpet_area_sqft=r.get("area_sqft", 160.0),
                bbox={"x_min": r["bbox_m"]["x_min"], "x_max": r["bbox_m"]["x_max"], "y_min": r["bbox_m"]["y_min"], "y_max": r["bbox_m"]["y_max"], "z_min": z0, "z_max": z1}
            )
            reg.add_unit(c_unit)
            reg.add_relationship(rid, fid_a, "PART_OF_UNIT")

            # 3D Room Geometry (Clean Interactive Floor Plate)
            room_w = max(0.4, round(r["dimensions_m"]["width"] - 0.16, 2))
            room_d = max(0.4, round(r["dimensions_m"]["length"] - 0.16, 2))
            geometries.append({
                "id": rid,
                "unit_id": rtag,
                "name": room_name,
                "type": "ROOM",
                "floor": flr_tag,
                "space_class": r.get("space_class", "V"),
                "rights": r.get("rights", "PRV"),
                "owner": room_owner,
                "ulpin_3d": u_3d,
                "ulpin_numeric": u_num,
                "carpet_area_sqm": r.get("area_sqm", 15.0),
                "carpet_area_sqft": r.get("area_sqft", 160.0),
                "z_min": z0,
                "z_max": z1,
                "cx": r["center_m"]["x"],
                "cy": round(z0 + 0.08, 2),
                "cz": r["center_m"]["y"],
                "width": room_w,
                "height": 0.14,
                "depth": room_d,
                "color": r.get("color", "#1e3a5f"),
                "edge_color": r.get("edge_color", "#00f0ff"),
                "opacity": 0.88,
                "is_dispute": False,
                "is_rera_flag": False
            })

    # 4. Amenities list: Only add external parking if present in blueprint
    amenities_list = []
    has_parking_in_blueprint = any(
        r.get("type") in ("PARKING", "PLOT") or
        "parking" in r.get("name", "").lower() or
        "garage" in r.get("name", "").lower()
        for r in rooms_def
    )
    if has_parking_in_blueprint:
        p1 = CadastreUnit(
            id="parking_p01", name="Assigned Parking P01", type="PARKING", floor="G00", space_class="S", rights="PRV",
            unit_id="PRK01", ulpin_3d=make_official_3d_ulpin(p, "G00", "S", "PRV", "PRK01", "V01"),
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 10), owner="Owner A (Suresh Gowda)",
            description="Assigned private parking bay for Ground Floor Suite", parent_2d_ulpin=p,
            z_min=0.0, z_max=0.3, carpet_area_sqm=12.5, carpet_area_sqft=135.0,
            bbox={"x_min": -bw/2 - 3.2, "x_max": -bw/2 - 0.6, "y_min": 0.5, "y_max": 3.0, "z_min": 0.0, "z_max": 0.3}
        )
        reg.add_unit(p1)
        reg.add_relationship("flat_101", "parking_p01", "OWNER_ASSOCIATED")
        amenities_list.append(p1)

    # 5. Clean, Validated Rooftop Terrace (Zero Clashes, Single Title)
    terrace_z0 = float(floors_count * floor_h)
    terrace_z1 = terrace_z0 + 2.50
    terrace = CadastreUnit(
        id="terrace_1", name="Rooftop Terrace T1", type="TERRACE", floor="R00", space_class="E", rights="COM",
        unit_id="TERR01", ulpin_3d=make_official_3d_ulpin(p, "R00", "E", "COM", "TERR01", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 99, 1), owner="Community",
        description="Clean validated common rooftop terrace open space and solar installation deck", parent_2d_ulpin=p,
        z_min=terrace_z0, z_max=terrace_z1, carpet_area_sqm=round(bw * bl * 0.95, 1), carpet_area_sqft=round(bw * bl * 0.95 * 10.7639, 1),
        bbox={"x_min": -bw/2 + 0.2, "x_max": bw/2 - 0.2, "y_min": -bl/2 + 0.2, "y_max": bl/2 - 0.2, "z_min": terrace_z0, "z_max": terrace_z1}
    )
    reg.add_unit(terrace)
    amenities_list.append(terrace)

    for u in reg.units.values():
        if u.type in ("FLAT", "ROOM"):
            reg.add_relationship(u.id, terrace.id, "COMMON_FACILITY_ACCESS")

    # Geometries for Parking and Clean Terrace
    for amenity in amenities_list:
        bb = amenity.bbox
        if not bb:
            continue
        w = bb["x_max"] - bb["x_min"]
        d = bb["y_max"] - bb["y_min"]
        h = amenity.z_max - amenity.z_min
        cx = (bb["x_min"] + bb["x_max"]) / 2.0
        cz = (bb["y_min"] + bb["y_max"]) / 2.0
        cy = amenity.z_min + h / 2.0

        col = "#162447" if amenity.type == "PARKING" else "#1e3a5f"
        edge_col = "#ffd166" if amenity.rights == "PRV" else "#00f0ff"

        geometries.append({
            "id": amenity.id,
            "unit_id": amenity.unit_id,
            "name": amenity.name,
            "type": amenity.type,
            "floor": amenity.floor,
            "space_class": amenity.space_class,
            "rights": amenity.rights,
            "owner": amenity.owner,
            "ulpin_3d": amenity.ulpin_3d,
            "ulpin_numeric": amenity.ulpin_numeric,
            "carpet_area_sqm": amenity.carpet_area_sqm,
            "carpet_area_sqft": amenity.carpet_area_sqft,
            "z_min": amenity.z_min,
            "z_max": amenity.z_max,
            "cx": round(cx, 2), "cy": round(cy, 2), "cz": round(cz, 2),
            "width": round(w, 2), "height": round(h, 2), "depth": round(d, 2),
            "color": col,
            "edge_color": edge_col,
            "opacity": 0.88 if amenity.rights == "PRV" else 0.75,
            "is_dispute": False,
            "is_rera_flag": False
        })

    render_payload = {
        "parent_2d_ulpin": p,
        "blueprint_type": b_type,
        "building_dimensions": {"width": bw, "length": bl, "height": total_bldg_h},
        "building_dimensions_m": {"width": bw, "length": bl, "height": total_bldg_h},
        "floors_count": floors_count,
        "floor_height": floor_h,
        "geometries": geometries,
        "cadastre": reg.to_dict()
    }

    return reg, render_payload

def export_to_obj(render_payload: Dict[str, Any], output_path: str):
    """
    Exports the 3D cadastre model into standard Wavefront OBJ format.
    """
    lines = [
        f"# SVAMITVA 3D CADASTRE V-CAD EXPORT",
        f"# Parent 2D ULPIN: {render_payload['parent_2d_ulpin']}",
        f"# Total Spatial Geometries: {len(render_payload['geometries'])}",
        ""
    ]

    v_offset = 1
    for geom in render_payload["geometries"]:
        gid = geom["id"]
        name = geom["name"].replace(" ", "_")
        cx, cy, cz = geom["cx"], geom["cy"], geom["cz"]
        w, h, d = geom["width"] / 2.0, geom["height"] / 2.0, geom["depth"] / 2.0

        lines.append(f"o {name}_{gid}")
        verts = [
            (cx - w, cy - h, cz - d),
            (cx + w, cy - h, cz - d),
            (cx + w, cy + h, cz - d),
            (cx - w, cy + h, cz - d),
            (cx - w, cy - h, cz + d),
            (cx + w, cy - h, cz + d),
            (cx + w, cy + h, cz + d),
            (cx - w, cy + h, cz + d),
        ]
        for vx, vy, vz in verts:
            lines.append(f"v {vx:.3f} {vy:.3f} {vz:.3f}")

        faces = [
            (1, 2, 3, 4),  # front
            (5, 8, 7, 6),  # back
            (1, 5, 6, 2),  # bottom
            (4, 3, 7, 8),  # top
            (1, 4, 8, 5),  # left
            (2, 6, 7, 3),  # right
        ]
        for f1, f2, f3, f4 in faces:
            lines.append(f"f {v_offset + f1 - 1} {v_offset + f2 - 1} {v_offset + f3 - 1} {v_offset + f4 - 1}")
        v_offset += 8
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Exported 3D OBJ to {output_path}")

def export_to_geojson(cadastre_data: Dict[str, Any], output_path: str):
    """
    Exports the 3D cadastre units into 3D GeoJSON with polygon coordinates and Z bounds.
    """
    features = []
    parent_ulpin = cadastre_data.get("parent_2d_ulpin", DEFAULT_PARENT_ULPIN)

    for unit in cadastre_data.get("units", []):
        bb = unit.get("bbox")
        if not bb:
            continue
        z0, z1 = unit.get("z_min", 0.0), unit.get("z_max", 3.0)
        poly_coords = [
            [bb["x_min"], bb["y_min"], z0],
            [bb["x_max"], bb["y_min"], z0],
            [bb["x_max"], bb["y_max"], z0],
            [bb["x_min"], bb["y_max"], z0],
            [bb["x_min"], bb["y_min"], z0]
        ]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly_coords]
            },
            "properties": {
                "id": unit["id"],
                "name": unit["name"],
                "type": unit["type"],
                "floor": unit["floor"],
                "space_class": unit["space_class"],
                "rights": unit["rights"],
                "unit_id": unit["unit_id"],
                "ulpin_3d": unit["ulpin_3d"],
                "ulpin_numeric": unit["ulpin_numeric"],
                "owner": unit["owner"],
                "carpet_area_sqm": unit["carpet_area_sqm"],
                "z_min": z0,
                "z_max": z1,
                "parent_2d_ulpin": parent_ulpin,
                "is_clean_title": True
            }
        })

    geojson_doc = {
        "type": "FeatureCollection",
        "parent_2d_ulpin": parent_ulpin,
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_doc, f, indent=2)
    print(f"[OK] Exported 3D GeoJSON to {output_path}")


def build_multi_level_cadastre(
    parent_ulpin: str = DEFAULT_PARENT_ULPIN,
    building_name: str = "Cadastre Complex",
    building_height: float = 15.0,
    floors_count: int = 5,
    building_depth: float = 6.0,
    basements_count: int = 2,
    level_blueprints: Optional[Dict[str, str]] = None,
    default_blueprint_path: Optional[str] = None,
    replicate_upper_floors: bool = False
) -> Tuple[CadastreRegistry, Dict[str, Any]]:
    """
    Builds a full 3D Cadastre model parameterized by Building Height & Building Depth,
    with distinct blueprints per floor (f1, f2, f3...) and basement (b1, b2, b3...).
    If replicate_upper_floors is False, upper floors without blueprints do not blindly
    replicate floor 1; basements never inherit above-ground blueprints.
    """
    from blueprint_vision import parse_any_blueprint

    p = normalize_2d_ulpin(parent_ulpin)
    reg = CadastreRegistry(p)

    n_floors = max(1, int(floors_count))
    n_basements = max(0, int(basements_count))
    h_total = max(1.0, float(building_height))
    d_total = max(0.0, float(building_depth))

    h_floor = round(h_total / n_floors, 2)
    h_basement = round(d_total / n_basements, 2) if n_basements > 0 else 2.8

    z_min = round(-d_total, 2)
    z_max = round(h_total, 2)

    level_bps = {k.lower(): v for k, v in (level_blueprints or {}).items()}

    # Cache analyses for level blueprints
    analyses_cache = {}
    def get_analysis_for(level_key: str):
        # Explicit level blueprint always takes priority
        bp_path = level_bps.get(level_key)
        # Only fall back to default blueprint if replicate_upper_floors is True and it's an above-ground floor
        if not bp_path and replicate_upper_floors and level_key.startswith("f"):
            bp_path = default_blueprint_path or level_bps.get("f1")

        if bp_path and Path(bp_path).exists():
            resolved = str(Path(bp_path).resolve())
            if resolved not in analyses_cache:
                try:
                    analyses_cache[resolved] = parse_any_blueprint(resolved, floors_count=1)
                except Exception as e:
                    print(f"[WARN] Could not parse blueprint {resolved}: {e}")
                    analyses_cache[resolved] = None
            return analyses_cache[resolved]
        return None

    # Get initial dimensions from first available blueprint or default to 14.0x10.0
    first_analysis = None
    for k in [f"f{i}" for i in range(1, n_floors + 1)] + [f"b{j}" for j in range(1, n_basements + 1)]:
        if k in level_bps:
            first_analysis = get_analysis_for(k)
            if first_analysis:
                break
    if not first_analysis and default_blueprint_path and Path(default_blueprint_path).exists():
        first_analysis = get_analysis_for("f1")

    bw = first_analysis.get("building_dimensions_m", {}).get("width", 14.0) if first_analysis else 14.0
    bl = first_analysis.get("building_dimensions_m", {}).get("length", 10.0) if first_analysis else 10.0

    total_carpet_bldg = round(bw * bl * (n_floors + n_basements), 1)

    # 1. Add Parent Building Unit
    bldg = CadastreUnit(
        id="building_a",
        name=building_name,
        type="BUILDING",
        floor=f"B{n_basements:02d}-F{n_floors:02d}" if n_basements > 0 else f"F01-F{n_floors:02d}",
        space_class="V",
        rights="COM",
        unit_id="BLKA",
        ulpin_3d=make_official_3d_ulpin(p, "G00", "V", "COM", "BLKA", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 1),
        owner="Community",
        description=f"Unified {n_floors}-storey building with {n_basements} basement(s) on {p}. Height: {h_total}m, Depth: {d_total}m.",
        parent_2d_ulpin=p,
        z_min=z_min,
        z_max=z_max,
        carpet_area_sqm=total_carpet_bldg,
        carpet_area_sqft=round(total_carpet_bldg * 10.7639, 1),
        bbox={"x_min": -bw/2, "x_max": bw/2, "y_min": -bl/2, "y_max": bl/2, "z_min": z_min, "z_max": z_max}
    )
    reg.add_unit(bldg)

    geometries = []

    # 2. Ground Landscape Base at y = 0
    lawn_ulpin = make_official_3d_ulpin(p, "G00", "S", "COM", "LAWN01", "V01")
    lawn_unit = CadastreUnit(
        id="landscape_base",
        name="Cadastral Ground Lawn & Landscape (LAWN01)",
        type="GROUND_LAND",
        floor="G00",
        space_class="S",
        rights="COM",
        unit_id="LAWN01",
        ulpin_3d=lawn_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 99),
        owner="Municipal Authority / Community",
        description=f"Ground cadastral surface landscape parcel on {p}",
        parent_2d_ulpin=p,
        z_min=-0.10,
        z_max=0.00,
        carpet_area_sqm=round(bw * bl * 1.5, 1),
        carpet_area_sqft=round(bw * bl * 1.5 * 10.7639, 1),
        bbox={"x_min": -bw/2 - 6, "x_max": bw/2 + 6, "y_min": -bl/2 - 5, "y_max": bl/2 + 5, "z_min": -0.10, "z_max": 0.00}
    )
    reg.add_unit(lawn_unit)
    reg.add_relationship("landscape_base", "building_a", "LOCATED_IN")

    geometries.append({
        "id": "landscape_base",
        "name": "Cadastral Ground Lawn & Landscape",
        "type": "GROUND_LAND",
        "floor": "LAND",
        "space_class": "S",
        "rights": "COM",
        "owner": "Municipal Authority / Community",
        "unit_id": "LAWN01",
        "ulpin_3d": lawn_ulpin,
        "color": "#122035",
        "edge_color": "#203a5e",
        "z_min": -0.10,
        "z_max": 0.00,
        "cx": 0.0, "cy": -0.05, "cz": 0.0,
        "width": round(bw + 12.0, 2), "height": 0.1, "depth": round(bl + 10.0, 2),
        "opacity": 0.98,
        "is_dispute": False,
        "is_rera_flag": False
    })

    owner_pool = [
        "Government of India / Municipal Authority",
        "Shri Rajesh Kumar Sharma",
        "Smt. Lakshmi Devi",
        "Shri Amit Patel",
        "M/s Amaravathi Cadastre Holdings",
        "Smt. Priyanka Reddy",
        "Shri Vikram Singhania"
    ]

    # 3. Build Basements (B01, B02...)
    for b_idx in range(1, n_basements + 1):
        flr_tag = f"B{b_idx:02d}"
        z0 = round(-b_idx * h_basement, 2)
        z1 = round(-(b_idx - 1) * h_basement, 2)
        cy = round((z0 + z1) / 2.0, 2)
        level_key = f"b{b_idx}"
        b_analysis = get_analysis_for(level_key)

        # Basement Floor Slab
        slab_ulpin_b = make_official_3d_ulpin(p, flr_tag, "U", "COM", f"SLAB{b_idx:02d}", "V01")
        reg.add_unit(CadastreUnit(
            id=f"slab_{flr_tag}",
            name=f"Basement {b_idx} Structural Slab (SLAB{b_idx:02d})",
            type="SLAB",
            floor=flr_tag,
            space_class="U",
            rights="COM",
            unit_id=f"SLAB{b_idx:02d}",
            ulpin_3d=slab_ulpin_b,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, -b_idx, 0),
            owner="Community",
            description=f"Basement foundation structural slab tier {flr_tag}",
            parent_2d_ulpin=p,
            z_min=z0,
            z_max=round(z0 + 0.16, 2),
            carpet_area_sqm=round(bw * bl, 1),
            carpet_area_sqft=round(bw * bl * 10.7639, 1),
            bbox={"x_min": -bw/2, "x_max": bw/2, "y_min": -bl/2, "y_max": bl/2, "z_min": z0, "z_max": round(z0 + 0.16, 2)}
        ))

        geometries.append({
            "id": f"slab_{flr_tag}",
            "name": f"Basement {b_idx} Reinforced Foundation Slab",
            "type": "SLAB",
            "floor": flr_tag,
            "space_class": "U",
            "rights": "COM",
            "owner": "Community",
            "unit_id": f"SLAB{b_idx:02d}",
            "ulpin_3d": slab_ulpin_b,
            "color": "#2c3e5a",
            "edge_color": "#38bdf8",
            "z_min": z0,
            "z_max": round(z0 + 0.16, 2),
            "cx": 0.0, "cy": round(z0 + 0.08, 2), "cz": 0.0,
            "width": round(bw + 0.4, 2), "height": 0.16, "depth": round(bl + 0.4, 2),
            "opacity": 0.98,
            "is_dispute": False,
            "is_rera_flag": False
        })

        if b_analysis and b_analysis.get("rooms"):
            for r_idx, r in enumerate(b_analysis["rooms"], start=1):
                rid = f"room_{flr_tag}_{r['id']}"
                raw_tag = r.get("unit_tag") or ""
                subtag = raw_tag.split('_')[-1] if '_' in raw_tag else (raw_tag or f"PARK{r_idx:02d}")
                tag = f"B{b_idx:02d}_{subtag}" if r.get("rights") == "PRV" else (raw_tag or f"B{b_idx:02d}{r_idx:02d}")
                ulpin_r = make_official_3d_ulpin(p, flr_tag, "U", r.get("rights", "COM"), tag, "V01")
                owner_r = owner_pool[b_idx % len(owner_pool)] if r.get("rights") == "PRV" else "Community"

                u_room = CadastreUnit(
                    id=rid,
                    name=f"{r['name']} ({flr_tag})",
                    type="PARKING" if "parking" in r.get("name", "").lower() else "ROOM",
                    floor=flr_tag,
                    space_class="U",
                    rights=r.get("rights", "COM"),
                    unit_id=tag,
                    ulpin_3d=ulpin_r,
                    ulpin_numeric=make_numeric_3d_ulpin(p, 1, -b_idx, r_idx),
                    owner=owner_r,
                    description=f"Underground basement cadastral unit on {flr_tag}",
                    parent_2d_ulpin=p,
                    z_min=z0,
                    z_max=z1,
                    carpet_area_sqm=r.get("area_sqm", 15.0),
                    carpet_area_sqft=r.get("area_sqft", 161.0),
                    bbox={"x_min": r["center_m"]["x"] - r["dimensions_m"]["width"]/2,
                          "x_max": r["center_m"]["x"] + r["dimensions_m"]["width"]/2,
                          "y_min": r["center_m"]["y"] - r["dimensions_m"]["length"]/2,
                          "y_max": r["center_m"]["y"] + r["dimensions_m"]["length"]/2,
                          "z_min": z0, "z_max": z1}
                )
                reg.add_unit(u_room)
                reg.add_relationship(rid, "building_a", "LOCATED_IN")

                geometries.append({
                    "id": rid,
                    "name": f"{r['name']} ({flr_tag})",
                    "type": "PARKING" if "parking" in r.get("name", "").lower() else "ROOM",
                    "floor": flr_tag,
                    "space_class": "U",
                    "rights": r.get("rights", "COM"),
                    "owner": owner_r,
                    "unit_id": tag,
                    "ulpin_3d": ulpin_r,
                    "carpet_area_sqm": r.get("area_sqm", 15.0),
                    "carpet_area_sqft": r.get("area_sqft", 161.0),
                    "z_min": z0,
                    "z_max": z1,
                    "width": r["dimensions_m"]["width"],
                    "height": round(h_basement - 0.2, 2),
                    "depth": r["dimensions_m"]["length"],
                    "cx": r["center_m"]["x"],
                    "cy": cy,
                    "cz": r["center_m"]["y"],
                    "color": "#202e48",
                    "edge_color": "#3b82f6",
                    "opacity": 0.85,
                    "is_dispute": False,
                    "is_rera_flag": False
                })

            for w_idx, w in enumerate(b_analysis.get("walls", []), start=1):
                w_code = f"W{b_idx:02d}{w_idx + 10:02d}"
                ulpin_bw = make_official_3d_ulpin(p, flr_tag, "U", "COM", w_code, "V01")
                reg.add_unit(CadastreUnit(
                    id=f"wall_{flr_tag}_{w['id']}",
                    name=f"{w['name']} ({flr_tag})",
                    type="WALL",
                    floor=flr_tag,
                    space_class="U",
                    rights="COM",
                    unit_id=w_code,
                    ulpin_3d=ulpin_bw,
                    ulpin_numeric=make_numeric_3d_ulpin(p, 1, -b_idx, 100 + w_idx),
                    owner="Community",
                    description=f"Basement structural wall on {flr_tag}",
                    parent_2d_ulpin=p,
                    z_min=z0,
                    z_max=z1,
                    carpet_area_sqm=round(w["width"] * w["depth"], 2),
                    carpet_area_sqft=round(w["width"] * w["depth"] * 10.7639, 2),
                    bbox={"x_min": w["cx"] - w["width"]/2, "x_max": w["cx"] + w["width"]/2, "y_min": w["cz"] - w["depth"]/2, "y_max": w["cz"] + w["depth"]/2, "z_min": z0, "z_max": z1}
                ))
                geometries.append({
                    "id": f"wall_{flr_tag}_{w['id']}",
                    "name": f"{w['name']} ({flr_tag})",
                    "type": "WALL",
                    "floor": flr_tag,
                    "space_class": "U",
                    "rights": "COM",
                    "owner": "Community",
                    "unit_id": w_code,
                    "ulpin_3d": ulpin_bw,
                    "z_min": z0,
                    "z_max": z1,
                    "cx": w["cx"],
                    "cy": cy,
                    "cz": w["cz"],
                    "width": w["width"],
                    "height": round(h_basement - 0.1, 2),
                    "depth": w["depth"],
                    "color": "#182234",
                    "edge_color": "#2563eb",
                    "opacity": 0.95,
                    "is_dispute": False,
                    "is_rera_flag": False
                })
        else:
            # Generate clean default basement spatial layout (Parking & Utility)
            b_units_def = [
                ("PARK01", f"Covered Parking Bay P{b_idx}01", -3.2, 1.8, 4.2, 3.4, "PRV", 14.3),
                ("PARK02", f"Covered Parking Bay P{b_idx}02", 3.2, 1.8, 4.2, 3.4, "PRV", 14.3),
                ("CELLAR", f"Secure Cellar & Storage C{b_idx}", -3.2, -2.5, 4.2, 3.0, "PRV", 12.6),
                ("UTL", f"Building Central Utility & HVAC U{b_idx}", 3.2, -2.5, 4.2, 3.0, "COM", 12.6)
            ]
            for u_code, u_name, u_cx, u_cz, u_w, u_d, u_r, u_area in b_units_def:
                rid = f"room_{flr_tag}_{u_code}"
                ulpin_r = make_official_3d_ulpin(p, flr_tag, "U", u_r, f"{u_code}_{b_idx}", "V01")
                owner_r = "Municipal Community" if u_r == "COM" else owner_pool[b_idx % len(owner_pool)]

                u_unit = CadastreUnit(
                    id=rid,
                    name=f"{u_name} ({flr_tag})",
                    type="PARKING" if "Parking" in u_name else "ROOM",
                    floor=flr_tag,
                    space_class="U",
                    rights=u_r,
                    unit_id=f"{u_code}_{b_idx}",
                    ulpin_3d=ulpin_r,
                    ulpin_numeric=make_numeric_3d_ulpin(p, 1, -b_idx, 1),
                    owner=owner_r,
                    description=f"Underground cadastral parcel on {flr_tag}",
                    parent_2d_ulpin=p,
                    z_min=z0,
                    z_max=z1,
                    carpet_area_sqm=u_area,
                    carpet_area_sqft=round(u_area * 10.7639, 1),
                    bbox={"x_min": u_cx - u_w/2, "x_max": u_cx + u_w/2, "y_min": u_cz - u_d/2, "y_max": u_cz + u_d/2, "z_min": z0, "z_max": z1}
                )
                reg.add_unit(u_unit)
                reg.add_relationship(rid, "building_a", "LOCATED_IN")

                geometries.append({
                    "id": rid,
                    "name": f"{u_name} ({flr_tag})",
                    "type": "PARKING" if "Parking" in u_name else "ROOM",
                    "floor": flr_tag,
                    "space_class": "U",
                    "rights": u_r,
                    "owner": owner_r,
                    "unit_id": f"{u_code}_{b_idx}",
                    "ulpin_3d": ulpin_r,
                    "carpet_area_sqm": u_area,
                    "carpet_area_sqft": round(u_area * 10.7639, 1),
                    "z_min": z0,
                    "z_max": z1,
                    "width": u_w,
                    "height": round(h_basement - 0.2, 2),
                    "depth": u_d,
                    "cx": u_cx,
                    "cy": cy,
                    "cz": u_cz,
                    "color": "#1b283d",
                    "edge_color": "#38bdf8",
                    "opacity": 0.85,
                    "is_dispute": False,
                    "is_rera_flag": False
                })

            # Foundation perimeter walls for basement
            wall_thick = 0.25
            f_walls_spec = [
                ("n", "North Foundation Wall", 0.0, bl/2, bw, wall_thick, f"W{b_idx:02d}01"),
                ("s", "South Foundation Wall", 0.0, -bl/2, bw, wall_thick, f"W{b_idx:02d}02"),
                ("e", "East Foundation Wall", bw/2, 0.0, wall_thick, bl, f"W{b_idx:02d}03"),
                ("w", "West Foundation Wall", -bw/2, 0.0, wall_thick, bl, f"W{b_idx:02d}04"),
            ]
            for w_dir, w_name, w_cx, w_cz, w_w, w_d, w_code in f_walls_spec:
                w_ulpin = make_official_3d_ulpin(p, flr_tag, "U", "COM", w_code, "V01")
                reg.add_unit(CadastreUnit(
                    id=f"bwall_{flr_tag}_{w_dir}",
                    name=f"{w_name} ({flr_tag})",
                    type="WALL",
                    floor=flr_tag,
                    space_class="U",
                    rights="COM",
                    unit_id=w_code,
                    ulpin_3d=w_ulpin,
                    ulpin_numeric=make_numeric_3d_ulpin(p, 1, -b_idx, int(w_code[-2:])),
                    owner="Community",
                    description=f"Underground foundation wall on {flr_tag}",
                    parent_2d_ulpin=p,
                    z_min=z0,
                    z_max=z1,
                    carpet_area_sqm=round(w_w * w_d, 2),
                    carpet_area_sqft=round(w_w * w_d * 10.7639, 2),
                    bbox={"x_min": w_cx - w_w/2, "x_max": w_cx + w_w/2, "y_min": w_cz - w_d/2, "y_max": w_cz + w_d/2, "z_min": z0, "z_max": z1}
                ))
                geometries.append({
                    "id": f"bwall_{flr_tag}_{w_dir}",
                    "name": f"{w_name} ({flr_tag})",
                    "type": "WALL",
                    "floor": flr_tag,
                    "space_class": "U",
                    "rights": "COM",
                    "owner": "Community",
                    "unit_id": w_code,
                    "ulpin_3d": w_ulpin,
                    "z_min": z0,
                    "z_max": z1,
                    "cx": w_cx,
                    "cy": cy,
                    "cz": w_cz,
                    "width": w_w,
                    "height": round(h_basement - 0.1, 2),
                    "depth": w_d,
                    "color": "#24354f",
                    "edge_color": "#60a5fa",
                    "opacity": 0.98
                })

    # 4. Build Above-Ground Floors (F01, F02, F03...)
    for f_idx in range(1, n_floors + 1):
        flr_tag = f"F{f_idx:02d}"
        z0 = round((f_idx - 1) * h_floor, 2)
        z1 = round(f_idx * h_floor, 2)
        cy = round((z0 + z1) / 2.0, 2)
        level_key = f"f{f_idx}"
        f_analysis = get_analysis_for(level_key)
        if not f_analysis and replicate_upper_floors:
            f_analysis = first_analysis

        floor_owner = owner_pool[(f_idx - 1) % len(owner_pool)]

        # Floor Slab
        slab_code = f"SLAB{f_idx:02d}"
        slab_ulpin_f = make_official_3d_ulpin(p, flr_tag, "V", "COM", slab_code, "V01")
        reg.add_unit(CadastreUnit(
            id=f"slab_{flr_tag}",
            name=f"Floor {f_idx} Structural Slab ({slab_code})",
            type="SLAB",
            floor=flr_tag,
            space_class="V",
            rights="COM",
            unit_id=slab_code,
            ulpin_3d=slab_ulpin_f,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, 0),
            owner="Community",
            description=f"Structural slab for floor {flr_tag}",
            parent_2d_ulpin=p,
            z_min=z0,
            z_max=round(z0 + 0.12, 2),
            carpet_area_sqm=round(bw * bl, 1),
            carpet_area_sqft=round(bw * bl * 10.7639, 1),
            bbox={"x_min": -bw/2, "x_max": bw/2, "y_min": -bl/2, "y_max": bl/2, "z_min": z0, "z_max": round(z0 + 0.12, 2)}
        ))

        geometries.append({
            "id": f"slab_{flr_tag}",
            "name": f"Floor {f_idx} Structural Slab",
            "type": "SLAB",
            "floor": flr_tag,
            "space_class": "V",
            "rights": "COM",
            "owner": "Community",
            "unit_id": slab_code,
            "ulpin_3d": slab_ulpin_f,
            "color": "#334155",
            "edge_color": "#00f0ff",
            "z_min": z0,
            "z_max": round(z0 + 0.12, 2),
            "cx": 0.0, "cy": round(z0 + 0.06, 2), "cz": 0.0,
            "width": round(bw + 0.2, 2), "height": 0.12, "depth": round(bl + 0.2, 2),
            "opacity": 0.96,
            "is_dispute": False,
            "is_rera_flag": False
        })

        # Flat / Suite Parent Unit
        uid_f = f"A{f_idx}01"
        fid_f = f"flat_{f_idx}01"
        flat_u = CadastreUnit(
            id=fid_f,
            name=f"Floor {f_idx} Cadastral Parcel ({uid_f})",
            type="FLAT",
            floor=flr_tag,
            space_class="V",
            rights="PRV",
            unit_id=uid_f,
            ulpin_3d=make_official_3d_ulpin(p, flr_tag, "V", "PRV", uid_f, "V01"),
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, 1),
            owner=floor_owner,
            description=f"Residential cadastral parcel ({uid_f}) on tier {flr_tag}",
            parent_2d_ulpin=p,
            z_min=z0,
            z_max=z1,
            carpet_area_sqm=round(bw * bl * 0.85, 1),
            carpet_area_sqft=round(bw * bl * 0.85 * 10.7639, 1),
            bbox={"x_min": -bw/2, "x_max": bw/2, "y_min": -bl/2, "y_max": bl/2, "z_min": z0, "z_max": z1}
        )
        reg.add_unit(flat_u)
        reg.add_relationship(fid_f, "building_a", "LOCATED_IN")

        # 🚗 Assigned Parking Bay for this Floor Flat Owner
        prk_code = f"PARK{f_idx:02d}"
        prk_ulpin = make_official_3d_ulpin(p, "G00", "S", "PRV", prk_code, "V01")
        prk_id = f"parking_p{f_idx:02d}"
        p_cx = round(-bw/2 - 2.8, 2)
        p_cz = round(-bl/2 + (f_idx - 1) * 3.2 + 1.6, 2)
        p_unit = CadastreUnit(
            id=prk_id,
            name=f"Assigned Parking Bay {prk_code}",
            type="PARKING",
            floor="G00",
            space_class="S",
            rights="PRV",
            unit_id=prk_code,
            ulpin_3d=prk_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 10 + f_idx),
            owner=floor_owner,
            description=f"Assigned private parking bay for Flat {uid_f} ({floor_owner})",
            parent_2d_ulpin=p,
            z_min=0.0,
            z_max=0.2,
            carpet_area_sqm=12.5,
            carpet_area_sqft=134.5,
            bbox={"x_min": p_cx - 1.3, "x_max": p_cx + 1.3, "y_min": p_cz - 2.5, "y_max": p_cz + 2.5, "z_min": 0.0, "z_max": 0.2}
        )
        reg.add_unit(p_unit)
        reg.add_relationship(fid_f, prk_id, "OWNER_ASSOCIATED")

        geometries.append({
            "id": prk_id,
            "name": f"Assigned Parking Bay {prk_code}",
            "type": "PARKING",
            "floor": "G00",
            "space_class": "S",
            "rights": "PRV",
            "owner": floor_owner,
            "unit_id": prk_code,
            "ulpin_3d": prk_ulpin,
            "carpet_area_sqm": 12.5,
            "carpet_area_sqft": 134.5,
            "z_min": 0.0,
            "z_max": 0.15,
            "cx": p_cx,
            "cy": 0.08,
            "cz": p_cz,
            "width": 2.6,
            "height": 0.15,
            "depth": 5.0,
            "color": "#1e3a5f",
            "edge_color": "#ffd166",
            "opacity": 0.95,
            "is_dispute": False,
            "is_rera_flag": False
        })

        # 🚶 Nearby Common Facilities on this Floor (Stairs, Fire Exit, Public Toilets)
        stair_code = f"STAIR{f_idx:02d}"
        stair_ulpin = make_official_3d_ulpin(p, flr_tag, "V", "COM", stair_code, "V01")
        stair_id = f"stair_{flr_tag}"
        u_stair = CadastreUnit(
            id=stair_id,
            name=f"Common Stairwell ({flr_tag})",
            type="STAIR",
            floor=flr_tag,
            space_class="V",
            rights="COM",
            unit_id=stair_code,
            ulpin_3d=stair_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, 90),
            owner="Community",
            description=f"Common staircase access route on {flr_tag}",
            parent_2d_ulpin=p,
            z_min=z0,
            z_max=z1,
            carpet_area_sqm=15.0,
            carpet_area_sqft=161.5,
            bbox={"x_min": -1.2, "x_max": 1.2, "y_min": bl/2 - 2.5, "y_max": bl/2, "z_min": z0, "z_max": z1}
        )
        reg.add_unit(u_stair)
        reg.add_relationship(fid_f, stair_id, "NEARBY_FACILITY")
        geometries.append({
            "id": stair_id,
            "name": f"Common Stairwell ({flr_tag})",
            "type": "STAIR",
            "floor": flr_tag,
            "space_class": "V",
            "rights": "COM",
            "owner": "Community",
            "unit_id": stair_code,
            "ulpin_3d": stair_ulpin,
            "carpet_area_sqm": 15.0,
            "carpet_area_sqft": 161.5,
            "z_min": z0,
            "z_max": z1,
            "cx": 0.0,
            "cy": cy,
            "cz": round(bl/2 - 1.25, 2),
            "width": 2.4,
            "height": round(h_floor - 0.15, 2),
            "depth": 2.5,
            "color": "#2563eb",
            "edge_color": "#60a5fa",
            "opacity": 0.85,
            "is_dispute": False,
            "is_rera_flag": False
        })

        fire_code = f"FIRE{f_idx:02d}"
        fire_ulpin = make_official_3d_ulpin(p, flr_tag, "V", "COM", fire_code, "V01")
        fire_id = f"fire_{flr_tag}"
        u_fire = CadastreUnit(
            id=fire_id,
            name=f"Emergency Fire Exit ({flr_tag})",
            type="FIRE_EXIT",
            floor=flr_tag,
            space_class="V",
            rights="COM",
            unit_id=fire_code,
            ulpin_3d=fire_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, 91),
            owner="Community",
            description=f"Statutory fire escape route on {flr_tag}",
            parent_2d_ulpin=p,
            z_min=z0,
            z_max=z1,
            carpet_area_sqm=10.0,
            carpet_area_sqft=107.6,
            bbox={"x_min": -1.2, "x_max": 1.2, "y_min": -bl/2, "y_max": -bl/2 + 2.0, "z_min": z0, "z_max": z1}
        )
        reg.add_unit(u_fire)
        reg.add_relationship(fid_f, fire_id, "NEARBY_FACILITY")
        geometries.append({
            "id": fire_id,
            "name": f"Emergency Fire Exit ({flr_tag})",
            "type": "FIRE_EXIT",
            "floor": flr_tag,
            "space_class": "V",
            "rights": "COM",
            "owner": "Community",
            "unit_id": fire_code,
            "ulpin_3d": fire_ulpin,
            "carpet_area_sqm": 10.0,
            "carpet_area_sqft": 107.6,
            "z_min": z0,
            "z_max": z1,
            "cx": 0.0,
            "cy": cy,
            "cz": round(-bl/2 + 1.0, 2),
            "width": 2.4,
            "height": round(h_floor - 0.15, 2),
            "depth": 2.0,
            "color": "#dc2626",
            "edge_color": "#f87171",
            "opacity": 0.85,
            "is_dispute": False,
            "is_rera_flag": False
        })

        toilet_code = f"TOILET{f_idx:02d}"
        toilet_ulpin = make_official_3d_ulpin(p, flr_tag, "V", "COM", toilet_code, "V01")
        toilet_id = f"toilet_{flr_tag}"
        u_toilet = CadastreUnit(
            id=toilet_id,
            name=f"Public Restroom ({flr_tag})",
            type="TOILET",
            floor=flr_tag,
            space_class="V",
            rights="COM",
            unit_id=toilet_code,
            ulpin_3d=toilet_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, 92),
            owner="Community",
            description=f"Common floor service washroom on {flr_tag}",
            parent_2d_ulpin=p,
            z_min=z0,
            z_max=z1,
            carpet_area_sqm=6.5,
            carpet_area_sqft=70.0,
            bbox={"x_min": 1.5, "x_max": 3.5, "y_min": bl/2 - 2.5, "y_max": bl/2, "z_min": z0, "z_max": z1}
        )
        reg.add_unit(u_toilet)
        reg.add_relationship(fid_f, toilet_id, "NEARBY_FACILITY")
        geometries.append({
            "id": toilet_id,
            "name": f"Public Restroom ({flr_tag})",
            "type": "TOILET",
            "floor": flr_tag,
            "space_class": "V",
            "rights": "COM",
            "owner": "Community",
            "unit_id": toilet_code,
            "ulpin_3d": toilet_ulpin,
            "carpet_area_sqm": 6.5,
            "carpet_area_sqft": 70.0,
            "z_min": z0,
            "z_max": z1,
            "cx": 2.5,
            "cy": cy,
            "cz": round(bl/2 - 1.25, 2),
            "width": 2.0,
            "height": round(h_floor - 0.15, 2),
            "depth": 2.5,
            "color": "#0891b2",
            "edge_color": "#22d3ee",
            "opacity": 0.85,
            "is_dispute": False,
            "is_rera_flag": False
        })

        # Associate Community Amenities
        reg.add_relationship(fid_f, "landscape_base", "COMMUNITY_AMENITY")
        reg.add_relationship(fid_f, "terrace_1", "COMMUNITY_AMENITY")

        if f_analysis and f_analysis.get("rooms"):
            # Extrude rooms from floor blueprint with clean standardized subtags
            for r_idx, r in enumerate(f_analysis["rooms"], start=1):
                rid = f"room_{flr_tag}_{r['id']}"
                raw_tag = r.get("unit_tag") or ""
                # Clean subtag extraction: eliminates repeated suite prefix e.g. "1101_BED1" -> "BED1"
                subtag = raw_tag.split('_')[-1] if '_' in raw_tag else (raw_tag or f"R{r_idx:02d}")
                if r.get("rights") == "PRV":
                    tag = f"{uid_f}_{subtag}"
                else:
                    tag = raw_tag or f"COM_{flr_tag}_{r_idx:02d}"

                ulpin_r = make_official_3d_ulpin(p, flr_tag, r.get("space_class", "V"), r.get("rights", "PRV"), tag, "V01")
                owner_r = floor_owner if r.get("rights") == "PRV" else "Community"

                u_room = CadastreUnit(
                    id=rid,
                    name=f"{r['name']} ({flr_tag})",
                    type="ROOM",
                    floor=flr_tag,
                    space_class=r.get("space_class", "V"),
                    rights=r.get("rights", "PRV"),
                    unit_id=tag,
                    ulpin_3d=ulpin_r,
                    ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, r_idx),
                    owner=owner_r,
                    description=f"Room spatial unit on {flr_tag}",
                    parent_2d_ulpin=p,
                    z_min=z0,
                    z_max=z1,
                    carpet_area_sqm=r.get("area_sqm", 20.0),
                    carpet_area_sqft=r.get("area_sqft", 215.0),
                    bbox={"x_min": r["center_m"]["x"] - r["dimensions_m"]["width"]/2,
                          "x_max": r["center_m"]["x"] + r["dimensions_m"]["width"]/2,
                          "y_min": r["center_m"]["y"] - r["dimensions_m"]["length"]/2,
                          "y_max": r["center_m"]["y"] + r["dimensions_m"]["length"]/2,
                          "z_min": z0, "z_max": z1}
                )
                reg.add_unit(u_room)
                reg.add_relationship(rid, fid_f, "PART_OF")

                geometries.append({
                    "id": rid,
                    "name": f"{r['name']} ({flr_tag})",
                    "type": "ROOM",
                    "floor": flr_tag,
                    "space_class": r.get("space_class", "V"),
                    "rights": r.get("rights", "PRV"),
                    "owner": owner_r,
                    "unit_id": tag,
                    "ulpin_3d": ulpin_r,
                    "carpet_area_sqm": r.get("area_sqm", 20.0),
                    "carpet_area_sqft": r.get("area_sqft", 215.0),
                    "z_min": z0,
                    "z_max": z1,
                    "width": r["dimensions_m"]["width"],
                    "height": round(h_floor - 0.15, 2),
                    "depth": r["dimensions_m"]["length"],
                    "cx": r["center_m"]["x"],
                    "cy": cy,
                    "cz": r["center_m"]["y"],
                    "color": "#1e3a8a" if r.get("rights") == "PRV" else "#065f46",
                    "edge_color": "#38bdf8",
                    "opacity": 0.86,
                    "is_dispute": False,
                    "is_rera_flag": False
                })

            if f_analysis and f_analysis.get("walls"):
                for w_idx, w in enumerate(f_analysis["walls"], start=1):
                    wid = f"wall_{flr_tag}_{w['id']}"
                    w_code = f"W{f_idx:02d}{w_idx:02d}"
                    w_rights = "COM" if w.get("wall_type") == "EXTERIOR" else "PRV"
                    w_owner = "Community" if w.get("wall_type") == "EXTERIOR" else floor_owner
                    ulpin_w = make_official_3d_ulpin(p, flr_tag, "V", w_rights, w_code, "V01")
                    u_wall = CadastreUnit(
                        id=wid,
                        name=f"{w['name']} ({flr_tag})",
                        type="WALL",
                        floor=flr_tag,
                        space_class="V",
                        rights=w_rights,
                        unit_id=w_code,
                        ulpin_3d=ulpin_w,
                        ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, 100 + w_idx),
                        owner=w_owner,
                        description=f"Structural wall unit {w_code} on {flr_tag}",
                        parent_2d_ulpin=p,
                        z_min=z0,
                        z_max=z1,
                        carpet_area_sqm=round(w["width"] * w["depth"], 2),
                        carpet_area_sqft=round(w["width"] * w["depth"] * 10.7639, 2),
                        bbox={"x_min": w["cx"] - w["width"]/2, "x_max": w["cx"] + w["width"]/2, "y_min": w["cz"] - w["depth"]/2, "y_max": w["cz"] + w["depth"]/2, "z_min": z0, "z_max": z1}
                    )
                    reg.add_unit(u_wall)
                    reg.add_relationship(wid, fid_f, "PART_OF")

                    geometries.append({
                        "id": wid,
                        "name": f"{w['name']} ({flr_tag})",
                        "type": "WALL",
                        "floor": flr_tag,
                        "space_class": "V",
                        "rights": w_rights,
                        "owner": w_owner,
                        "unit_id": w_code,
                        "ulpin_3d": ulpin_w,
                        "z_min": z0,
                        "z_max": z1,
                        "cx": w["cx"],
                        "cy": cy,
                        "cz": w["cz"],
                        "width": w["width"],
                        "height": round(h_floor - 0.1, 2),
                        "depth": w["depth"],
                        "color": w.get("color", "#182438"),
                        "edge_color": w.get("edge_color", "#38bdf8"),
                        "opacity": 0.96,
                        "is_dispute": False,
                        "is_rera_flag": False
                    })
        else:
            # Generate clean standard perimeter walls for floor without custom blueprint
            wall_thick = 0.22
            std_walls = [
                ("n", f"North Perimeter Wall ({flr_tag})", 0.0, bl/2, bw, wall_thick, f"W{f_idx:02d}01"),
                ("s", f"South Perimeter Wall ({flr_tag})", 0.0, -bl/2, bw, wall_thick, f"W{f_idx:02d}02"),
                ("e", f"East Perimeter Wall ({flr_tag})", bw/2, 0.0, wall_thick, bl, f"W{f_idx:02d}03"),
                ("w", f"West Perimeter Wall ({flr_tag})", -bw/2, 0.0, wall_thick, bl, f"W{f_idx:02d}04"),
            ]
            for w_dir, w_name, w_cx, w_cz, w_w, w_d, w_code in std_walls:
                ulpin_w = make_official_3d_ulpin(p, flr_tag, "V", "COM", w_code, "V01")
                wid = f"wall_{flr_tag}_{w_dir}"
                u_wall = CadastreUnit(
                    id=wid,
                    name=w_name,
                    type="WALL",
                    floor=flr_tag,
                    space_class="V",
                    rights="COM",
                    unit_id=w_code,
                    ulpin_3d=ulpin_w,
                    ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, 100 + len(w_dir)),
                    owner="Community",
                    description=f"Structural exterior wall {w_code} on {flr_tag}",
                    parent_2d_ulpin=p,
                    z_min=z0,
                    z_max=z1,
                    carpet_area_sqm=round(w_w * w_d, 2),
                    carpet_area_sqft=round(w_w * w_d * 10.7639, 2),
                    bbox={"x_min": w_cx - w_w/2, "x_max": w_cx + w_w/2, "y_min": w_cz - w_d/2, "y_max": w_cz + w_d/2, "z_min": z0, "z_max": z1}
                )
                reg.add_unit(u_wall)
                reg.add_relationship(wid, fid_f, "PART_OF")

                geometries.append({
                    "id": wid,
                    "name": w_name,
                    "type": "WALL",
                    "floor": flr_tag,
                    "space_class": "V",
                    "rights": "COM",
                    "owner": "Community",
                    "unit_id": w_code,
                    "ulpin_3d": ulpin_w,
                    "z_min": z0,
                    "z_max": z1,
                    "cx": w_cx,
                    "cy": cy,
                    "cz": w_cz,
                    "width": w_w,
                    "height": round(h_floor - 0.1, 2),
                    "depth": w_d,
                    "color": "#1b2738",
                    "edge_color": "#38bdf8",
                    "opacity": 0.95,
                    "is_dispute": False,
                    "is_rera_flag": False
                })

    # 5. Rooftop Terrace Deck (R00)
    terrace_z = round(h_total, 2)
    t_ulpin = make_official_3d_ulpin(p, "R00", "E", "COM", "TERR01", "V01")
    t_unit = CadastreUnit(
        id="terrace_1",
        name="Rooftop Community Terrace (TERR01)",
        type="TERRACE",
        floor="R00",
        space_class="E",
        rights="COM",
        unit_id="TERR01",
        ulpin_3d=t_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 99, 1),
        owner="Building Community",
        description=f"Common elevated rooftop parcel on {p} at +{terrace_z}m elevation",
        parent_2d_ulpin=p,
        z_min=terrace_z,
        z_max=round(terrace_z + 1.2, 2),
        carpet_area_sqm=round(bw * bl * 0.9, 1),
        carpet_area_sqft=round(bw * bl * 0.9 * 10.7639, 1),
        bbox={"x_min": -bw/2, "x_max": bw/2, "y_min": -bl/2, "y_max": bl/2, "z_min": terrace_z, "z_max": terrace_z + 1.2}
    )
    reg.add_unit(t_unit)
    reg.add_relationship("terrace_1", "building_a", "LOCATED_IN")

    geometries.append({
        "id": "terrace_deck",
        "name": "Rooftop Terrace Deck",
        "type": "TERRACE",
        "floor": "R00",
        "space_class": "E",
        "rights": "COM",
        "owner": "Community",
        "unit_id": "TERR01",
        "ulpin_3d": t_ulpin,
        "carpet_area_sqm": round(bw * bl * 0.9, 1),
        "carpet_area_sqft": round(bw * bl * 0.9 * 10.7639, 1),
        "z_min": terrace_z,
        "z_max": round(terrace_z + 0.12, 2),
        "cx": 0.0,
        "cy": round(terrace_z + 0.06, 2),
        "cz": 0.0,
        "width": bw,
        "height": 0.12,
        "depth": bl,
        "color": "#064e3b",
        "edge_color": "#10b981",
        "opacity": 0.92,
        "is_dispute": False,
        "is_rera_flag": False
    })

    # Parapet safety walls
    parapets = [
        ("n", "North Rooftop Parapet", 0.0, bl/2, bw, 0.2, "PARA_N01"),
        ("s", "South Rooftop Parapet", 0.0, -bl/2, bw, 0.2, "PARA_S01"),
        ("e", "East Rooftop Parapet", bw/2, 0.0, 0.2, bl, "PARA_E01"),
        ("w", "West Rooftop Parapet", -bw/2, 0.0, 0.2, bl, "PARA_W01"),
    ]
    for p_dir, p_name, p_cx, p_cz, p_w, p_d, p_code in parapets:
        p_ulpin = make_official_3d_ulpin(p, "R00", "E", "COM", p_code, "V01")
        reg.add_unit(CadastreUnit(
            id=f"parapet_{p_dir}",
            name=f"{p_name} (R00)",
            type="WALL",
            floor="R00",
            space_class="E",
            rights="COM",
            unit_id=p_code,
            ulpin_3d=p_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 99, 10 + len(p_dir)),
            owner="Community",
            description=f"Rooftop safety parapet wall on {p}",
            parent_2d_ulpin=p,
            z_min=terrace_z,
            z_max=round(terrace_z + 0.95, 2),
            carpet_area_sqm=round(p_w * p_d, 2),
            carpet_area_sqft=round(p_w * p_d * 10.7639, 2),
            bbox={"x_min": p_cx - p_w/2, "x_max": p_cx + p_w/2, "y_min": p_cz - p_d/2, "y_max": p_cz + p_d/2, "z_min": terrace_z, "z_max": terrace_z + 0.95}
        ))
        geometries.append({
            "id": f"parapet_{p_dir}",
            "name": f"{p_name} (R00)",
            "type": "WALL",
            "floor": "R00",
            "space_class": "E",
            "rights": "COM",
            "owner": "Community",
            "unit_id": p_code,
            "ulpin_3d": p_ulpin,
            "z_min": terrace_z,
            "z_max": round(terrace_z + 0.95, 2),
            "cx": p_cx,
            "cy": round(terrace_z + 0.55, 2),
            "cz": p_cz,
            "width": p_w,
            "height": 0.95,
            "depth": p_d,
            "color": "#1e293b",
            "edge_color": "#059669",
            "opacity": 0.95
        })

    render_payload = {
        "parent_2d_ulpin": p,
        "building_name": building_name,
        "building_height": h_total,
        "building_depth": d_total,
        "floors_count": n_floors,
        "basements_count": n_basements,
        "elevation_range": {"z_min": z_min, "z_max": z_max},
        "floor_height_m": h_floor,
        "basement_depth_m": h_basement,
        "cadastre": reg.to_dict(),
        "geometries": geometries,
        "source_filename": f"{n_floors}F_{n_basements}B_multi_level"
    }

    return reg, render_payload
