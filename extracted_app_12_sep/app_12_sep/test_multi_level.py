import sys
from pathlib import Path
sys.path.insert(0, "vcad_engine_sih2026")

from blueprint_vision import parse_any_blueprint
from ulpin_engine import (
    CadastreRegistry, CadastreUnit, make_official_3d_ulpin,
    make_numeric_3d_ulpin, normalize_2d_ulpin
)

def test_generation():
    parent_ulpin = "12345678901234"
    building_height = 15.0
    floors_count = 5
    building_depth = 6.0
    basements_count = 2

    h_floor = building_height / floors_count # 3.0m
    h_basement = building_depth / basements_count # 3.0m

    print(f"Building: {floors_count} Floors (each {h_floor}m), {basements_count} Basements (each {h_basement}m)")
    print(f"Z-Span: {-building_depth}m to +{building_height}m")

    # Sample blueprint
    sample_bp = "storage/blueprints/floor_plan_f03_a301.png"
    analysis = parse_any_blueprint(sample_bp, floors_count=1)

    print("Rooms per floor:", len(analysis.get("rooms", [])))
    print("Walls per floor:", len(analysis.get("walls", [])))

test_generation()