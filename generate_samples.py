"""
Generate Realistic Architectural Sample Blueprints (JPG, PNG, SVG, JSON)
"""

from PIL import Image, ImageDraw, ImageFont
import json
from pathlib import Path

out_dir = Path("sample_blueprints")
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Generate 2-Unit Architectural Blueprint JPG (sample_floor_2unit.jpg)
w, h = 1200, 1600
img = Image.new("RGB", (w, h), color="#0c1d36")  # Blueprint dark blue
draw = ImageDraw.Draw(img)

# Grid lines
for x in range(0, w, 40):
    draw.line([(x, 0), (x, h)], fill="#142c52", width=1)
for y in range(0, h, 40):
    draw.line([(0, y), (w, y)], fill="#142c52", width=1)

# Major grid lines
for x in range(0, w, 200):
    draw.line([(x, 0), (x, h)], fill="#1d3d6f", width=1)
for y in range(0, h, 200):
    draw.line([(0, y), (w, y)], fill="#1d3d6f", width=1)

# Outer Building Wall Envelope (White/Cyan, thick)
margin_x, margin_y = 120, 160
bw, bh = w - 2 * margin_x, h - 2 * margin_y
draw.rectangle([margin_x, margin_y, margin_x + bw, margin_y + bh], outline="#00e5ff", width=8)

# Central Spine / Corridor (X = w//2 - 60 to w//2 + 60)
corr_x0 = w // 2 - 50
corr_x1 = w // 2 + 50
draw.line([(corr_x0, margin_y), (corr_x0, margin_y + bh)], fill="#00e5ff", width=6)
draw.line([(corr_x1, margin_y), (corr_x1, margin_y + bh)], fill="#00e5ff", width=6)

# Horizontal dividing walls (Floor splitting)
y_mid = margin_y + bh // 2
y_third1 = margin_y + bh // 3
y_third2 = margin_y + 2 * bh // 3

