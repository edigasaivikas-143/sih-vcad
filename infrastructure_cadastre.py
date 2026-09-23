"""
V-CAD Specialized Government, Railway, Road, and Civic Infrastructure Cadastre Module
Provides organized 3D cadastre generators with official 3D ULPINs compliant with SVAMITVA / LADM:
1. Railway Infrastructure (Dual tracks, sleepers, ballast bed, station terminal, platforms, canopies, Foot-Over-Bridge).
2. Road & Highway Network (Multi-lane carriageway, median dividers, lane markings, zebra crossings, sidewalks, streetlights).
3. Statues & Civic Monuments (Stepped granite plinth, pedestal, commemorative statue/monolith, memorial plaza, flagmast).
4. Government Administrative Spaces (Multi-wing Secretariat, District Collectorate, Citizen Seva Kendra, Police Outpost).
5. Integrated Master Town Cadastre (Coordinated multi-sector layout with zero collisions and anti-clutter layer tagging).
"""

from __future__ import annotations
import math
from typing import Dict, List, Tuple, Any, Optional
from ulpin_engine import (
    CadastreRegistry, CadastreUnit, make_official_3d_ulpin, make_numeric_3d_ulpin,
    normalize_2d_ulpin, DEFAULT_PARENT_ULPIN
)


# ==============================================================================
# 1. RAILWAY INFRASTRUCTURE CADASTRE GENERATOR
# ==============================================================================

def build_railway_cadastre(
    parent_ulpin: str = "28045678901234",
    station_name: str = "Central Junction Railway Station",
    track_length_m: float = 120.0
) -> Tuple[CadastreRegistry, Dict[str, Any]]:
    """
    Constructs high-fidelity 3D Railway Infrastructure:
    - Dual broad-gauge tracks (UP Line and DOWN Line)
    - Crushed stone ballast bed & concrete sleepers
    - Station building (G+2 concourse, ticketing, administration)
    - High-level boarding platforms (Platform 1 & 2) with weather sheds
    - Elevated Foot-Over-Bridge (FOB) spanning across tracks (Space Class: E)
    - Catenary OHE masts & electrification lines
    """
    p = normalize_2d_ulpin(parent_ulpin)
    reg = CadastreRegistry(p)
    geometries: List[Dict[str, Any]] = []

    half_l = track_length_m / 2.0

    # 1. Ballast Bed Foundation
    ballast_ulpin = make_official_3d_ulpin(p, "G00", "S", "RLW", "BALLAST01", "V01")
    reg.add_unit(CadastreUnit(
        id="rlw_ballast",
        name="Railway Track Ballast Bed (BALLAST01)",
        type="RAILWAY_TRACK",
        floor="G00",
        space_class="S",
        rights="RLW",
        unit_id="BALLAST01",
        ulpin_3d=ballast_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 1),
        owner="Ministry of Railways / Indian Railways",
        description="Crushed stone ballast bed for dual broad-gauge track corridor",
        parent_2d_ulpin=p,
        category="RAILWAY",
        z_min=-0.35, z_max=0.00,
        carpet_area_sqm=round(track_length_m * 12.0, 1),
        carpet_area_sqft=round(track_length_m * 12.0 * 10.7639, 1),
        bbox={"x_min": -6.0, "x_max": 6.0, "y_min": -half_l, "y_max": half_l, "z_min": -0.35, "z_max": 0.00}
    ))
    geometries.append({
        "id": "rlw_ballast",
        "name": "Railway Track Ballast Bed",
        "type": "GROUND_LAND",
        "floor": "LAND",
        "category": "RAILWAY",
        "space_class": "S",
        "rights": "RLW",
        "owner": "Ministry of Railways",
        "unit_id": "BALLAST01",
        "ulpin_3d": ballast_ulpin,
        "color": "#334155",
        "edge_color": "#64748b",
        "z_min": -0.35, "z_max": 0.00,
        "cx": 0.0, "cy": -0.175, "cz": 0.0,
        "width": 12.0, "height": 0.35, "depth": track_length_m,
        "opacity": 0.98
    })

    # 2. UP and DOWN Running Tracks & Sleepers
    # Track UP at X = -2.5m, Track DOWN at X = +2.5m (Broad gauge = 1.676m)
    tracks_def = [
        ("UP", -2.5, "TRK_UP", "Broad Gauge Track 1 (UP Line)"),
        ("DN", 2.5, "TRK_DN", "Broad Gauge Track 2 (DOWN Line)")
    ]

    for t_code, t_x, t_tag, t_name in tracks_def:
        trk_ulpin = make_official_3d_ulpin(p, "G00", "S", "RLW", t_tag, "V01")
        reg.add_unit(CadastreUnit(
            id=f"rlw_track_{t_code}",
            name=f"{t_name} ({t_tag})",
            type="RAILWAY_TRACK",
            floor="G00",
            space_class="S",
            rights="RLW",
            unit_id=t_tag,
            ulpin_3d=trk_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 10 if t_code == "UP" else 11),
            owner="Ministry of Railways / Indian Railways",
            description=f"Running rail line {t_name} on parcel {p}",
            parent_2d_ulpin=p,
            category="RAILWAY",
            z_min=0.00, z_max=0.35,
            carpet_area_sqm=round(track_length_m * 2.2, 1),
            carpet_area_sqft=round(track_length_m * 2.2 * 10.7639, 1),
            bbox={"x_min": t_x - 1.1, "x_max": t_x + 1.1, "y_min": -half_l, "y_max": half_l, "z_min": 0.00, "z_max": 0.35}
        ))

        # Left & Right Steel Rails
        rail_spacing = 0.838  # 1.676 / 2
        for r_side, r_offset in [("L", -rail_spacing), ("R", rail_spacing)]:
            geometries.append({
                "id": f"rail_{t_code}_{r_side}",
                "name": f"Steel Running Rail ({t_code}-{r_side})",
                "type": "WALL",
                "floor": "G00",
                "category": "RAILWAY",
                "space_class": "S",
                "rights": "RLW",
                "owner": "Ministry of Railways",
                "unit_id": f"{t_tag}_{r_side}",
                "ulpin_3d": trk_ulpin,
                "color": "#94a3b8",
                "edge_color": "#00f0ff",
                "z_min": 0.12, "z_max": 0.30,
                "cx": round(t_x + r_offset, 2), "cy": 0.21, "cz": 0.0,
                "width": 0.10, "height": 0.18, "depth": track_length_m,
                "opacity": 0.98
            })

    # Concrete Sleepers (every 2.5m along track corridor)
    num_sleepers = int(track_length_m / 2.5)
    for s_i in range(num_sleepers):
        s_z = round(-half_l + s_i * 2.5 + 1.25, 2)
        for t_code, t_x, t_tag, _ in tracks_def:
            geometries.append({
                "id": f"sleeper_{t_code}_{s_i}",
                "name": f"Prestressed Concrete Sleeper #{s_i}",
                "type": "WALL",
                "floor": "G00",
                "category": "RAILWAY",
                "space_class": "S",
                "rights": "RLW",
                "owner": "Ministry of Railways",
                "unit_id": f"SLP_{t_code}_{s_i:02d}",
                "ulpin_3d": f"{p}-G00-S-RLW-SLP{s_i:02d}-V01",
                "color": "#64748b",
                "edge_color": "#94a3b8",
                "z_min": 0.00, "z_max": 0.12,
                "cx": t_x, "cy": 0.06, "cz": s_z,
                "width": 2.40, "height": 0.12, "depth": 0.28,
                "opacity": 0.95
            })

    # 3. Passenger Platforms (Platform 1 on West, Platform 2 on East)
    platforms_def = [
        ("PLTF01", -9.0, 5.0, "Passenger Platform 1 (Main Side)", "#1e293b", "#38bdf8"),
        ("PLTF02", 9.0, 5.0, "Passenger Platform 2 (Island Side)", "#1e293b", "#38bdf8")
    ]

    for plt_tag, plt_x, plt_w, plt_name, plt_col, plt_edge in platforms_def:
        plt_ulpin = make_official_3d_ulpin(p, "G00", "S", "RLW", plt_tag, "V01")
        reg.add_unit(CadastreUnit(
            id=f"rlw_{plt_tag.lower()}",
            name=f"{plt_name} ({plt_tag})",
            type="PLATFORM",
            floor="G00",
            space_class="S",
            rights="RLW",
            unit_id=plt_tag,
            ulpin_3d=plt_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 20 if "1" in plt_tag else 21),
            owner="Ministry of Railways / Indian Railways",
            description=f"High-level passenger platform with tactile paving on {p}",
            parent_2d_ulpin=p,
            category="RAILWAY",
            z_min=0.00, z_max=0.85,
            carpet_area_sqm=round(track_length_m * 0.8 * plt_w, 1),
            carpet_area_sqft=round(track_length_m * 0.8 * plt_w * 10.7639, 1),
            bbox={"x_min": plt_x - plt_w/2, "x_max": plt_x + plt_w/2, "y_min": -half_l * 0.8, "y_max": half_l * 0.8, "z_min": 0.00, "z_max": 0.85}
        ))

        # Platform Slab
        geometries.append({
            "id": f"rlw_{plt_tag.lower()}",
            "name": plt_name,
            "type": "ROOM",
            "floor": "G00",
            "category": "RAILWAY",
            "space_class": "S",
            "rights": "RLW",
            "owner": "Ministry of Railways",
            "unit_id": plt_tag,
            "ulpin_3d": plt_ulpin,
            "color": plt_col,
            "edge_color": plt_edge,
            "z_min": 0.00, "z_max": 0.85,
            "cx": plt_x, "cy": 0.425, "cz": 0.0,
            "width": plt_w, "height": 0.85, "depth": round(track_length_m * 0.8, 2),
            "opacity": 0.96
        })

        # Platform Canopy / Weather Shelter
        canopy_ulpin = make_official_3d_ulpin(p, "F01", "E", "RLW", f"{plt_tag}_SHED", "V01")
        geometries.append({
            "id": f"shed_{plt_tag.lower()}",
            "name": f"Platform Canopy Shed ({plt_tag})",
            "type": "SLAB",
            "floor": "F01",
            "category": "RAILWAY",
            "space_class": "E",
            "rights": "RLW",
            "owner": "Ministry of Railways",
            "unit_id": f"{plt_tag}_SHED",
            "ulpin_3d": canopy_ulpin,
            "color": "#1e3a8a",
            "edge_color": "#60a5fa",
            "z_min": 4.5, "z_max": 4.8,
            "cx": plt_x, "cy": 4.65, "cz": 0.0,
            "width": plt_w + 1.2, "height": 0.20, "depth": round(track_length_m * 0.5, 2),
            "opacity": 0.90
        })

    # 4. Elevated Foot-Over-Bridge (FOB) across tracks
    fob_ulpin = make_official_3d_ulpin(p, "F02", "E", "RLW", "FOB01", "V01")
    reg.add_unit(CadastreUnit(
        id="rlw_fob",
        name="Station Foot-Over-Bridge (FOB01)",
        type="STAIR",
        floor="F02",
        space_class="E",
        rights="RLW",
        unit_id="FOB01",
        ulpin_3d=fob_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 2, 1),
        owner="Ministry of Railways / Indian Railways",
        description="Elevated pedestrian foot-over-bridge connecting Platform 1 and Platform 2",
        parent_2d_ulpin=p,
        category="RAILWAY",
        z_min=5.80, z_max=8.20,
        carpet_area_sqm=90.0,
        carpet_area_sqft=968.7,
        bbox={"x_min": -11.5, "x_max": 11.5, "y_min": -2.5, "y_max": 2.5, "z_min": 5.80, "z_max": 8.20}
    ))
    # FOB Walkway Span
    geometries.append({
        "id": "rlw_fob_span",
        "name": "Elevated Foot-Over-Bridge Span",
        "type": "ROOM",
        "floor": "F02",
        "category": "RAILWAY",
        "space_class": "E",
        "rights": "RLW",
        "owner": "Ministry of Railways",
        "unit_id": "FOB01",
        "ulpin_3d": fob_ulpin,
        "color": "#1e40af",
        "edge_color": "#38bdf8",
        "z_min": 5.80, "z_max": 6.10,
        "cx": 0.0, "cy": 5.95, "cz": 0.0,
        "width": 24.0, "height": 0.30, "depth": 4.5,
        "opacity": 0.95
    })
    # FOB Left & Right Stair Towers
    for fob_side, fob_x in [("W", -11.0), ("E", 11.0)]:
        geometries.append({
            "id": f"fob_stair_{fob_side}",
            "name": f"FOB Stairway Access ({fob_side})",
            "type": "STAIR",
            "floor": "F01",
            "category": "RAILWAY",
            "space_class": "V",
            "rights": "RLW",
            "owner": "Ministry of Railways",
            "unit_id": f"FOB_STR_{fob_side}",
            "ulpin_3d": fob_ulpin,
            "color": "#1d4ed8",
            "edge_color": "#ffd166",
            "z_min": 0.85, "z_max": 5.80,
            "cx": fob_x, "cy": 3.325, "cz": 0.0,
            "width": 3.0, "height": 4.95, "depth": 4.5,
            "opacity": 0.92
        })

    # 5. Main Station Terminal Building (Adjacent to Platform 1)
    stn_bldg_ulpin = make_official_3d_ulpin(p, "F01", "V", "RLW", "STN_MAIN", "V01")
    reg.add_unit(CadastreUnit(
        id="rlw_station_terminal",
        name=f"{station_name} Terminal Building",
        type="BUILDING",
        floor="F01-F03",
        space_class="V",
        rights="RLW",
        unit_id="STN_MAIN",
        ulpin_3d=stn_bldg_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 1, 1),
        owner="Ministry of Railways / Indian Railways",
        description=f"Unified station terminal building (Concourse, Ticketing, Control) on {p}",
        parent_2d_ulpin=p,
        category="RAILWAY",
        z_min=0.0, z_max=11.5,
        carpet_area_sqm=1200.0,
        carpet_area_sqft=12916.7,
        bbox={"x_min": -28.0, "x_max": -12.0, "y_min": -15.0, "y_max": 15.0, "z_min": 0.0, "z_max": 11.5}
    ))
    # Terminal Building Geometry
    geometries.append({
        "id": "rlw_station_terminal",
        "name": f"{station_name} Concourse & Terminal",
        "type": "ROOM",
        "floor": "F01",
        "category": "RAILWAY",
        "space_class": "V",
        "rights": "RLW",
        "owner": "Ministry of Railways",
        "unit_id": "STN_MAIN",
        "ulpin_3d": stn_bldg_ulpin,
        "color": "#0f172a",
        "edge_color": "#38bdf8",
        "z_min": 0.0, "z_max": 11.5,
        "cx": -20.0, "cy": 5.75, "cz": 0.0,
        "width": 14.0, "height": 11.5, "depth": 30.0,
        "opacity": 0.95
    })

    # Catenary OHE Masts (Overhead Electrification Poles)
    for m_i in range(5):
        m_z = round(-half_l + m_i * 24.0 + 12.0, 2)
        for m_x, m_id in [(-5.0, "W"), (5.0, "E")]:
            geometries.append({
                "id": f"ohe_mast_{m_i}_{m_id}",
                "name": f"OHE Electrification Mast #{m_i+1}",
                "type": "WALL",
                "floor": "G00",
                "category": "RAILWAY",
                "space_class": "E",
                "rights": "RLW",
                "owner": "Ministry of Railways",
                "unit_id": f"OHE_{m_i}_{m_id}",
                "ulpin_3d": f"{p}-G00-E-RLW-OHE{m_i}-V01",
                "color": "#475569",
                "edge_color": "#00f0ff",
                "z_min": 0.0, "z_max": 7.5,
                "cx": m_x, "cy": 3.75, "cz": m_z,
                "width": 0.35, "height": 7.5, "depth": 0.35,
                "opacity": 0.92
            })

    render_payload = {
        "parent_2d_ulpin": p,
        "building_name": station_name,
        "category": "RAILWAY",
        "building_height": 11.5,
        "building_depth": 0.35,
        "floors_count": 3,
        "basements_count": 0,
        "elevation_range": {"z_min": -0.35, "z_max": 11.5},
        "floor_height_m": 3.8,
        "cadastre": reg.to_dict(),
        "geometries": geometries,
        "source_filename": "railway_infrastructure_cadastre"
    }

    return reg, render_payload


