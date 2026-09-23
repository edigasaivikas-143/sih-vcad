"""
3D ULPIN Engine & Cadastre Registry Specification
Compliant with SVAMITVA / DILRMP 3D Extension & ISO 19152 LADM Standard.

Official Schema:
  [Parent ULPIN]-[Z-Level]-[Space Class]-[Rights/Use Code]-[Unit ID]-[Version]
Example:
  12345678901234-F03-V-PRV-A301-V01
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any

DEFAULT_PARENT_ULPIN = "12345678901234"

def normalize_2d_ulpin(ulpin: str | int) -> str:
    """Validate and normalize 14-digit parent 2D ULPIN."""
    clean = str(ulpin).strip()
    clean = "".join(c for c in clean if c.isdigit())
    if len(clean) < 14:
        clean = clean.ljust(14, "0")
    else:
        clean = clean[:14]
    return clean

def make_official_3d_ulpin(
    parent_ulpin: str,
    z_level: str,
    space_class: str,
    rights: str,
    unit_id: str,
    version: str = "V01",
) -> str:
    """
    Generate the official separator-based 3D ULPIN string:
    [Parent ULPIN]-[Z-Level]-[Space Class]-[Rights/Use Code]-[Unit ID]-[Version]
    """
    parent = normalize_2d_ulpin(parent_ulpin)
    z_clean = z_level.strip().upper()
    sc_clean = space_class.strip().upper()
    rights_clean = rights.strip().upper()
    unit_clean = unit_id.strip().upper().replace(" ", "_")
    v_clean = version.strip().upper()
    return f"{parent}-{z_clean}-{sc_clean}-{rights_clean}-{unit_clean}-{v_clean}"

def make_numeric_3d_ulpin(
    parent_ulpin: str,
    building_code: int = 1,
    floor_number: int = 1,
    unit_number: int = 1,
) -> str:
    """
    Deterministic 21-digit numeric fallback:
    <14-digit parent><3-digit building><2-digit floor><2-digit unit>
    """
    parent = normalize_2d_ulpin(parent_ulpin)
    b_code = max(1, min(999, int(building_code)))
    f_code = max(0, min(99, int(floor_number)))
    u_code = max(1, min(99, int(unit_number)))
    return f"{parent}{b_code:03d}{f_code:02d}{u_code:02d}"

@dataclass
class CadastreUnit:
    id: str
    name: str
    type: str  # BUILDING, FLAT, PARKING, PLOT, STAIR, FIRE_EXIT, PARK, LAWN, CELLAR, TERRACE, RAILWAY_TRACK, PLATFORM, STATION, ROAD, STATUE, GOVT_OFFICE
    floor: str  # G00, F01, F02, F03, B01, R00, or F00-F03
    space_class: str  # V, S, U, E
    rights: str  # PRV, COM, GOV, RLW, PUB, UTL, CML
    unit_id: str  # e.g. A101, PRK01, TRK_UP, ROAD_M01, STATUE01, SEC01
    ulpin_3d: str  # Official format
    ulpin_numeric: str  # 21-digit format
    owner: str
    description: str
    parent_2d_ulpin: str
    category: str = "BUILDINGS"  # RAILWAY, ROADS, GOVT_SPACES, MONUMENTS, BUILDINGS, COMMON_SPACES
    z_min: float = 0.0
    z_max: float = 3.0
    carpet_area_sqm: float = 0.0
    carpet_area_sqft: float = 0.0
    bbox: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Relationship:
    source_id: str
    target_id: str
    type: str  # LOCATED_IN, OWNER_ASSOCIATED, COMMON_FACILITY_ACCESS

class CadastreRegistry:
    def __init__(self, parent_2d_ulpin: str = DEFAULT_PARENT_ULPIN):
        self.parent_2d_ulpin = normalize_2d_ulpin(parent_2d_ulpin)
        self.units: Dict[str, CadastreUnit] = {}
        self.relationships: List[Relationship] = []

    def add_unit(self, unit: CadastreUnit):
        self.units[unit.id] = unit

    def add_relationship(self, source_id: str, target_id: str, rel_type: str):
        self.relationships.append(Relationship(source_id=source_id, target_id=target_id, type=rel_type))

    def get_unit(self, unit_id: str) -> Optional[CadastreUnit]:
        return self.units.get(unit_id)

    def get_related(self, unit_id: str) -> List[Dict[str, Any]]:
        results = []
        for rel in self.relationships:
            if rel.source_id == unit_id and rel.target_id in self.units:
                results.append({
                    "relation": rel.type,
                    "target": asdict(self.units[rel.target_id]),
                    "direction": "outbound"
                })
            elif rel.target_id == unit_id and rel.source_id in self.units:
                results.append({
                    "relation": rel.type,
                    "target": asdict(self.units[rel.source_id]),
                    "direction": "inbound"
                })
        return results

    def check_3d_disputes(self) -> List[Dict[str, Any]]:
        disputes = []
        private_units = [u for u in self.units.values() if u.rights == "PRV" and u.type in ("FLAT", "TERRACE")]
        for i in range(len(private_units)):
            for j in range(i + 1, len(private_units)):
                u1, u2 = private_units[i], private_units[j]
                if u1.bbox and u2.bbox:
                    overlap_x = max(0.0, min(u1.bbox["x_max"], u2.bbox["x_max"]) - max(u1.bbox["x_min"], u2.bbox["x_min"]))
                    overlap_y = max(0.0, min(u1.bbox["y_max"], u2.bbox["y_max"]) - max(u1.bbox["y_min"], u2.bbox["y_min"]))
                    overlap_z = max(0.0, min(u1.z_max, u2.z_max) - max(u1.z_min, u2.z_min))
                    if overlap_x > 0.05 and overlap_y > 0.05 and overlap_z > 0.05:
                        clash_vol = overlap_x * overlap_y * overlap_z
                        disputes.append({
                            "type": "3D_VOLUMETRIC_CLASH",
                            "severity": "CRITICAL",
                            "unit_a": u1.id,
                            "unit_b": u2.id,
                            "ulpin_a": u1.ulpin_3d,
                            "ulpin_b": u2.ulpin_3d,
                            "clash_volume_m3": round(clash_vol, 2),
                            "postgis_function": "ST_3DIntersects(geom_a, geom_b) = TRUE",
                            "message": f"Illegal 3D volumetric overlap detected between {u1.name} and {u2.name} ({round(clash_vol, 2)} m³ clash)."
                        })

        for u in self.units.values():
            if u.metadata.get("rera_registered_sqm"):
                registered = float(u.metadata["rera_registered_sqm"])
                measured = u.carpet_area_sqm
                if registered > 0 and measured < registered:
                    shortfall_pct = round(((registered - measured) / registered) * 100, 2)
                    if shortfall_pct > 5.0:
                        disputes.append({
                            "type": "RERA_CARPET_DEFICIT",
                            "severity": "HIGH",
                            "unit_id": u.id,
                            "ulpin_3d": u.ulpin_3d,
                            "registered_sqm": registered,
                            "measured_sqm": measured,
                            "shortfall_pct": shortfall_pct,
                            "statutory_action": "Auto-generate RERA Sec. 14 Defect Notice + Statutory Fine",
                            "message": f"{u.name}: Internal usable carpet area ({measured} m²) has a {shortfall_pct}% shortfall against registered deed title ({registered} m²)."
                        })
        return disputes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parent_2d_ulpin": self.parent_2d_ulpin,
            "units": [asdict(u) for u in self.units.values()],
            "relationships": [asdict(r) for r in self.relationships],
            "disputes": self.check_3d_disputes(),
            "summary": {
                "total_units": len(self.units),
                "private_flats": len([u for u in self.units.values() if u.type == "FLAT"]),
                "public_spaces": len([u for u in self.units.values() if u.rights == "COM"]),
                "parking_slots": len([u for u in self.units.values() if u.type == "PARKING"]),
                "floors": sorted(list(set(u.floor for u in self.units.values()))),
            }
        }

def build_default_sih_cadastre(parent_ulpin: str = DEFAULT_PARENT_ULPIN) -> CadastreRegistry:
    reg = CadastreRegistry(parent_ulpin)
    p = reg.parent_2d_ulpin

    # 1. Building Block A
    bldg = CadastreUnit(
        id="building_a",
        name="Block A",
        type="BUILDING",
        floor="G00",
        space_class="V",
        rights="COM",
        unit_id="BLKA",
        ulpin_3d=make_official_3d_ulpin(p, "G00", "V", "COM", "BLKA", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 1),
        owner="Community",
        description="Main 4-storey residential apartment building",
        parent_2d_ulpin=p,
        z_min=0.0,
        z_max=12.0,
        carpet_area_sqm=384.0,
        carpet_area_sqft=4133.0,
        bbox={"x_min": -4.0, "x_max": 4.0, "y_min": -6.0, "y_max": 6.0, "z_min": 0.0, "z_max": 12.0}
    )
    reg.add_unit(bldg)

    # 2. Private Flats (Floor 1, Floor 2, Floor 3)
    flat_configs = [
        ("flat_101", "Flat 101", "F01", "A101", "Owner A (Suresh Gowda)", 0.0, 3.0, 85.0, 915.0, [-3.8, -0.2, -5.5, 5.5], 1, 1),
        ("flat_102", "Flat 102", "F01", "A102", "Owner B (Priya Sharma)", 0.0, 3.0, 82.5, 888.0, [0.2, 3.8, -5.5, 5.5], 1, 2),
        ("flat_201", "Flat 201", "F02", "A201", "Owner A (Suresh Gowda)", 3.0, 6.0, 85.0, 915.0, [-3.8, -0.2, -5.5, 5.5], 2, 1),
        ("flat_202", "Flat 202", "F02", "A202", "Owner C (Vikram Rao)", 3.0, 6.0, 82.5, 888.0, [0.2, 3.8, -5.5, 5.5], 2, 2),
        ("flat_301", "Flat 301", "F03", "A301", "Owner D (Ramesh Gowda)", 6.0, 9.0, 84.2, 906.0, [-3.8, -0.2, -5.5, 5.5], 3, 1),
        ("flat_302", "Flat 302", "F03", "A302", "Owner E (Suresh Patel)", 6.0, 9.0, 82.5, 888.0, [0.2, 3.8, -5.5, 5.5], 3, 2),
    ]

    for fid, name, flr, uid, owner, z0, z1, sqm, sqft, bb, fnum, unum in flat_configs:
        unit = CadastreUnit(
            id=fid,
            name=name,
            type="FLAT",
            floor=flr,
            space_class="V",
            rights="PRV",
            unit_id=uid,
            ulpin_3d=make_official_3d_ulpin(p, flr, "V", "PRV", uid, "V01"),
            ulpin_numeric=make_numeric_3d_ulpin(p, 1, fnum, unum),
            owner=owner,
            description=f"Private residential apartment unit on {flr}",
            parent_2d_ulpin=p,
            z_min=z0,
            z_max=z1,
            carpet_area_sqm=sqm,
            carpet_area_sqft=sqft,
            bbox={"x_min": bb[0], "x_max": bb[1], "y_min": bb[2], "y_max": bb[3], "z_min": z0, "z_max": z1},
            metadata={"rera_registered_sqm": 98.2 if fid == "flat_301" else sqm}
        )
        reg.add_unit(unit)
        reg.add_relationship(fid, "building_a", "LOCATED_IN")

    # Parking
    p1 = CadastreUnit(
        id="parking_p01", name="Parking P01", type="PARKING", floor="G00", space_class="S", rights="PRV",
        unit_id="PRK01", ulpin_3d=make_official_3d_ulpin(p, "G00", "S", "PRV", "PRK01", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 10), owner="Owner A (Suresh Gowda)",
        description="Assigned private parking bay for Flat 101/201", parent_2d_ulpin=p,
        z_min=0.0, z_max=0.3, carpet_area_sqm=12.5, carpet_area_sqft=135.0,
        bbox={"x_min": -6.5, "x_max": -4.2, "y_min": 2.0, "y_max": 4.5, "z_min": 0.0, "z_max": 0.3}
    )
    p2 = CadastreUnit(
        id="parking_p02", name="Parking P02", type="PARKING", floor="G00", space_class="S", rights="PRV",
        unit_id="PRK02", ulpin_3d=make_official_3d_ulpin(p, "G00", "S", "PRV", "PRK02", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 11), owner="Owner B (Priya Sharma)",
        description="Assigned private parking bay for Flat 102", parent_2d_ulpin=p,
        z_min=0.0, z_max=0.3, carpet_area_sqm=12.5, carpet_area_sqft=135.0,
        bbox={"x_min": 4.2, "x_max": 6.5, "y_min": 2.0, "y_max": 4.5, "z_min": 0.0, "z_max": 0.3}
    )
    reg.add_unit(p1)
    reg.add_unit(p2)
    reg.add_relationship("flat_101", "parking_p01", "OWNER_ASSOCIATED")
    reg.add_relationship("flat_201", "parking_p01", "OWNER_ASSOCIATED")
    reg.add_relationship("flat_102", "parking_p02", "OWNER_ASSOCIATED")

    # Associated Plot 17
    plot17 = CadastreUnit(
        id="plot_17", name="Associated Plot 17", type="PLOT", floor="G00", space_class="S", rights="PRV",
        unit_id="P17", ulpin_3d=make_official_3d_ulpin(p, "G00", "S", "PRV", "P17", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 17), owner="Owner A (Suresh Gowda)",
        description="Private outdoor garden plot attached to Ground Floor", parent_2d_ulpin=p,
        z_min=0.0, z_max=0.2, carpet_area_sqm=28.0, carpet_area_sqft=301.0,
        bbox={"x_min": -6.5, "x_max": -4.2, "y_min": -4.5, "y_max": -1.5, "z_min": 0.0, "z_max": 0.2}
    )
    reg.add_unit(plot17)
    reg.add_relationship("flat_101", "plot_17", "OWNER_ASSOCIATED")
    reg.add_relationship("flat_201", "plot_17", "OWNER_ASSOCIATED")

    # Common facilities
    stairs = CadastreUnit(
        id="stairs_s1", name="Staircase S1", type="STAIR", floor="F00-F03", space_class="V", rights="COM",
        unit_id="STAIR1", ulpin_3d=make_official_3d_ulpin(p, "G00", "V", "COM", "STAIR1", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 90), owner="Community",
        description="Common central staircase connecting all floor tiers", parent_2d_ulpin=p,
        z_min=0.0, z_max=12.0, carpet_area_sqm=18.0, carpet_area_sqft=194.0,
        bbox={"x_min": -0.8, "x_max": 0.8, "y_min": 3.8, "y_max": 5.8, "z_min": 0.0, "z_max": 12.0}
    )
    fire_exit = CadastreUnit(
        id="fire_f1", name="Fire Exit F1", type="FIRE_EXIT", floor="F00-F03", space_class="V", rights="COM",
        unit_id="FIRE01", ulpin_3d=make_official_3d_ulpin(p, "G00", "V", "COM", "FIRE01", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 91), owner="Community",
        description="Statutory emergency escape route and fire staircase", parent_2d_ulpin=p,
        z_min=0.0, z_max=12.0, carpet_area_sqm=12.0, carpet_area_sqft=129.0,
        bbox={"x_min": -0.8, "x_max": 0.8, "y_min": -5.8, "y_max": -4.2, "z_min": 0.0, "z_max": 12.0}
    )
    park = CadastreUnit(
        id="park_1", name="Community Park", type="PARK", floor="G00", space_class="S", rights="COM",
        unit_id="PARK01", ulpin_3d=make_official_3d_ulpin(p, "G00", "S", "COM", "PARK01", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 92), owner="Community",
        description="Shared recreational green park and playground", parent_2d_ulpin=p,
        z_min=0.0, z_max=0.2, carpet_area_sqm=120.0, carpet_area_sqft=1292.0,
        bbox={"x_min": -9.0, "x_max": -5.0, "y_min": -7.0, "y_max": 7.0, "z_min": 0.0, "z_max": 0.2}
    )
    lawn = CadastreUnit(
        id="lawn_1", name="Community Lawn", type="LAWN", floor="G00", space_class="S", rights="COM",
        unit_id="LAWN01", ulpin_3d=make_official_3d_ulpin(p, "G00", "S", "COM", "LAWN01", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 93), owner="Community",
        description="Landscaped common front lawn and pathway", parent_2d_ulpin=p,
        z_min=0.0, z_max=0.2, carpet_area_sqm=110.0, carpet_area_sqft=1184.0,
        bbox={"x_min": 5.0, "x_max": 9.0, "y_min": -7.0, "y_max": 7.0, "z_min": 0.0, "z_max": 0.2}
    )
    cellar = CadastreUnit(
        id="cellar_1", name="Cellar C1", type="CELLAR", floor="B01", space_class="U", rights="COM",
        unit_id="CELLAR1", ulpin_3d=make_official_3d_ulpin(p, "B01", "U", "COM", "CELLAR1", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 0, 94), owner="Community",
        description="Underground utility basement, water tanks, electrical pump room", parent_2d_ulpin=p,
        z_min=-3.0, z_max=0.0, carpet_area_sqm=140.0, carpet_area_sqft=1506.0,
        bbox={"x_min": -3.8, "x_max": 3.8, "y_min": -5.5, "y_max": 5.5, "z_min": -3.0, "z_max": 0.0}
    )
    terrace = CadastreUnit(
        id="terrace_1", name="Terrace T1", type="TERRACE", floor="R00", space_class="E", rights="COM",
        unit_id="TERR01", ulpin_3d=make_official_3d_ulpin(p, "R00", "E", "COM", "TERR01", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 99, 1), owner="Community",
        description="Common rooftop terrace open space and solar installation deck", parent_2d_ulpin=p,
        z_min=9.0, z_max=12.0, carpet_area_sqm=165.0, carpet_area_sqft=1776.0,
        bbox={"x_min": -3.8, "x_max": 3.8, "y_min": -5.5, "y_max": 5.5, "z_min": 9.0, "z_max": 12.0}
    )

    for facility in [stairs, fire_exit, park, lawn, cellar, terrace]:
        reg.add_unit(facility)
        for fid, _, _, _, _, _, _, _, _, _, _, _ in flat_configs:
            reg.add_relationship(fid, facility.id, "COMMON_FACILITY_ACCESS")

    # Planted 3D Clash on roof
    t_a = CadastreUnit(
        id="terrace_a", name="Terrace TR01 (Unit 401 Claim)", type="TERRACE", floor="R00", space_class="E", rights="PRV",
        unit_id="TR01", ulpin_3d=make_official_3d_ulpin(p, "R00", "E", "PRV", "TR01", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 99, 10), owner="Owner D (Ramesh Gowda)",
        description="Private roof terrace exclusive deed claim", parent_2d_ulpin=p,
        z_min=9.0, z_max=12.0, carpet_area_sqm=48.0, carpet_area_sqft=516.0,
        bbox={"x_min": -3.8, "x_max": 0.5, "y_min": -3.0, "y_max": 3.0, "z_min": 9.0, "z_max": 12.0}
    )
    t_b = CadastreUnit(
        id="terrace_b", name="Terrace TR02 (Unit 402 Claim)", type="TERRACE", floor="R00", space_class="E", rights="PRV",
        unit_id="TR02", ulpin_3d=make_official_3d_ulpin(p, "R00", "E", "PRV", "TR02", "V01"),
        ulpin_numeric=make_numeric_3d_ulpin(p, 1, 99, 11), owner="Owner E (Suresh Patel)",
        description="Disputed overlapping roof terrace claim", parent_2d_ulpin=p,
        z_min=9.0, z_max=12.0, carpet_area_sqm=46.0, carpet_area_sqft=495.0,
        bbox={"x_min": -0.8, "x_max": 3.8, "y_min": -3.0, "y_max": 3.0, "z_min": 9.0, "z_max": 12.0}
    )
    reg.add_unit(t_a)
    reg.add_unit(t_b)

    return reg