# Unit A (Left Flat) rooms
draw.line([(margin_x, y_third1), (corr_x0, y_third1)], fill="#00e5ff", width=5)
draw.line([(margin_x, y_third2), (corr_x0, y_third2)], fill="#00e5ff", width=5)
draw.line([(margin_x + (corr_x0 - margin_x)//2, margin_y), (margin_x + (corr_x0 - margin_x)//2, y_third1)], fill="#00e5ff", width=4)

# Unit B (Right Flat) rooms
draw.line([(corr_x1, y_third1), (margin_x + bw, y_third1)], fill="#00e5ff", width=5)
draw.line([(corr_x1, y_third2), (margin_x + bw, y_third2)], fill="#00e5ff", width=5)
draw.line([(corr_x1 + (margin_x + bw - corr_x1)//2, margin_y), (corr_x1 + (margin_x + bw - corr_x1)//2, y_third1)], fill="#00e5ff", width=4)

# Common Stairwell in Corridor (top)
stair_y0 = margin_y + 40
stair_y1 = margin_y + 280
draw.rectangle([corr_x0 + 6, stair_y0, corr_x1 - 6, stair_y1], outline="#ffd166", width=3)
for sy in range(stair_y0 + 20, stair_y1, 20):
    draw.line([(corr_x0 + 10, sy), (corr_x1 - 10, sy)], fill="#ffd166", width=2)

# Fire Exit in Corridor (bottom)
fire_y0 = margin_y + bh - 240
fire_y1 = margin_y + bh - 40
draw.rectangle([corr_x0 + 6, fire_y0, corr_x1 - 6, fire_y1], outline="#ff5252", width=3)
draw.line([(corr_x0 + 10, fire_y0 + 10), (corr_x1 - 10, fire_y1 - 10)], fill="#ff5252", width=2)
draw.line([(corr_x0 + 10, fire_y1 - 10), (corr_x1 - 10, fire_y0 + 10)], fill="#ff5252", width=2)

# Balconies (Outward extensions)
draw.rectangle([margin_x - 40, margin_y + 100, margin_x, margin_y + 350], outline="#00e5ff", width=3)
draw.rectangle([margin_x + bw, margin_y + 100, margin_x + bw + 40, margin_y + 350], outline="#00e5ff", width=3)

# Blueprint Labels & Annotations
try:
    font = ImageFont.load_default()
except Exception:
    font = None

draw.text((margin_x + 80, margin_y + 80), "UNIT A: LIVING ROOM (A101)", fill="#ffffff", font=font)
draw.text((margin_x + 80, y_third1 + 80), "UNIT A: MASTER BEDROOM", fill="#ffffff", font=font)
draw.text((margin_x + 80, y_third2 + 80), "UNIT A: KITCHEN / DINING", fill="#ffffff", font=font)

draw.text((corr_x1 + 80, margin_y + 80), "UNIT B: LIVING ROOM (A102)", fill="#ffffff", font=font)
draw.text((corr_x1 + 80, y_third1 + 80), "UNIT B: MASTER BEDROOM", fill="#ffffff", font=font)
draw.text((corr_x1 + 80, y_third2 + 80), "UNIT B: KITCHEN / DINING", fill="#ffffff", font=font)

draw.text((w // 2 - 40, stair_y0 - 25), "STAIRS (S1)", fill="#ffd166", font=font)
draw.text((w // 2 - 45, fire_y1 + 10), "FIRE EXIT (F1)", fill="#ff5252", font=font)
draw.text((w // 2 - 40, y_mid), "CORRIDOR", fill="#00e5ff", font=font)

# Title Stamp Block
stamp_x0, stamp_y0 = margin_x, margin_y + bh + 25
draw.rectangle([stamp_x0, stamp_y0, stamp_x0 + 400, stamp_y0 + 70], outline="#00e5ff", width=2)
draw.text((stamp_x0 + 15, stamp_y0 + 10), "PROJECT: SVAMITVA 3D CADASTRE V-CAD", fill="#ffd166", font=font)
draw.text((stamp_x0 + 15, stamp_y0 + 28), "BASE 2D ULPIN: 12345678901234 | SCALE 1:100", fill="#ffffff", font=font)
draw.text((stamp_x0 + 15, stamp_y0 + 46), "LEVEL: TYPICAL RESIDENTIAL FLOOR (F01 - F03)", fill="#67e8f9", font=font)

# Dimension line
draw.line([(margin_x, margin_y - 30), (margin_x + bw, margin_y - 30)], fill="#00e5ff", width=2)
draw.line([(margin_x, margin_y - 40), (margin_x, margin_y - 20)], fill="#00e5ff", width=2)
draw.line([(margin_x + bw, margin_y - 40), (margin_x + bw, margin_y - 20)], fill="#00e5ff", width=2)
draw.text((w // 2 - 40, margin_y - 50), "16.0 METERS", fill="#00e5ff", font=font)

img.save(out_dir / "sample_floor_2unit.jpg", quality=95)
print("[OK] Created sample_floor_2unit.jpg")

# 2. Also save as PNG
img.save(out_dir / "sample_floor_2unit.png")
print("[OK] Created sample_floor_2unit.png")

# 3. Create sample_blueprint.svg
svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1200" width="800" height="1200" style="background:#071426;">
  <defs>
    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#122847" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="800" height="1200" fill="url(#grid)" />
  
  <!-- Outer Walls (16m x 24m scaled) -->
  <rect x="100" y="100" width="600" height="1000" fill="#0d2342" stroke="#00e5ff" stroke-width="6" />
  
  <!-- Central Corridor -->
  <rect id="corridor" x="370" y="100" width="60" height="1000" fill="#0a1a33" stroke="#00e5ff" stroke-width="4" />
  
  <!-- Unit A Rooms (Left) -->
  <rect id="A101_Living" x="100" y="100" width="270" height="350" fill="#112d54" stroke="#00e5ff" stroke-width="3" />
  <rect id="A101_Bedroom" x="100" y="450" width="270" height="350" fill="#112d54" stroke="#00e5ff" stroke-width="3" />
  <rect id="A101_Kitchen" x="100" y="800" width="270" height="300" fill="#112d54" stroke="#00e5ff" stroke-width="3" />
  
  <!-- Unit B Rooms (Right) -->
  <rect id="A102_Living" x="430" y="100" width="270" height="350" fill="#112d54" stroke="#00e5ff" stroke-width="3" />
  <rect id="A102_Bedroom" x="430" y="450" width="270" height="350" fill="#112d54" stroke="#00e5ff" stroke-width="3" />
  <rect id="A102_Kitchen" x="430" y="800" width="270" height="300" fill="#112d54" stroke="#00e5ff" stroke-width="3" />
  
  <!-- Common Facilities -->
  <rect id="STAIR1" x="375" y="130" width="50" height="180" fill="#2d3748" stroke="#ffd166" stroke-width="3" />
  <rect id="FIRE01" x="375" y="900" width="50" height="160" fill="#2d3748" stroke="#ff5252" stroke-width="3" />
  
  <!-- Text Labels -->
  <text x="140" y="270" fill="#ffffff" font-family="monospace" font-size="16" font-weight="bold">FLAT 101 (UNIT A)</text>
  <text x="140" y="295" fill="#67e8f9" font-family="monospace" font-size="12">85.0 SQM | 3D-ULPIN: A101</text>
  
  <text x="470" y="270" fill="#ffffff" font-family="monospace" font-size="16" font-weight="bold">FLAT 102 (UNIT B)</text>
  <text x="470" y="295" fill="#67e8f9" font-family="monospace" font-size="12">82.5 SQM | 3D-ULPIN: A102</text>

  <text x="382" y="225" fill="#ffd166" font-family="monospace" font-size="12" transform="rotate(-90 382 225)">STAIRS S1</text>
  <text x="382" y="990" fill="#ff5252" font-family="monospace" font-size="12" transform="rotate(-90 382 990)">FIRE EXIT</text>
  
  <text x="100" y="60" fill="#ffd166" font-family="monospace" font-size="14" font-weight="bold">PARENT 2D ULPIN: 12345678901234</text>
</svg>'''

with open(out_dir / "sample_blueprint.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("[OK] Created sample_blueprint.svg")

# 4. Save sample_cadastre.json (Golden dataset)
cadastre_data = {
  "prototype": True,
  "source": "Official SVAMITVA 3D Cadastre Dataset",
  "parent_2d_ulpin": "12345678901234",
  "objects": [
    {
      "id": "building_a",
      "name": "Block A",
      "type": "BUILDING",
      "floor": "G00",
      "space_class": "V",
      "rights": "COM",
      "unit_id": "BLKA",
      "ulpin_3d": "12345678901234-G00-V-COM-BLKA-V01",
      "owner": "Community",
      "description": "Main apartment building",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "flat_101",
      "name": "Flat 101",
      "type": "FLAT",
      "floor": "F01",
      "space_class": "V",
      "rights": "PRV",
      "unit_id": "A101",
      "ulpin_3d": "12345678901234-F01-V-PRV-A101-V01",
      "owner": "Owner A (Suresh Gowda)",
      "description": "Private residential unit",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "flat_102",
      "name": "Flat 102",
      "type": "FLAT",
      "floor": "F01",
      "space_class": "V",
      "rights": "PRV",
      "unit_id": "A102",
      "ulpin_3d": "12345678901234-F01-V-PRV-A102-V01",
      "owner": "Owner B (Priya Sharma)",
      "description": "Private residential unit",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "flat_201",
      "name": "Flat 201",
      "type": "FLAT",
      "floor": "F02",
      "space_class": "V",
      "rights": "PRV",
      "unit_id": "A201",
      "ulpin_3d": "12345678901234-F02-V-PRV-A201-V01",
      "owner": "Owner A (Suresh Gowda)",
      "description": "Private residential unit",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "flat_202",
      "name": "Flat 202",
      "type": "FLAT",
      "floor": "F02",
      "space_class": "V",
      "rights": "PRV",
      "unit_id": "A202",
      "ulpin_3d": "12345678901234-F02-V-PRV-A202-V01",
      "owner": "Owner C (Vikram Rao)",
      "description": "Private residential unit",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "flat_301",
      "name": "Flat 301",
      "type": "FLAT",
      "floor": "F03",
      "space_class": "V",
      "rights": "PRV",
      "unit_id": "A301",
      "ulpin_3d": "12345678901234-F03-V-PRV-A301-V01",
      "owner": "Owner D (Ramesh Gowda)",
      "description": "Private residential unit (RERA Deficit Flagged)",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "flat_302",
      "name": "Flat 302",
      "type": "FLAT",
      "floor": "F03",
      "space_class": "V",
      "rights": "PRV",
      "unit_id": "A302",
      "ulpin_3d": "12345678901234-F03-V-PRV-A302-V01",
      "owner": "Owner E (Suresh Patel)",
      "description": "Private residential unit",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "parking_p01",
      "name": "Parking P01",
      "type": "PARKING",
      "floor": "G00",
      "space_class": "S",
      "rights": "PRV",
      "unit_id": "PRK01",
      "ulpin_3d": "12345678901234-G00-S-PRV-PRK01-V01",
      "owner": "Owner A (Suresh Gowda)",
      "description": "Assigned parking for Owner A",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "parking_p02",
      "name": "Parking P02",
      "type": "PARKING",
      "floor": "G00",
      "space_class": "S",
      "rights": "PRV",
      "unit_id": "PRK02",
      "ulpin_3d": "12345678901234-G00-S-PRV-PRK02-V01",
      "owner": "Owner B (Priya Sharma)",
      "description": "Assigned parking for Owner B",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "plot_17",
      "name": "Associated Plot 17",
      "type": "PLOT",
      "floor": "G00",
      "space_class": "S",
      "rights": "PRV",
      "unit_id": "P17",
      "ulpin_3d": "12345678901234-G00-S-PRV-P17-V01",
      "owner": "Owner A (Suresh Gowda)",
      "description": "Parent/associated plot",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "stairs_s1",
      "name": "Staircase S1",
      "type": "STAIR",
      "floor": "F00-F03",
      "space_class": "V",
      "rights": "COM",
      "unit_id": "STAIR1",
      "ulpin_3d": "12345678901234-G00-V-COM-STAIR1-V01",
      "owner": "Community",
      "description": "Common staircase",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "fire_f1",
      "name": "Fire Exit F1",
      "type": "FIRE_EXIT",
      "floor": "F00-F03",
      "space_class": "V",
      "rights": "COM",
      "unit_id": "FIRE01",
      "ulpin_3d": "12345678901234-G00-V-COM-FIRE01-V01",
      "owner": "Community",
      "description": "Common emergency exit",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "park_1",
      "name": "Community Park",
      "type": "PARK",
      "floor": "G00",
      "space_class": "S",
      "rights": "COM",
      "unit_id": "PARK01",
      "ulpin_3d": "12345678901234-G00-S-COM-PARK01-V01",
      "owner": "Community",
      "description": "Common green area",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "lawn_1",
      "name": "Community Lawn",
      "type": "LAWN",
      "floor": "G00",
      "space_class": "S",
      "rights": "COM",
      "unit_id": "LAWN01",
      "ulpin_3d": "12345678901234-G00-S-COM-LAWN01-V01",
      "owner": "Community",
      "description": "Common lawn",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "cellar_1",
      "name": "Cellar C1",
      "type": "CELLAR",
      "floor": "B01",
      "space_class": "U",
      "rights": "COM",
      "unit_id": "CELLAR1",
      "ulpin_3d": "12345678901234-B01-U-COM-CELLAR1-V01",
      "owner": "Community",
      "description": "Common underground cellar",
      "parent_2d_ulpin": "12345678901234"
    },
    {
      "id": "terrace_1",
      "name": "Terrace T1",
      "type": "TERRACE",
      "floor": "R00",
      "space_class": "E",
      "rights": "COM",
      "unit_id": "TERR01",
      "ulpin_3d": "12345678901234-R00-E-COM-TERR01-V01",
      "owner": "Community",
      "description": "Common roof terrace",
      "parent_2d_ulpin": "12345678901234"
    }
  ],
  "relationships": [
    {"source_id": "flat_101", "target_id": "parking_p01", "type": "OWNER_ASSOCIATED"},
    {"source_id": "flat_101", "target_id": "plot_17", "type": "OWNER_ASSOCIATED"},
    {"source_id": "flat_101", "target_id": "building_a", "type": "LOCATED_IN"},
    {"source_id": "flat_102", "target_id": "parking_p02", "type": "OWNER_ASSOCIATED"},
    {"source_id": "flat_102", "target_id": "building_a", "type": "LOCATED_IN"},
    {"source_id": "flat_201", "target_id": "parking_p01", "type": "OWNER_ASSOCIATED"},
    {"source_id": "flat_201", "target_id": "plot_17", "type": "OWNER_ASSOCIATED"},
    {"source_id": "flat_201", "target_id": "building_a", "type": "LOCATED_IN"},
    {"source_id": "flat_202", "target_id": "building_a", "type": "LOCATED_IN"},
    {"source_id": "flat_301", "target_id": "building_a", "type": "LOCATED_IN"},
    {"source_id": "flat_302", "target_id": "building_a", "type": "LOCATED_IN"},
    {"source_id": "flat_101", "target_id": "stairs_s1", "type": "COMMON_FACILITY_ACCESS"},
    {"source_id": "flat_101", "target_id": "fire_f1", "type": "COMMON_FACILITY_ACCESS"},
    {"source_id": "flat_101", "target_id": "park_1", "type": "COMMON_FACILITY_ACCESS"},
    {"source_id": "flat_101", "target_id": "lawn_1", "type": "COMMON_FACILITY_ACCESS"},
    {"source_id": "flat_101", "target_id": "cellar_1", "type": "COMMON_FACILITY_ACCESS"},
    {"source_id": "flat_101", "target_id": "terrace_1", "type": "COMMON_FACILITY_ACCESS"}
  ]
}

with open(out_dir / "sample_cadastre.json", "w", encoding="utf-8") as f:
    json.dump(cadastre_data, f, indent=2)
print("[OK] Created sample_cadastre.json")