# ==============================================================================
# 2. ROAD NETWORK & HIGHWAY CADASTRE GENERATOR
# ==============================================================================

def build_road_network_cadastre(
    parent_ulpin: str = "28045678901235",
    road_name: str = "Grand Trunk National Arterial Corridor",
    corridor_length_m: float = 120.0
) -> Tuple[CadastreRegistry, Dict[str, Any]]:
    """
    Constructs 3D Road Network Cadastre:
    - 4-lane Asphalt Carriageway with curbs
    - Center median divider with decorative landscaping
    - Crisp white/yellow lane dividing stripes
    - Pedestrian zebra crossing at intersection
    - Elevated pedestrian sidewalks on both sides
    - Modern LED highway street lighting columns
    """
    p = normalize_2d_ulpin(parent_ulpin)
    reg = CadastreRegistry(p)
    geometries: List[Dict[str, Any]] = []

    half_l = corridor_length_m / 2.0
    road_w = 20.0  # Total roadway width including median & lanes

    # 1. Main Asphalt Carriageway
    road_ulpin = make_official_3d_ulpin(p, "G00", "S", "PUB", "ROAD_M01", "V01")
    reg.add_unit(CadastreUnit(
        id="road_carriageway",
        name=f"{road_name} (Carriageway)",
        type="ROAD",
        floor="G00",
        space_class="S",
        rights="PUB",
        unit_id="ROAD_M01",
        ulpin_3d=road_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 1),
        owner="Ministry of Road Transport & Highways / PWD",
        description="Public arterial 4-lane dual carriageway surface parcel",
        parent_2d_ulpin=p,
        category="ROADS",
        z_min=-0.25, z_max=0.00,
        carpet_area_sqm=round(corridor_length_m * road_w, 1),
        carpet_area_sqft=round(corridor_length_m * road_w * 10.7639, 1),
        bbox={"x_min": -road_w/2, "x_max": road_w/2, "y_min": -half_l, "y_max": half_l, "z_min": -0.25, "z_max": 0.00}
    ))
    geometries.append({
        "id": "road_carriageway",
        "name": road_name,
        "type": "GROUND_LAND",
        "floor": "LAND",
        "category": "ROADS",
        "space_class": "S",
        "rights": "PUB",
        "owner": "MoRTH / PWD",
        "unit_id": "ROAD_M01",
        "ulpin_3d": road_ulpin,
        "color": "#1e293b",  # Dark asphalt
        "edge_color": "#475569",
        "z_min": -0.25, "z_max": 0.00,
        "cx": 0.0, "cy": -0.125, "cz": 0.0,
        "width": road_w, "height": 0.25, "depth": corridor_length_m,
        "opacity": 0.98
    })

    # 2. Central Median Barrier / Divider
    median_w = 1.2
    median_ulpin = make_official_3d_ulpin(p, "G00", "S", "PUB", "MEDIAN01", "V01")
    reg.add_unit(CadastreUnit(
        id="road_median",
        name="Highway Central Median Divider (MEDIAN01)",
        type="ROAD",
        floor="G00",
        space_class="S",
        rights="PUB",
        unit_id="MEDIAN01",
        ulpin_3d=median_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 2),
        owner="Ministry of Road Transport & Highways / PWD",
        description="Reinforced concrete central median traffic separator",
        parent_2d_ulpin=p,
        category="ROADS",
        z_min=0.00, z_max=0.45,
        carpet_area_sqm=round(corridor_length_m * median_w, 1),
        carpet_area_sqft=round(corridor_length_m * median_w * 10.7639, 1),
        bbox={"x_min": -median_w/2, "x_max": median_w/2, "y_min": -half_l, "y_max": half_l, "z_min": 0.00, "z_max": 0.45}
    ))
    geometries.append({
        "id": "road_median",
        "name": "Central Median Divider",
        "type": "WALL",
        "floor": "G00",
        "category": "ROADS",
        "space_class": "S",
        "rights": "PUB",
        "owner": "MoRTH / PWD",
        "unit_id": "MEDIAN01",
        "ulpin_3d": median_ulpin,
        "color": "#047857",  # Green landscaped median
        "edge_color": "#ffd166",
        "z_min": 0.00, "z_max": 0.45,
        "cx": 0.0, "cy": 0.225, "cz": 0.0,
        "width": median_w, "height": 0.45, "depth": corridor_length_m,
        "opacity": 0.95
    })

    # 3. White / Yellow Dashed Lane Dividers (Dashes every 6m)
    num_dashes = int(corridor_length_m / 6.0)
    for d_i in range(num_dashes):
        d_z = round(-half_l + d_i * 6.0 + 3.0, 2)
        # Left Lane Divider (X = -5.0m) and Right Lane Divider (X = +5.0m)
        for lx, lside in [(-5.0, "W"), (5.0, "E")]:
            geometries.append({
                "id": f"lane_mark_{lside}_{d_i}",
                "name": f"Road Lane Marking ({lside}-{d_i})",
                "type": "WALL",
                "floor": "G00",
                "category": "ROADS",
                "space_class": "S",
                "rights": "PUB",
                "owner": "MoRTH / PWD",
                "unit_id": f"MARK_{lside}_{d_i:02d}",
                "ulpin_3d": f"{p}-G00-S-PUB-MARK{d_i:02d}-V01",
                "color": "#ffffff",
                "edge_color": "#f8fafc",
                "z_min": 0.00, "z_max": 0.02,
                "cx": lx, "cy": 0.01, "cz": d_z,
                "width": 0.20, "height": 0.02, "depth": 3.5,
                "opacity": 0.99
            })

    # 4. Pedestrian Sidewalks (West and East elevated walkways)
    sidewalk_w = 3.0
    for sw_side, sw_x, sw_code in [("W", -road_w/2 - sidewalk_w/2, "SWALK_W"), ("E", road_w/2 + sidewalk_w/2, "SWALK_E")]:
        sw_ulpin = make_official_3d_ulpin(p, "G00", "S", "PUB", sw_code, "V01")
        reg.add_unit(CadastreUnit(
            id=f"sidewalk_{sw_side.lower()}",
            name=f"Pedestrian Sidewalk ({sw_side} Wing)",
            type="ROAD",
            floor="G00",
            space_class="S",
            rights="PUB",
            unit_id=sw_code,
            ulpin_3d=sw_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 30 if sw_side == "W" else 31),
            owner="Municipal Corporation / Urban Local Body",
            description="Elevated pedestrian paved sidewalk and utility strip",
            parent_2d_ulpin=p,
            category="ROADS",
            z_min=0.00, z_max=0.20,
            carpet_area_sqm=round(corridor_length_m * sidewalk_w, 1),
            carpet_area_sqft=round(corridor_length_m * sidewalk_w * 10.7639, 1),
            bbox={"x_min": sw_x - sidewalk_w/2, "x_max": sw_x + sidewalk_w/2, "y_min": -half_l, "y_max": half_l, "z_min": 0.00, "z_max": 0.20}
        ))
        geometries.append({
            "id": f"sidewalk_{sw_side.lower()}",
            "name": f"Pedestrian Sidewalk ({sw_side})",
            "type": "ROOM",
            "floor": "G00",
            "category": "ROADS",
            "space_class": "S",
            "rights": "PUB",
            "owner": "Municipal Corporation",
            "unit_id": sw_code,
            "ulpin_3d": sw_ulpin,
            "color": "#475569",
            "edge_color": "#94a3b8",
            "z_min": 0.00, "z_max": 0.20,
            "cx": sw_x, "cy": 0.10, "cz": 0.0,
            "width": sidewalk_w, "height": 0.20, "depth": corridor_length_m,
            "opacity": 0.95
        })

    # 5. Pedestrian Zebra Crosswalk at junction (Z = 0)
    for z_i in range(12):
        zx = round(-road_w/2 + 1.2 + z_i * 1.5, 2)
        if abs(zx) < median_w/2 + 0.3:
            continue
        geometries.append({
            "id": f"zebra_stripe_{z_i}",
            "name": f"Pedestrian Zebra Stripe #{z_i}",
            "type": "WALL",
            "floor": "G00",
            "category": "ROADS",
            "space_class": "S",
            "rights": "PUB",
            "owner": "MoRTH / PWD",
            "unit_id": f"ZEBRA_{z_i:02d}",
            "ulpin_3d": f"{p}-G00-S-PUB-ZEBRA01-V01",
            "color": "#f8fafc",
            "edge_color": "#ffd166",
            "z_min": 0.00, "z_max": 0.02,
            "cx": zx, "cy": 0.015, "cz": 0.0,
            "width": 0.60, "height": 0.02, "depth": 4.0,
            "opacity": 0.99
        })

    # 6. Street Lighting Columns
    for pole_i in range(5):
        pz = round(-half_l + pole_i * 24.0 + 12.0, 2)
        for px, pside in [(-road_w/2 - 1.2, "W"), (road_w/2 + 1.2, "E")]:
            geometries.append({
                "id": f"light_pole_{pside}_{pole_i}",
                "name": f"LED Streetlight Mast ({pside}-{pole_i+1})",
                "type": "WALL",
                "floor": "G00",
                "category": "ROADS",
                "space_class": "E",
                "rights": "PUB",
                "owner": "Municipal Corporation",
                "unit_id": f"LGT_{pside}_{pole_i:02d}",
                "ulpin_3d": f"{p}-G00-E-PUB-LIGHT{pole_i:02d}-V01",
                "color": "#94a3b8",
                "edge_color": "#ffd166",
                "z_min": 0.0, "z_max": 7.0,
                "cx": px, "cy": 3.5, "cz": pz,
                "width": 0.25, "height": 7.0, "depth": 0.25,
                "opacity": 0.95
            })

    render_payload = {
        "parent_2d_ulpin": p,
        "building_name": road_name,
        "category": "ROADS",
        "building_height": 7.0,
        "building_depth": 0.25,
        "floors_count": 1,
        "basements_count": 0,
        "elevation_range": {"z_min": -0.25, "z_max": 7.0},
        "floor_height_m": 3.0,
        "cadastre": reg.to_dict(),
        "geometries": geometries,
        "source_filename": "road_network_cadastre"
    }

    return reg, render_payload


# ==============================================================================
# 3. STATUES & CIVIC MONUMENTS CADASTRE GENERATOR
# ==============================================================================

def build_civic_monument_cadastre(
    parent_ulpin: str = "28045678901237",
    monument_name: str = "National Unity Statue & Memorial Plaza"
) -> Tuple[CadastreRegistry, Dict[str, Any]]:
    """
    Constructs 3D Civic Monument Cadastre:
    - Memorial Courtyard & Plaza (Granite paved civic space)
    - 3-tier stepped polished granite ceremonial plinth
    - Architectural monument pedestal with dedication bronze plaque
    - Commemorative Statue / Monolith Column (Total height 9.5m)
    - Ceremonial Flagmast with National flag
    - Perimeter safety bollards & chain railing
    """
    p = normalize_2d_ulpin(parent_ulpin)
    reg = CadastreRegistry(p)
    geometries: List[Dict[str, Any]] = []

    plaza_size = 40.0

    # 1. Memorial Courtyard & Plaza
    plaza_ulpin = make_official_3d_ulpin(p, "G00", "S", "GOV", "MEM_PLAZA", "V01")
    reg.add_unit(CadastreUnit(
        id="monument_plaza",
        name="Civic Memorial Plaza (MEM_PLAZA)",
        type="PARK",
        floor="G00",
        space_class="S",
        rights="GOV",
        unit_id="MEM_PLAZA",
        ulpin_3d=plaza_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 1),
        owner="Municipal Corporation / Government Heritage Dept",
        description="Public civic gathering plaza and ceremonial grounds",
        parent_2d_ulpin=p,
        category="MONUMENTS",
        z_min=-0.15, z_max=0.00,
        carpet_area_sqm=round(plaza_size * plaza_size, 1),
        carpet_area_sqft=round(plaza_size * plaza_size * 10.7639, 1),
        bbox={"x_min": -plaza_size/2, "x_max": plaza_size/2, "y_min": -plaza_size/2, "y_max": plaza_size/2, "z_min": -0.15, "z_max": 0.00}
    ))
    geometries.append({
        "id": "monument_plaza",
        "name": "Ceremonial Memorial Plaza",
        "type": "GROUND_LAND",
        "floor": "LAND",
        "category": "MONUMENTS",
        "space_class": "S",
        "rights": "GOV",
        "owner": "Government Heritage Dept",
        "unit_id": "MEM_PLAZA",
        "ulpin_3d": plaza_ulpin,
        "color": "#1e293b",
        "edge_color": "#d97706",
        "z_min": -0.15, "z_max": 0.00,
        "cx": 0.0, "cy": -0.075, "cz": 0.0,
        "width": plaza_size, "height": 0.15, "depth": plaza_size,
        "opacity": 0.98
    })

    # 2. Stepped 3-Tier Ceremonial Plinth
    plinths = [
        (1, 14.0, 0.45, 0.00, "Tier 1 Base Plinth (Granite)"),
        (2, 10.0, 0.45, 0.45, "Tier 2 Intermediate Plinth"),
        (3, 7.0, 0.45, 0.90, "Tier 3 Upper Plinth Deck")
    ]
    for tier_i, p_w, p_h, p_z0, p_name in plinths:
        t_ulpin = make_official_3d_ulpin(p, "G00", "S", "GOV", f"PLINTH0{tier_i}", "V01")
        reg.add_unit(CadastreUnit(
            id=f"plinth_tier_{tier_i}",
            name=f"{p_name} (PLINTH0{tier_i})",
            type="PLOT",
            floor="G00",
            space_class="S",
            rights="GOV",
            unit_id=f"PLINTH0{tier_i}",
            ulpin_3d=t_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 10 + tier_i),
            owner="Government Heritage Dept",
            description=f"Stepped ceremonial granite plinth tier {tier_i}",
            parent_2d_ulpin=p,
            category="MONUMENTS",
            z_min=p_z0, z_max=p_z0 + p_h,
            carpet_area_sqm=round(p_w * p_w, 1),
            carpet_area_sqft=round(p_w * p_w * 10.7639, 1),
            bbox={"x_min": -p_w/2, "x_max": p_w/2, "y_min": -p_w/2, "y_max": p_w/2, "z_min": p_z0, "z_max": p_z0 + p_h}
        ))
        geometries.append({
            "id": f"plinth_tier_{tier_i}",
            "name": p_name,
            "type": "ROOM",
            "floor": "G00",
            "category": "MONUMENTS",
            "space_class": "S",
            "rights": "GOV",
            "owner": "Government Heritage Dept",
            "unit_id": f"PLINTH0{tier_i}",
            "ulpin_3d": t_ulpin,
            "color": "#334155" if tier_i % 2 == 1 else "#475569",
            "edge_color": "#f59e0b",
            "z_min": p_z0, "z_max": p_z0 + p_h,
            "cx": 0.0, "cy": round(p_z0 + p_h / 2.0, 2), "cz": 0.0,
            "width": p_w, "height": p_h, "depth": p_w,
            "opacity": 0.98
        })

    # 3. Monument Pedestal / Pylon
    ped_z0 = 1.35
    ped_h = 3.20
    ped_ulpin = make_official_3d_ulpin(p, "G00", "S", "GOV", "PEDESTAL01", "V01")
    reg.add_unit(CadastreUnit(
        id="monument_pedestal",
        name="Monument Pedestal & Engraving Pylon (PEDESTAL01)",
        type="WALL",
        floor="G00",
        space_class="S",
        rights="GOV",
        unit_id="PEDESTAL01",
        ulpin_3d=ped_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 20),
        owner="Government Heritage Dept",
        description="Sculpted granite pedestal carrying state emblem and dedication deed",
        parent_2d_ulpin=p,
        category="MONUMENTS",
        z_min=ped_z0, z_max=ped_z0 + ped_h,
        carpet_area_sqm=12.25,
        carpet_area_sqft=131.9,
        bbox={"x_min": -1.75, "x_max": 1.75, "y_min": -1.75, "y_max": 1.75, "z_min": ped_z0, "z_max": ped_z0 + ped_h}
    ))
    geometries.append({
        "id": "monument_pedestal",
        "name": "Monument Pedestal Core",
        "type": "WALL",
        "floor": "G00",
        "category": "MONUMENTS",
        "space_class": "S",
        "rights": "GOV",
        "owner": "Government Heritage Dept",
        "unit_id": "PEDESTAL01",
        "ulpin_3d": ped_ulpin,
        "color": "#1e293b",
        "edge_color": "#d97706",
        "z_min": ped_z0, "z_max": ped_z0 + ped_h,
        "cx": 0.0, "cy": round(ped_z0 + ped_h / 2.0, 2), "cz": 0.0,
        "width": 3.5, "height": ped_h, "depth": 3.5,
        "opacity": 0.98
    })

    # 4. Commemorative Statue / Monolith Figure (Height 4.8m above pedestal)
    statue_z0 = ped_z0 + ped_h
    statue_h = 4.80
    statue_ulpin = make_official_3d_ulpin(p, "F01", "V", "GOV", "STATUE01", "V01")
    reg.add_unit(CadastreUnit(
        id="civic_statue",
        name=f"{monument_name} (STATUE01)",
        type="STATUE",
        floor="F01",
        space_class="V",
        rights="GOV",
        unit_id="STATUE01",
        ulpin_3d=statue_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 1, 99),
        owner="Government Heritage Dept / State Government",
        description=f"Official bronze commemorative monument statue on {p}",
        parent_2d_ulpin=p,
        category="MONUMENTS",
        z_min=statue_z0, z_max=statue_z0 + statue_h,
        carpet_area_sqm=5.0,
        carpet_area_sqft=53.8,
        bbox={"x_min": -1.2, "x_max": 1.2, "y_min": -1.2, "y_max": 1.2, "z_min": statue_z0, "z_max": statue_z0 + statue_h}
    ))
    # Statue Body (Torso & Base)
    geometries.append({
        "id": "civic_statue_body",
        "name": f"{monument_name} (Main Bronze Volume)",
        "type": "ROOM",
        "floor": "F01",
        "category": "MONUMENTS",
        "space_class": "V",
        "rights": "GOV",
        "owner": "Government Heritage Dept",
        "unit_id": "STATUE01",
        "ulpin_3d": statue_ulpin,
        "color": "#d97706",  # Bronze / Gold
        "edge_color": "#ffd166",
        "z_min": statue_z0, "z_max": statue_z0 + statue_h,
        "cx": 0.0, "cy": round(statue_z0 + statue_h / 2.0, 2), "cz": 0.0,
        "width": 2.2, "height": statue_h, "depth": 2.2,
        "opacity": 0.98
    })

    # 5. Ceremonial Flagmast (Height 12m)
    flag_ulpin = make_official_3d_ulpin(p, "F01", "E", "GOV", "FLAGMAST01", "V01")
    geometries.append({
        "id": "ceremonial_flagmast",
        "name": "State Ceremonial Flagmast",
        "type": "WALL",
        "floor": "G00",
        "category": "MONUMENTS",
        "space_class": "E",
        "rights": "GOV",
        "owner": "Government of India",
        "unit_id": "FLAGMAST01",
        "ulpin_3d": flag_ulpin,
        "color": "#f8fafc",
        "edge_color": "#ffd166",
        "z_min": 0.0, "z_max": 12.0,
        "cx": 8.0, "cy": 6.0, "cz": -8.0,
        "width": 0.25, "height": 12.0, "depth": 0.25,
        "opacity": 0.98
    })
    # Flag Geometry
    geometries.append({
        "id": "national_flag_fabric",
        "name": "National Flag Fabric",
        "type": "WALL",
        "floor": "F02",
        "category": "MONUMENTS",
        "space_class": "E",
        "rights": "GOV",
        "owner": "Government of India",
        "unit_id": "FLAG_BANNER",
        "ulpin_3d": flag_ulpin,
        "color": "#ea580c",  # Saffron
        "edge_color": "#16a34a",
        "z_min": 9.5, "z_max": 11.5,
        "cx": 9.4, "cy": 10.5, "cz": -8.0,
        "width": 2.5, "height": 1.6, "depth": 0.05,
        "opacity": 0.98
    })

    total_h = round(statue_z0 + statue_h, 2)
    render_payload = {
        "parent_2d_ulpin": p,
        "building_name": monument_name,
        "category": "MONUMENTS",
        "building_height": total_h,
        "building_depth": 0.15,
        "floors_count": 2,
        "basements_count": 0,
        "elevation_range": {"z_min": -0.15, "z_max": 12.0},
        "floor_height_m": 4.5,
        "cadastre": reg.to_dict(),
        "geometries": geometries,
        "source_filename": "civic_monument_cadastre"
    }

    return reg, render_payload


# ==============================================================================
# 4. GOVERNMENT ADMINISTRATIVE SPACES CADASTRE GENERATOR
# ==============================================================================

def build_govt_spaces_cadastre(
    parent_ulpin: str = "28045678901236",
    complex_name: str = "Government Administrative Secretariat Complex"
) -> Tuple[CadastreRegistry, Dict[str, Any]]:
    """
    Constructs 3D Government Administrative Spaces:
    - Multi-wing Government Secretariat (G+3 Floors)
    - Ground Floor: Citizen Facilitation Center (Seva Kendra) & Central Atrium
    - Floor 1: Land Administration & Cadastre Directorate
    - Floor 2: District Collectorate & Revenue Directorate
    - Floor 3: Cabinet Secretariat & High-level Conference Chambers
    - Civic Public Safety Outpost / Police Station building
    - Courtyard with official state flag plaza
    """
    p = normalize_2d_ulpin(parent_ulpin)
    reg = CadastreRegistry(p)
    geometries: List[Dict[str, Any]] = []

    flr_h = 3.6
    n_floors = 4
    total_h = flr_h * n_floors

    b_width = 36.0
    b_depth = 24.0

    # 1. Base Campus Parcel
    campus_ulpin = make_official_3d_ulpin(p, "G00", "S", "GOV", "CAMPUS01", "V01")
    reg.add_unit(CadastreUnit(
        id="govt_campus",
        name=f"{complex_name} (Civic Campus)",
        type="PARK",
        floor="G00",
        space_class="S",
        rights="GOV",
        unit_id="CAMPUS01",
        ulpin_3d=campus_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 1),
        owner="Government of Andhra Pradesh / General Administration Dept",
        description="Gazetted government administrative campus land parcel",
        parent_2d_ulpin=p,
        category="GOVT_SPACES",
        z_min=-0.20, z_max=0.00,
        carpet_area_sqm=round(b_width * b_depth * 2.2, 1),
        carpet_area_sqft=round(b_width * b_depth * 2.2 * 10.7639, 1),
        bbox={"x_min": -b_width, "x_max": b_width, "y_min": -b_depth, "y_max": b_depth, "z_min": -0.20, "z_max": 0.00}
    ))
    geometries.append({
        "id": "govt_campus",
        "name": "Secretariat Administrative Campus",
        "type": "GROUND_LAND",
        "floor": "LAND",
        "category": "GOVT_SPACES",
        "space_class": "S",
        "rights": "GOV",
        "owner": "General Administration Dept",
        "unit_id": "CAMPUS01",
        "ulpin_3d": campus_ulpin,
        "color": "#0f172a",
        "edge_color": "#1e3a8a",
        "z_min": -0.20, "z_max": 0.00,
        "cx": 0.0, "cy": -0.10, "cz": 0.0,
        "width": b_width + 20.0, "height": 0.20, "depth": b_depth + 18.0,
        "opacity": 0.98
    })

    # 2. Secretariat Main Block Floors
    floor_configs = [
        ("G00", "Citizen Facilitation Center (Seva Kendra)", "SEVA_CTR", "Public Citizen Service Atrium & Help Desks", "#1e3a8a"),
        ("F01", "Land Records & Cadastre Directorate", "CAD_DIR", "SVAMITVA & DILRMP Spatial Data Records Hub", "#1e40af"),
        ("F02", "District Collectorate & Revenue Directorate", "COLL_OFF", "Executive Revenue Offices & Magistrate Court", "#1d4ed8"),
        ("F03", "Cabinet Secretariat & Conference Chambers", "CABINET", "Ministerial Chambers & Video-Conference Assembly", "#2563eb")
    ]

    for f_idx, (flr_code, flr_name, flr_tag, flr_desc, flr_col) in enumerate(floor_configs):
        z0 = round(f_idx * flr_h, 2)
        z1 = round((f_idx + 1) * flr_h, 2)
        flr_ulpin = make_official_3d_ulpin(p, flr_code, "V", "GOV", flr_tag, "V01")

        reg.add_unit(CadastreUnit(
            id=f"govt_floor_{flr_code.lower()}",
            name=f"{flr_name} ({flr_tag})",
            type="GOVT_OFFICE",
            floor=flr_code,
            space_class="V",
            rights="GOV",
            unit_id=flr_tag,
            ulpin_3d=flr_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, f_idx, 1),
            owner="Government of Andhra Pradesh / General Administration Dept",
            description=f"{flr_desc} on tier {flr_code}",
            parent_2d_ulpin=p,
            category="GOVT_SPACES",
            z_min=z0, z_max=z1,
            carpet_area_sqm=round(b_width * b_depth * 0.85, 1),
            carpet_area_sqft=round(b_width * b_depth * 0.85 * 10.7639, 1),
            bbox={"x_min": -b_width/2, "x_max": b_width/2, "y_min": -b_depth/2, "y_max": b_depth/2, "z_min": z0, "z_max": z1}
        ))

        # Main Floor Geometry
        geometries.append({
            "id": f"govt_floor_{flr_code.lower()}",
            "name": flr_name,
            "type": "ROOM",
            "floor": flr_code,
            "category": "GOVT_SPACES",
            "space_class": "V",
            "rights": "GOV",
            "owner": "General Administration Dept",
            "unit_id": flr_tag,
            "ulpin_3d": flr_ulpin,
            "color": flr_col,
            "edge_color": "#60a5fa",
            "z_min": z0, "z_max": z1,
            "cx": 0.0, "cy": round(z0 + flr_h / 2.0, 2), "cz": 0.0,
            "width": b_width, "height": flr_h, "depth": b_depth,
            "opacity": 0.94
        })

        # Floor Slab
        geometries.append({
            "id": f"slab_govt_{flr_code.lower()}",
            "name": f"Secretariat Floor {flr_code} Structural Slab",
            "type": "SLAB",
            "floor": flr_code,
            "category": "GOVT_SPACES",
            "space_class": "V",
            "rights": "GOV",
            "owner": "General Administration Dept",
            "unit_id": f"SLAB_{flr_tag}",
            "ulpin_3d": flr_ulpin,
            "color": "#172554",
            "edge_color": "#00f0ff",
            "z_min": z0, "z_max": round(z0 + 0.15, 2),
            "cx": 0.0, "cy": round(z0 + 0.075, 2), "cz": 0.0,
            "width": b_width + 0.8, "height": 0.15, "depth": b_depth + 0.8,
            "opacity": 0.98
        })

    # 3. Civic Public Safety Outpost / Police Station Building (G+1)
    police_ulpin = make_official_3d_ulpin(p, "F01", "V", "GOV", "POLICE01", "V01")
    reg.add_unit(CadastreUnit(
        id="govt_police_outpost",
        name="Civic Public Safety Outpost & Police Station",
        type="GOVT_OFFICE",
        floor="F01",
        space_class="V",
        rights="GOV",
        unit_id="POLICE01",
        ulpin_3d=police_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 1, 90),
        owner="State Police Department",
        description="Public safety outpost and 24/7 emergency coordination desk",
        parent_2d_ulpin=p,
        category="GOVT_SPACES",
        z_min=0.0, z_max=6.5,
        carpet_area_sqm=180.0,
        carpet_area_sqft=1937.5,
        bbox={"x_min": b_width/2 + 5.0, "x_max": b_width/2 + 18.0, "y_min": -8.0, "y_max": 8.0, "z_min": 0.0, "z_max": 6.5}
    ))
    geometries.append({
        "id": "govt_police_outpost",
        "name": "Civic Police Outpost (24/7)",
        "type": "ROOM",
        "floor": "F01",
        "category": "GOVT_SPACES",
        "space_class": "V",
        "rights": "GOV",
        "owner": "State Police Department",
        "unit_id": "POLICE01",
        "ulpin_3d": police_ulpin,
        "color": "#1e3a8a",
        "edge_color": "#ffd166",
        "z_min": 0.0, "z_max": 6.5,
        "cx": round(b_width/2 + 11.5, 2), "cy": 3.25, "cz": 0.0,
        "width": 13.0, "height": 6.5, "depth": 16.0,
        "opacity": 0.95
    })

    render_payload = {
        "parent_2d_ulpin": p,
        "building_name": complex_name,
        "category": "GOVT_SPACES",
        "building_height": total_h,
        "building_depth": 0.20,
        "floors_count": n_floors,
        "basements_count": 0,
        "elevation_range": {"z_min": -0.20, "z_max": total_h},
        "floor_height_m": flr_h,
        "cadastre": reg.to_dict(),
        "geometries": geometries,
        "source_filename": "govt_spaces_cadastre"
    }

    return reg, render_payload


# ==============================================================================
# 5. INTEGRATED MASTER TOWN CADASTRE GENERATOR (ZERO CLUMSINESS)
# ==============================================================================

def build_master_town_cadastre(
    parent_ulpin: str = "28045678901000",
    town_name: str = "SVAMITVA Integrated Smart Town Masterplan"
) -> Tuple[CadastreRegistry, Dict[str, Any]]:
    """
    Coordinates all infrastructure and housing into a clean, collision-free township:
    - West Zone: Railway Corridor & Central Station (Category: RAILWAY)
    - Central Spine: Arterial Highway & Crossroad (Category: ROADS)
    - Civic Center: Memorial Plaza & National Statue (Category: MONUMENTS)
    - North Zone: Government Secretariat & Police Outpost (Category: GOVT_SPACES)
    - East Zone: Multi-Storey Residential Complex (Category: BUILDINGS)
    - Green Belt: Landscaped Lawns & Public Buffer (Category: COMMON_SPACES)
    
    Every geometry has an explicit `category` tag, allowing instant solo-isolation
    or master composite view without any visual clutter or clumsiness.
    """
    p = normalize_2d_ulpin(parent_ulpin)
    master_reg = CadastreRegistry(p)
    all_geometries: List[Dict[str, Any]] = []

    # 1. Railway Corridor (Offset X = -45m)
    r_reg, r_payload = build_railway_cadastre(parent_ulpin="28045678901234", station_name="Metro Central Station", track_length_m=100.0)
    for u in r_reg.units.values():
        u.category = "RAILWAY"
        master_reg.add_unit(u)
    for g in r_payload.get("geometries", []):
        g_copy = dict(g)
        g_copy["category"] = "RAILWAY"
        g_copy["cx"] = round(g_copy["cx"] - 45.0, 2)
        all_geometries.append(g_copy)

    # 2. Road Network (Central Spine, X = -12m)
    rd_reg, rd_payload = build_road_network_cadastre(parent_ulpin="28045678901235", road_name="Township Arterial Avenue", corridor_length_m=100.0)
    for u in rd_reg.units.values():
        u.category = "ROADS"
        master_reg.add_unit(u)
    for g in rd_payload.get("geometries", []):
        g_copy = dict(g)
        g_copy["category"] = "ROADS"
        g_copy["cx"] = round(g_copy["cx"] - 12.0, 2)
        all_geometries.append(g_copy)

    # 3. Civic Monument & Statue Plaza (Center-East, X = 18m, Z = -25m)
    m_reg, m_payload = build_civic_monument_cadastre(parent_ulpin="28045678901237", monument_name="National Unity Statue Plaza")
    for u in m_reg.units.values():
        u.category = "MONUMENTS"
        master_reg.add_unit(u)
    for g in m_payload.get("geometries", []):
        g_copy = dict(g)
        g_copy["category"] = "MONUMENTS"
        g_copy["cx"] = round(g_copy["cx"] + 18.0, 2)
        g_copy["cz"] = round(g_copy["cz"] - 25.0, 2)
        all_geometries.append(g_copy)

    # 4. Government Administrative Complex (North-East, X = 18m, Z = 22m)
    gov_reg, gov_payload = build_govt_spaces_cadastre(parent_ulpin="28045678901236", complex_name="State Secretariat Complex")
    for u in gov_reg.units.values():
        u.category = "GOVT_SPACES"
        master_reg.add_unit(u)
    for g in gov_payload.get("geometries", []):
        g_copy = dict(g)
        g_copy["category"] = "GOVT_SPACES"
        g_copy["cx"] = round(g_copy["cx"] + 18.0, 2)
        g_copy["cz"] = round(g_copy["cz"] + 22.0, 2)
        all_geometries.append(g_copy)

    # 5. Private Residential Housing (Far East, X = 55m, Z = 0m)
    res_bldg_ulpin = make_official_3d_ulpin(p, "F01", "V", "PRV", "RES_TOWER_A", "V01")
    master_reg.add_unit(CadastreUnit(
        id="private_residential_tower",
        name="Royal Palms Residential Tower A",
        type="BUILDING",
        floor="F01-F05",
        space_class="V",
        rights="PRV",
        unit_id="RES_TOWER_A",
        ulpin_3d=res_bldg_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 2, 1, 1),
        owner="Private Apartment Owners Association",
        description="Private residential multi-storey building with 10 flats",
        parent_2d_ulpin=p,
        category="BUILDINGS",
        z_min=0.0, z_max=15.0,
        carpet_area_sqm=1400.0,
        carpet_area_sqft=15069.5,
        bbox={"x_min": 45.0, "x_max": 65.0, "y_min": -12.0, "y_max": 12.0, "z_min": 0.0, "z_max": 15.0}
    ))
    all_geometries.append({
        "id": "private_residential_tower",
        "name": "Royal Palms Residential Tower A",
        "type": "ROOM",
        "floor": "F01",
        "category": "BUILDINGS",
        "space_class": "V",
        "rights": "PRV",
        "owner": "Private Owners Association",
        "unit_id": "RES_TOWER_A",
        "ulpin_3d": res_bldg_ulpin,
        "color": "#047857",
        "edge_color": "#34d399",
        "z_min": 0.0, "z_max": 15.0,
        "cx": 55.0, "cy": 7.5, "cz": 0.0,
        "width": 20.0, "height": 15.0, "depth": 24.0,
        "opacity": 0.94
    })

    # Individual Residential Suites
    for fi in range(1, 6):
        fid = f"RES_FLAT_A{fi}01"
        fu_3d = make_official_3d_ulpin(p, f"F{fi:02d}", "V", "PRV", f"A{fi}01", "V01")
        master_reg.add_unit(CadastreUnit(
            id=f"flat_a{fi}01",
            name=f"Residential Flat A{fi}01 (Floor {fi})",
            type="FLAT",
            floor=f"F{fi:02d}",
            space_class="V",
            rights="PRV",
            unit_id=f"A{fi}01",
            ulpin_3d=fu_3d,
            ulpin_numeric=make_numeric_3d_ulpin(p, 2, fi, 1),
            owner=f"Resident Owner #{fi}",
            description=f"3BHK Private Flat A{fi}01 on Floor {fi}",
            parent_2d_ulpin=p,
            category="BUILDINGS",
            z_min=(fi-1)*3.0, z_max=fi*3.0,
            carpet_area_sqm=125.0,
            carpet_area_sqft=1345.5,
            bbox={"x_min": 45.0, "x_max": 65.0, "y_min": -12.0, "y_max": 12.0, "z_min": (fi-1)*3.0, "z_max": fi*3.0}
        ))

    # 6. Public Community Green Lawns & Buffer
    park_ulpin = make_official_3d_ulpin(p, "G00", "S", "COM", "GREEN_PARK01", "V01")
    master_reg.add_unit(CadastreUnit(
        id="community_green_park",
        name="SVAMITVA Eco-Park & Buffer Green",
        type="PARK",
        floor="G00",
        space_class="S",
        rights="COM",
        unit_id="GREEN_PARK01",
        ulpin_3d=park_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 3, 0, 1),
        owner="Municipal Corporation / Community",
        description="Public eco-park buffer between highway and residential sector",
        parent_2d_ulpin=p,
        category="COMMON_SPACES",
        z_min=-0.10, z_max=0.00,
        carpet_area_sqm=800.0,
        carpet_area_sqft=8611.1,
        bbox={"x_min": 3.0, "x_max": 33.0, "y_min": -12.0, "y_max": 12.0, "z_min": -0.10, "z_max": 0.00}
    ))
    all_geometries.append({
        "id": "community_green_park",
        "name": "Community Eco-Park & Public Green",
        "type": "ROOM",
        "floor": "LAND",
        "category": "COMMON_SPACES",
        "space_class": "S",
        "rights": "COM",
        "owner": "Municipal Corporation",
        "unit_id": "GREEN_PARK01",
        "ulpin_3d": park_ulpin,
        "color": "#166534",
        "edge_color": "#4ade80",
        "z_min": -0.10, "z_max": 0.00,
        "cx": 18.0, "cy": -0.05, "cz": 0.0,
        "width": 30.0, "height": 0.10, "depth": 24.0,
        "opacity": 0.96
    })

    master_payload = {
        "parent_2d_ulpin": p,
        "building_name": town_name,
        "category": "MASTER_TOWN",
        "building_height": 15.0,
        "building_depth": 0.35,
        "floors_count": 5,
        "basements_count": 0,
        "elevation_range": {"z_min": -0.35, "z_max": 15.0},
        "floor_height_m": 3.0,
        "cadastre": master_reg.to_dict(),
        "geometries": all_geometries,
        "source_filename": "integrated_master_town_cadastre"
    }

    return master_reg, master_payload


# ==============================================================================
# 6. BRIDGES & ELEVATED FLYOVER INFRASTRUCTURE CADASTRE GENERATOR
# ==============================================================================

def build_bridge_infrastructure_cadastre(
    parent_ulpin: str = "28045678901239",
    bridge_name: str = "National River Viaduct & Flyover Corridor",
    bridge_length_m: float = 120.0,
    deck_elevation_m: float = 10.0
) -> Tuple[CadastreRegistry, Dict[str, Any]]:
    """
    Constructs high-fidelity 3D Bridge & Elevated Flyover Cadastre:
    - Elevated Reinforced Concrete Box Girder Deck Slab (Space Class: E)
    - Dual Carriageway Highway (Northbound & Southbound with central median)
    - Concrete Support Piers with Pier Caps & Elastomeric Bearings (Space Class: S)
    - North & South Heavy Abutments and Earth Retaining Wingwalls
    - Continuous Crash Barriers & Parapet Railings on both deck edges
    - Elevated LED Streetlight Poles
    - Sloped Approach Ramps connecting ground to elevated deck
    """
    p = normalize_2d_ulpin(parent_ulpin)
    reg = CadastreRegistry(p)
    geometries: List[Dict[str, Any]] = []

    half_l = bridge_length_m / 2.0
    deck_w = 14.0  # 4-lane dual carriageway
    deck_z = deck_elevation_m
    deck_th = 1.2

    # 1. Ground Reference & Waterway Corridor
    ground_ulpin = make_official_3d_ulpin(p, "G00", "S", "PUB", "GND_CORR01", "V01")
    reg.add_unit(CadastreUnit(
        id="brg_ground",
        name="Bridge Right-of-Way Surface Corridor",
        type="GROUND_LAND",
        floor="G00",
        space_class="S",
        rights="PUB",
        unit_id="GND_CORR01",
        ulpin_3d=ground_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 1),
        owner="Ministry of Road Transport & Highways / NHAI",
        description="Surface right-of-way corridor beneath elevated bridge superstructure",
        parent_2d_ulpin=p,
        category="BRIDGES",
        z_min=-0.5, z_max=0.0,
        carpet_area_sqm=round(bridge_length_m * 24.0, 1),
        carpet_area_sqft=round(bridge_length_m * 24.0 * 10.7639, 1),
        bbox={"x_min": -12.0, "x_max": 12.0, "y_min": -half_l, "y_max": half_l, "z_min": -0.5, "z_max": 0.0}
    ))
    geometries.append({
        "id": "brg_ground",
        "name": "Bridge ROW Surface Ground",
        "type": "GROUND_LAND",
        "floor": "LAND",
        "category": "BRIDGES",
        "space_class": "S",
        "rights": "PUB",
        "unit_id": "GND_CORR01",
        "ulpin_3d": ground_ulpin,
        "color": "#1e293b",
        "edge_color": "#334155",
        "z_min": -0.5, "z_max": 0.0,
        "cx": 0.0, "cy": -0.25, "cz": 0.0,
        "width": 24.0, "height": 0.5, "depth": bridge_length_m + 50.0,
        "opacity": 0.95
    })

    # Underpass River / Canal at center
    river_ulpin = make_official_3d_ulpin(p, "G00", "S", "PUB", "RIVER_CH01", "V01")
    reg.add_unit(CadastreUnit(
        id="brg_waterway",
        name="Navigable Waterway / River Channel",
        type="RIVER",
        floor="G00",
        space_class="S",
        rights="PUB",
        unit_id="RIVER_CH01",
        ulpin_3d=river_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 2),
        owner="Inland Waterways Authority of India / State Water Resources Dept",
        description="Navigable river channel spanned by the central bridge spans",
        parent_2d_ulpin=p,
        category="BRIDGES",
        z_min=-2.0, z_max=-0.5,
        carpet_area_sqm=round(40.0 * 24.0, 1),
        carpet_area_sqft=round(40.0 * 24.0 * 10.7639, 1),
        bbox={"x_min": -12.0, "x_max": 12.0, "y_min": -20.0, "y_max": 20.0, "z_min": -2.0, "z_max": -0.5}
    ))
    geometries.append({
        "id": "brg_waterway",
        "name": "Navigable Waterway Channel",
        "type": "WATER",
        "floor": "LAND",
        "category": "BRIDGES",
        "space_class": "S",
        "rights": "PUB",
        "unit_id": "RIVER_CH01",
        "ulpin_3d": river_ulpin,
        "color": "#0284c7",
        "edge_color": "#38bdf8",
        "z_min": -2.0, "z_max": -0.5,
        "cx": 0.0, "cy": -1.25, "cz": 0.0,
        "width": 24.0, "height": 1.5, "depth": 40.0,
        "opacity": 0.85
    })

    # 2. Reinforced Concrete Piers & Pier Caps
    pier_positions = [-40.0, -15.0, 15.0, 40.0]
    for idx, py in enumerate(pier_positions, start=1):
        pier_id = f"PIER0{idx}"
        pier_ulpin = make_official_3d_ulpin(p, "G00", "S", "PUB", pier_id, "V01")
        reg.add_unit(CadastreUnit(
            id=f"brg_pier_{idx}",
            name=f"Bridge Pier {idx} & Substructure Foundation ({pier_id})",
            type="PIER",
            floor="G00",
            space_class="S",
            rights="PUB",
            unit_id=pier_id,
            ulpin_3d=pier_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 10 + idx),
            owner="National Highways Authority of India (NHAI)",
            description="Heavy reinforced concrete cylindrical pier column and pile cap",
            parent_2d_ulpin=p,
            category="BRIDGES",
            z_min=0.0, z_max=deck_z,
            carpet_area_sqm=12.5,
            carpet_area_sqft=134.5,
            bbox={"x_min": -1.8, "x_max": 1.8, "y_min": py - 1.8, "y_max": py + 1.8, "z_min": 0.0, "z_max": deck_z}
        ))
        geometries.append({
            "id": f"brg_pier_{idx}_col",
            "name": f"Concrete Pier Column {idx}",
            "type": "COLUMN",
            "floor": "G00",
            "category": "BRIDGES",
            "space_class": "S",
            "rights": "PUB",
            "unit_id": pier_id,
            "ulpin_3d": pier_ulpin,
            "color": "#64748b",
            "edge_color": "#94a3b8",
            "z_min": 0.0, "z_max": deck_z - 0.8,
            "cx": 0.0, "cy": (deck_z - 0.8) / 2.0, "cz": py,
            "width": 3.0, "height": deck_z - 0.8, "depth": 3.0,
            "opacity": 1.0
        })
        geometries.append({
            "id": f"brg_pier_{idx}_cap",
            "name": f"Pier Cap & Bearing Seat {idx}",
            "type": "BEAM",
            "floor": "G00",
            "category": "BRIDGES",
            "space_class": "S",
            "rights": "PUB",
            "unit_id": pier_id,
            "ulpin_3d": pier_ulpin,
            "color": "#475569",
            "edge_color": "#cbd5e1",
            "z_min": deck_z - 0.8, "z_max": deck_z,
            "cx": 0.0, "cy": deck_z - 0.4, "cz": py,
            "width": deck_w - 0.5, "height": 0.8, "depth": 3.6,
            "opacity": 1.0
        })

    # 3. North & South Abutments
    abut_configs = [
        ("N", -half_l, "ABUT_N", "North Approach Abutment & Retaining Wingwall"),
        ("S", half_l, "ABUT_S", "South Approach Abutment & Retaining Wingwall")
    ]
    for side, ay, aid, aname in abut_configs:
        a_ulpin = make_official_3d_ulpin(p, "G00", "S", "PUB", aid, "V01")
        reg.add_unit(CadastreUnit(
            id=f"brg_abut_{side.lower()}",
            name=f"{aname} ({aid})",
            type="ABUTMENT",
            floor="G00",
            space_class="S",
            rights="PUB",
            unit_id=aid,
            ulpin_3d=a_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 20 if side == "N" else 21),
            owner="National Highways Authority of India (NHAI)",
            description="Cast-in-place concrete end abutment and ballast wall for bridge approach",
            parent_2d_ulpin=p,
            category="BRIDGES",
            z_min=0.0, z_max=deck_z,
            carpet_area_sqm=round(deck_w * 4.0, 1),
            carpet_area_sqft=round(deck_w * 4.0 * 10.7639, 1),
            bbox={"x_min": -deck_w/2, "x_max": deck_w/2, "y_min": ay - 2.0, "y_max": ay + 2.0, "z_min": 0.0, "z_max": deck_z}
        ))
        geometries.append({
            "id": f"brg_abut_{side.lower()}",
            "name": aname,
            "type": "WALL",
            "floor": "G00",
            "category": "BRIDGES",
            "space_class": "S",
            "rights": "PUB",
            "unit_id": aid,
            "ulpin_3d": a_ulpin,
            "color": "#475569",
            "edge_color": "#94a3b8",
            "z_min": 0.0, "z_max": deck_z,
            "cx": 0.0, "cy": deck_z / 2.0, "cz": ay,
            "width": deck_w + 2.0, "height": deck_z, "depth": 4.0,
            "opacity": 1.0
        })

    # 4. Superstructure: Prestressed Concrete Box Girder Deck Slab (Space Class: E)
    deck_ulpin = make_official_3d_ulpin(p, "F01", "E", "PUB", "BRG_DECK01", "V01")
    reg.add_unit(CadastreUnit(
        id="brg_deck_slab",
        name="Elevated Viaduct Deck Superstructure (BRG_DECK01)",
        type="BRIDGE_DECK",
        floor="F01",
        space_class="E",
        rights="PUB",
        unit_id="BRG_DECK01",
        ulpin_3d=deck_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 1, 1),
        owner="National Highways Authority of India (NHAI)",
        description="Continuous prestressed box girder superstructure carrying 4-lane arterial carriageway",
        parent_2d_ulpin=p,
        category="BRIDGES",
        z_min=deck_z, z_max=deck_z + deck_th,
        carpet_area_sqm=round(bridge_length_m * deck_w, 1),
        carpet_area_sqft=round(bridge_length_m * deck_w * 10.7639, 1),
        bbox={"x_min": -deck_w/2, "x_max": deck_w/2, "y_min": -half_l, "y_max": half_l, "z_min": deck_z, "z_max": deck_z + deck_th}
    ))
    geometries.append({
        "id": "brg_deck_slab",
        "name": "Elevated Box Girder Deck Slab",
        "type": "ROOM",
        "floor": "F01",
        "category": "BRIDGES",
        "space_class": "E",
        "rights": "PUB",
        "unit_id": "BRG_DECK01",
        "ulpin_3d": deck_ulpin,
        "color": "#3b82f6",
        "edge_color": "#60a5fa",
        "z_min": deck_z, "z_max": deck_z + deck_th,
        "cx": 0.0, "cy": deck_z + (deck_th / 2.0), "cz": 0.0,
        "width": deck_w, "height": deck_th, "depth": bridge_length_m,
        "opacity": 0.96
    })

    # 5. Dual Carriageways (Northbound & Southbound Lanes) on the Deck
    cway_z = deck_z + deck_th
    nb_ulpin = make_official_3d_ulpin(p, "F01", "E", "PUB", "BRG_CW_NB", "V01")
    reg.add_unit(CadastreUnit(
        id="brg_cway_nb",
        name="Elevated Carriageway - Northbound 2-Lane (BRG_CW_NB)",
        type="CARRIAGEWAY",
        floor="F01",
        space_class="E",
        rights="PUB",
        unit_id="BRG_CW_NB",
        ulpin_3d=nb_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 1, 2),
        owner="State Public Works Dept (PWD) / NHAI",
        description="Northbound 2-lane asphalt wearing course carriageway with anti-skid surface",
        parent_2d_ulpin=p,
        category="BRIDGES",
        z_min=cway_z, z_max=cway_z + 0.15,
        carpet_area_sqm=round(bridge_length_m * 6.2, 1),
        carpet_area_sqft=round(bridge_length_m * 6.2 * 10.7639, 1),
        bbox={"x_min": -6.5, "x_max": -0.3, "y_min": -half_l, "y_max": half_l, "z_min": cway_z, "z_max": cway_z + 0.15}
    ))
    geometries.append({
        "id": "brg_cway_nb",
        "name": "Northbound Elevated Carriageway",
        "type": "ROOM",
        "floor": "F01",
        "category": "BRIDGES",
        "space_class": "E",
        "rights": "PUB",
        "unit_id": "BRG_CW_NB",
        "ulpin_3d": nb_ulpin,
        "color": "#1e293b",
        "edge_color": "#38bdf8",
        "z_min": cway_z, "z_max": cway_z + 0.15,
        "cx": -3.4, "cy": cway_z + 0.075, "cz": 0.0,
        "width": 6.2, "height": 0.15, "depth": bridge_length_m,
        "opacity": 0.98
    })

    sb_ulpin = make_official_3d_ulpin(p, "F01", "E", "PUB", "BRG_CW_SB", "V01")
    reg.add_unit(CadastreUnit(
        id="brg_cway_sb",
        name="Elevated Carriageway - Southbound 2-Lane (BRG_CW_SB)",
        type="CARRIAGEWAY",
        floor="F01",
        space_class="E",
        rights="PUB",
        unit_id="BRG_CW_SB",
        ulpin_3d=sb_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 1, 3),
        owner="State Public Works Dept (PWD) / NHAI",
        description="Southbound 2-lane asphalt wearing course carriageway with anti-skid surface",
        parent_2d_ulpin=p,
        category="BRIDGES",
        z_min=cway_z, z_max=cway_z + 0.15,
        carpet_area_sqm=round(bridge_length_m * 6.2, 1),
        carpet_area_sqft=round(bridge_length_m * 6.2 * 10.7639, 1),
        bbox={"x_min": 0.3, "x_max": 6.5, "y_min": -half_l, "y_max": half_l, "z_min": cway_z, "z_max": cway_z + 0.15}
    ))
    geometries.append({
        "id": "brg_cway_sb",
        "name": "Southbound Elevated Carriageway",
        "type": "ROOM",
        "floor": "F01",
        "category": "BRIDGES",
        "space_class": "E",
        "rights": "PUB",
        "unit_id": "BRG_CW_SB",
        "ulpin_3d": sb_ulpin,
        "color": "#1e293b",
        "edge_color": "#38bdf8",
        "z_min": cway_z, "z_max": cway_z + 0.15,
        "cx": 3.4, "cy": cway_z + 0.075, "cz": 0.0,
        "width": 6.2, "height": 0.15, "depth": bridge_length_m,
        "opacity": 0.98
    })

    # Central Median Barrier & Outer Crash Barriers
    geometries.append({
        "id": "brg_median",
        "name": "Bridge Central Anti-Crash Concrete Barrier",
        "type": "WALL",
        "floor": "F01",
        "category": "BRIDGES",
        "space_class": "E",
        "rights": "PUB",
        "unit_id": "BRG_DECK01",
        "ulpin_3d": deck_ulpin,
        "color": "#e2e8f0",
        "edge_color": "#94a3b8",
        "z_min": cway_z, "z_max": cway_z + 0.9,
        "cx": 0.0, "cy": cway_z + 0.45, "cz": 0.0,
        "width": 0.6, "height": 0.9, "depth": bridge_length_m,
        "opacity": 1.0
    })

    for side, xpos in [("left", -6.7), ("right", 6.7)]:
        geometries.append({
            "id": f"brg_barrier_{side}",
            "name": f"Reinforced Crash Barrier & Parapet ({side.title()})",
            "type": "WALL",
            "floor": "F01",
            "category": "BRIDGES",
            "space_class": "E",
            "rights": "PUB",
            "unit_id": "BRG_DECK01",
            "ulpin_3d": deck_ulpin,
            "color": "#f8fafc",
            "edge_color": "#cbd5e1",
            "z_min": cway_z, "z_max": cway_z + 1.1,
            "cx": xpos, "cy": cway_z + 0.55, "cz": 0.0,
            "width": 0.5, "height": 1.1, "depth": bridge_length_m,
            "opacity": 1.0
        })

    # 6. Sloped Approach Ramps
    ramp_l = 30.0
    for side, r_start_y, r_end_y, r_id, r_name in [
        ("N", -half_l - ramp_l, -half_l, "RAMP_N", "North Approach Flyover Ramp"),
        ("S", half_l, half_l + ramp_l, "RAMP_S", "South Approach Flyover Ramp")
    ]:
        r_ulpin = make_official_3d_ulpin(p, "G00", "S", "PUB", r_id, "V01")
        reg.add_unit(CadastreUnit(
            id=f"brg_ramp_{side.lower()}",
            name=f"{r_name} ({r_id})",
            type="APPROACH_RAMP",
            floor="G00",
            space_class="S",
            rights="PUB",
            unit_id=r_id,
            ulpin_3d=r_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 30 if side == "N" else 31),
            owner="National Highways Authority of India (NHAI)",
            description="Reinforced earth retaining approach ramp connecting surface road to elevated viaduct",
            parent_2d_ulpin=p,
            category="BRIDGES",
            z_min=0.0, z_max=deck_z,
            carpet_area_sqm=round(ramp_l * deck_w, 1),
            carpet_area_sqft=round(ramp_l * deck_w * 10.7639, 1),
            bbox={"x_min": -deck_w/2, "x_max": deck_w/2, "y_min": min(r_start_y, r_end_y), "y_max": max(r_start_y, r_end_y), "z_min": 0.0, "z_max": deck_z}
        ))
        geometries.append({
            "id": f"brg_ramp_{side.lower()}",
            "name": r_name,
            "type": "ROOM",
            "floor": "LAND",
            "category": "BRIDGES",
            "space_class": "S",
            "rights": "PUB",
            "unit_id": r_id,
            "ulpin_3d": r_ulpin,
            "color": "#334155",
            "edge_color": "#64748b",
            "z_min": 0.0, "z_max": deck_z / 2.0,
            "cx": 0.0, "cy": deck_z / 4.0, "cz": (r_start_y + r_end_y) / 2.0,
            "width": deck_w, "height": deck_z / 2.0, "depth": ramp_l,
            "opacity": 0.95
        })

    bridge_payload = {
        "parent_2d_ulpin": p,
        "building_name": bridge_name,
        "category": "BRIDGES",
        "building_height": round(deck_z + deck_th + 3.0, 1),
        "building_depth": 2.0,
        "floors_count": 2,
        "basements_count": 0,
        "elevation_range": {"z_min": -2.0, "z_max": round(deck_z + deck_th + 3.0, 1)},
        "floor_height_m": deck_z,
        "cadastre": reg.to_dict(),
        "geometries": geometries,
        "source_filename": "bridge_infrastructure_cadastre"
    }

    return reg, bridge_payload


# ==============================================================================
# 7. TUNNELS & SUBTERRANEAN CORRIDOR CADASTRE GENERATOR
# ==============================================================================

def build_tunnel_infrastructure_cadastre(
    parent_ulpin: str = "28045678901240",
    tunnel_name: str = "Subterranean Twin-Bore Expressway Tunnel",
    tunnel_length_m: float = 120.0,
    depth_m: float = 14.0
) -> Tuple[CadastreRegistry, Dict[str, Any]]:
    """
    Constructs high-fidelity 3D Subterranean Tunnel Infrastructure Cadastre:
    - Deep underground twin horseshoe tunnel tubes (Z = -14.0m to -6.5m, Space Class: U)
    - Reinforced precast concrete segment vault lining
    - Underground asphalt carriageway lanes (Northbound & Southbound)
    - Subterranean safety walkways & cable trenches
    - Pressurized emergency cross-passages with fire doors connecting tubes
    - Heavy vertical exhaust & ventilation shaft rising to surface headhouse
    - Suspended jet-fan booster ventilation units
    - Cut-and-cover North and South entrance portals with rock-socketed headwalls
    """
    p = normalize_2d_ulpin(parent_ulpin)
    reg = CadastreRegistry(p)
    geometries: List[Dict[str, Any]] = []

    half_l = tunnel_length_m / 2.0
    floor_z = -depth_m  # Base invert elevation: -14.0m
    crown_z = floor_z + 7.5  # Top crown of vault: -6.5m
    tube_w = 8.5
    tube_h = 7.5

    # 1. Surface Overburden Soil / Rock Reference (Space Class: S)
    surface_ulpin = make_official_3d_ulpin(p, "G00", "S", "PUB", "TNL_SURF01", "V01")
    reg.add_unit(CadastreUnit(
        id="tnl_surface",
        name="Tunnel Overburden & Surface Geological Layer",
        type="GROUND_LAND",
        floor="G00",
        space_class="S",
        rights="PUB",
        unit_id="TNL_SURF01",
        ulpin_3d=surface_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 1),
        owner="Ministry of Road Transport & Highways / National Highways Authority",
        description="Surface land envelope situated directly above subterranean tunnel corridor",
        parent_2d_ulpin=p,
        category="TUNNELS",
        z_min=-1.0, z_max=0.0,
        carpet_area_sqm=round(tunnel_length_m * 30.0, 1),
        carpet_area_sqft=round(tunnel_length_m * 30.0 * 10.7639, 1),
        bbox={"x_min": -15.0, "x_max": 15.0, "y_min": -half_l, "y_max": half_l, "z_min": -1.0, "z_max": 0.0}
    ))
    geometries.append({
        "id": "tnl_surface",
        "name": "Surface Overburden Layer",
        "type": "GROUND_LAND",
        "floor": "LAND",
        "category": "TUNNELS",
        "space_class": "S",
        "rights": "PUB",
        "unit_id": "TNL_SURF01",
        "ulpin_3d": surface_ulpin,
        "color": "#1e293b",
        "edge_color": "#475569",
        "z_min": -0.6, "z_max": 0.0,
        "cx": 0.0, "cy": -0.3, "cz": 0.0,
        "width": 30.0, "height": 0.6, "depth": tunnel_length_m + 30.0,
        "opacity": 0.82
    })

    # 2. Cut-and-Cover North & South Portal Retaining Structures (Space Class: S / U)
    portals = [
        ("N", -half_l, "PORTAL_N", "North Tunnel Portal Entrance & Headwall"),
        ("S", half_l, "PORTAL_S", "South Tunnel Portal Entrance & Headwall")
    ]
    for side, py, pid, pname in portals:
        pt_ulpin = make_official_3d_ulpin(p, "G00", "S", "PUB", pid, "V01")
        reg.add_unit(CadastreUnit(
            id=f"tnl_portal_{side.lower()}",
            name=f"{pname} ({pid})",
            type="TUNNEL_PORTAL",
            floor="G00",
            space_class="S",
            rights="PUB",
            unit_id=pid,
            ulpin_3d=pt_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 5 if side == "N" else 6),
            owner="National Highways Authority of India (NHAI)",
            description=f"Reinforced concrete portal canopy and earth retaining headwall",
            parent_2d_ulpin=p,
            category="TUNNELS",
            z_min=floor_z, z_max=2.0,
            carpet_area_sqm=round(30.0 * 6.0, 1),
            carpet_area_sqft=round(30.0 * 6.0 * 10.7639, 1),
            bbox={"x_min": -15.0, "x_max": 15.0, "y_min": py - 3.0, "y_max": py + 3.0, "z_min": floor_z, "z_max": 2.0}
        ))
        geometries.append({
            "id": f"tnl_portal_{side.lower()}",
            "name": pname,
            "type": "WALL",
            "floor": "G00",
            "category": "TUNNELS",
            "space_class": "S",
            "rights": "PUB",
            "unit_id": pid,
            "ulpin_3d": pt_ulpin,
            "color": "#64748b",
            "edge_color": "#94a3b8",
            "z_min": floor_z, "z_max": 2.0,
            "cx": 0.0, "cy": (floor_z + 2.0) / 2.0, "cz": py,
            "width": 30.0, "height": 2.0 - floor_z, "depth": 4.0,
            "opacity": 0.98
        })

    # 3. Subterranean Tube 1 (Northbound) and Tube 2 (Southbound) (Space Class: U)
    tube_configs = [
        ("TUBE1", -7.5, "TNL_TUBE1", "Subterranean Vaulted Tunnel - Northbound Tube", "#7c3aed", "#a78bfa"),
        ("TUBE2", 7.5, "TNL_TUBE2", "Subterranean Vaulted Tunnel - Southbound Tube", "#6d28d9", "#c4b5fd")
    ]

    for tid, cx, uid, uname, color, edge_color in tube_configs:
        t_ulpin = make_official_3d_ulpin(p, "B02", "U", "PUB", uid, "V01")
        reg.add_unit(CadastreUnit(
            id=f"tnl_{tid.lower()}",
            name=f"{uname} ({uid})",
            type="TUNNEL_TUBE",
            floor="B02",
            space_class="U",
            rights="PUB",
            unit_id=uid,
            ulpin_3d=t_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 2, 2, 1 if tid == "TUBE1" else 2),
            owner="National Highways Authority of India (NHAI)",
            description=f"Cast precast concrete segmented vaulted subterranean tunnel tube ({depth_m}m depth)",
            parent_2d_ulpin=p,
            category="TUNNELS",
            z_min=floor_z, z_max=crown_z,
            carpet_area_sqm=round(tunnel_length_m * tube_w, 1),
            carpet_area_sqft=round(tunnel_length_m * tube_w * 10.7639, 1),
            bbox={"x_min": cx - (tube_w/2), "x_max": cx + (tube_w/2), "y_min": -half_l, "y_max": half_l, "z_min": floor_z, "z_max": crown_z}
        ))

        # Vaulted Concrete Outer Lining Mesh
        geometries.append({
            "id": f"tnl_{tid.lower()}_vault",
            "name": f"{uname} Concrete Arch Vault",
            "type": "ROOM",
            "floor": "B02",
            "category": "TUNNELS",
            "space_class": "U",
            "rights": "PUB",
            "unit_id": uid,
            "ulpin_3d": t_ulpin,
            "color": color,
            "edge_color": edge_color,
            "z_min": floor_z, "z_max": crown_z,
            "cx": cx, "cy": (floor_z + crown_z) / 2.0, "cz": 0.0,
            "width": tube_w, "height": tube_h, "depth": tunnel_length_m,
            "opacity": 0.88
        })

        # Road Carriageway Invert inside the tube
        cw_id = f"CW_{tid}"
        cw_ulpin = make_official_3d_ulpin(p, "B02", "U", "PUB", cw_id, "V01")
        reg.add_unit(CadastreUnit(
            id=f"tnl_{tid.lower()}_cw",
            name=f"Underground Carriageway - {tid} ({cw_id})",
            type="CARRIAGEWAY",
            floor="B02",
            space_class="U",
            rights="PUB",
            unit_id=cw_id,
            ulpin_3d=cw_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 2, 2, 10 if tid == "TUBE1" else 11),
            owner="State PWD / NHAI",
            description=f"Dual-lane asphalt carriageway in subterranean tunnel tube at elevation {floor_z}m",
            parent_2d_ulpin=p,
            category="TUNNELS",
            z_min=floor_z, z_max=floor_z + 0.25,
            carpet_area_sqm=round(tunnel_length_m * 6.5, 1),
            carpet_area_sqft=round(tunnel_length_m * 6.5 * 10.7639, 1),
            bbox={"x_min": cx - 3.25, "x_max": cx + 3.25, "y_min": -half_l, "y_max": half_l, "z_min": floor_z, "z_max": floor_z + 0.25}
        ))
        geometries.append({
            "id": f"tnl_{tid.lower()}_cw",
            "name": f"Subterranean Carriageway {tid}",
            "type": "ROOM",
            "floor": "B02",
            "category": "TUNNELS",
            "space_class": "U",
            "rights": "PUB",
            "unit_id": cw_id,
            "ulpin_3d": cw_ulpin,
            "color": "#0f172a",
            "edge_color": "#38bdf8",
            "z_min": floor_z, "z_max": floor_z + 0.25,
            "cx": cx, "cy": floor_z + 0.125, "cz": 0.0,
            "width": 6.5, "height": 0.25, "depth": tunnel_length_m,
            "opacity": 0.98
        })

    # 4. Emergency Evacuation Cross-Passages (Space Class: U)
    cpass_positions = [-30.0, 30.0]
    for idx, cpy in enumerate(cpass_positions, start=1):
        cpass_id = f"CPASS0{idx}"
        cp_ulpin = make_official_3d_ulpin(p, "B02", "U", "PUB", cpass_id, "V01")
        reg.add_unit(CadastreUnit(
            id=f"tnl_cpass_{idx}",
            name=f"Subterranean Emergency Evacuation Cross-Passage {idx} ({cpass_id})",
            type="CROSS_PASSAGE",
            floor="B02",
            space_class="U",
            rights="PUB",
            unit_id=cpass_id,
            ulpin_3d=cp_ulpin,
            ulpin_numeric=make_numeric_3d_ulpin(p, 2, 2, 20 + idx),
            owner="National Highways Authority of India (NHAI) / Emergency Services",
            description=f"Pressurized fire-resistant pedestrian cross-connection between twin tunnel tubes",
            parent_2d_ulpin=p,
            category="TUNNELS",
            z_min=floor_z, z_max=floor_z + 3.2,
            carpet_area_sqm=round(6.5 * 3.5, 1),
            carpet_area_sqft=round(6.5 * 3.5 * 10.7639, 1),
            bbox={"x_min": -3.25, "x_max": 3.25, "y_min": cpy - 1.75, "y_max": cpy + 1.75, "z_min": floor_z, "z_max": floor_z + 3.2}
        ))
        geometries.append({
            "id": f"tnl_cpass_{idx}",
            "name": f"Emergency Evacuation Cross-Passage {idx}",
            "type": "ROOM",
            "floor": "B02",
            "category": "TUNNELS",
            "space_class": "U",
            "rights": "PUB",
            "unit_id": cpass_id,
            "ulpin_3d": cp_ulpin,
            "color": "#15803d",
            "edge_color": "#4ade80",
            "z_min": floor_z, "z_max": floor_z + 3.2,
            "cx": 0.0, "cy": floor_z + 1.6, "cz": cpy,
            "width": 6.5, "height": 3.2, "depth": 3.5,
            "opacity": 0.95
        })

    # 5. Heavy Central Deep Ventilation & Exhaust Shaft (Space Class: U)
    vent_ulpin = make_official_3d_ulpin(p, "B01", "U", "UTL", "VENT_SHAFT01", "V01")
    reg.add_unit(CadastreUnit(
        id="tnl_vent_shaft",
        name="Tunnel Deep Ventilation & Smoke Exhaust Shaft (VENT_SHAFT01)",
        type="VENTILATION_SHAFT",
        floor="B01",
        space_class="U",
        rights="UTL",
        unit_id="VENT_SHAFT01",
        ulpin_3d=vent_ulpin,
        ulpin_numeric=make_numeric_3d_ulpin(p, 2, 1, 1),
        owner="Municipal Corporation / Highway Infrastructure Dept",
        description=f"Vertical concrete ventilation shaft rising from subterranean depth {floor_z}m to surface headhouse",
        parent_2d_ulpin=p,
        category="TUNNELS",
        z_min=floor_z, z_max=3.5,
        carpet_area_sqm=36.0,
        carpet_area_sqft=387.5,
        bbox={"x_min": -3.0, "x_max": 3.0, "y_min": -3.0, "y_max": 3.0, "z_min": floor_z, "z_max": 3.5}
    ))
    geometries.append({
        "id": "tnl_vent_shaft",
        "name": "Tunnel Vertical Air Ventilation Shaft",
        "type": "ROOM",
        "floor": "B01",
        "category": "TUNNELS",
        "space_class": "U",
        "rights": "UTL",
        "unit_id": "VENT_SHAFT01",
        "ulpin_3d": vent_ulpin,
        "color": "#0284c7",
        "edge_color": "#38bdf8",
        "z_min": floor_z, "z_max": 3.5,
        "cx": 0.0, "cy": (floor_z + 3.5) / 2.0, "cz": 0.0,
        "width": 5.0, "height": 3.5 - floor_z, "depth": 5.0,
        "opacity": 0.95
    })

    # Surface Ventilation Plant Headhouse
    geometries.append({
        "id": "tnl_vent_headhouse",
        "name": "Surface Ventilation Fan Headhouse",
        "type": "ROOM",
        "floor": "G00",
        "category": "TUNNELS",
        "space_class": "S",
        "rights": "UTL",
        "unit_id": "VENT_SHAFT01",
        "ulpin_3d": vent_ulpin,
        "color": "#334155",
        "edge_color": "#0284c7",
        "z_min": 0.0, "z_max": 3.5,
        "cx": 0.0, "cy": 1.75, "cz": 0.0,
        "width": 8.0, "height": 3.5, "depth": 8.0,
        "opacity": 0.95
    })

    tunnel_payload = {
        "parent_2d_ulpin": p,
        "building_name": tunnel_name,
        "category": "TUNNELS",
        "building_height": 3.5,
        "building_depth": abs(floor_z),
        "floors_count": 1,
        "basements_count": 2,
        "elevation_range": {"z_min": floor_z, "z_max": 3.5},
        "floor_height_m": 3.5,
        "cadastre": reg.to_dict(),
        "geometries": geometries,
        "source_filename": "tunnel_infrastructure_cadastre"
    }

    return reg, tunnel_payload

