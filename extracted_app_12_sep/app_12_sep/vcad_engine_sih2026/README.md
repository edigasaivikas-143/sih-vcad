# V-CAD: Automated 2D Blueprint to 3D Cadastre Engine & 3D ULPIN Assignment
### Smart India Hackathon (SIH 2026) • SVAMITVA / DILRMP 3D Geospatial Cadastre

---

## ?? Executive Summary
**V-CAD** is an autonomous computer vision and cadastral engine that transforms raw 2D floor plans, architectural blueprints (JPG, PNG, SVG, JSON), and cross-sections into **interactive, volumetrically verified 3D digital cadastres** with **official 14+ digit 3D ULPINs** (Unique Land Parcel Identification Numbers) aligned with India's DILRMP / SVAMITVA spatial standards.

---

## ?? Key Features

1. **Autonomous Computer Vision Extrusion (OpenCV)**:
   - Ingests raw floor plan images without manual CAD tracing.
   - Detects outer perimeter walls, partition walls, doors, and functional zones (Living, Master Bedroom, Kitchen, Dining, Balcony, Terrace).
   - Preserves metric building aspect ratio and calculates true carpet area (^2$ and .ft$).

2. **Official 3D ULPIN Standard Generator**:
   - Implements the official hierarchical standard:
     [Parent 2D ULPIN]-[Vertical Floor Tier]-[Space Class]-[Rights Type]-[Unit ID]-[Version]
   - Example: 12345678901234-F01-V-PRV-A101_LIV-V01
   - Generates numeric cadastral identifiers (e.g. 123456789012340010101) for database indexing.

3. **Multi-Floor & Blueprint Repetition**:
   - Defaults strictly to 1 floor (+ clean terrace deck) for standard 2D floor plans.
   - Intelligently detects text annotations in blueprints (e.g. *"Typical Floor Plan (1st to 3rd)"*) to clone floor geometries with distinct floor tags (F01, F02, F03) and unique room ULPINs.

4. **Zero-Dispute Title Guarantee**:
   - Real-time 3D volumetric collision detection eliminates duplicate unit allocations and spatial title overlaps.
   - Clear distinction between Private Ownership Titles (PRV) and Common Public/Community Rights (COM).

5. **High-Performance 3D WebGL Viewer (Three.js)**:
   - Floor-by-floor inspection filter (All, F01, R00).
   - Vertical exploded view slider (0m to 100m separation).
   - Dynamic 3D HTML labels with automatic floor culling and toggle (ON/OFF).
   - High-resolution snapshot export (PNG).

6. **Interoperable Geospatial Export**:
   - **Wavefront OBJ (.obj)**: Standard 3D model with mesh vertices, faces, and material definitions.
   - **3D GeoJSON (.geojson)**: GIS-ready volumetric polygons with full cadastral properties.
   - **Digital Legal Deed Certificate**: Printable deed with QR verification code, 3D ULPIN, and owner details.

---

## ?? Project Structure

`
vcad_engine/
¦
+-- server.py               # Starlette + Uvicorn HTTP server & REST API endpoints
+-- blueprint_vision.py     # OpenCV computer vision extractor & room classifier
+-- cad_generator.py        # 3D geometry builder, OBJ exporter & GeoJSON generator
+-- ulpin_engine.py         # 3D ULPIN generator (alphanumeric & numeric DILRMP standards)
+-- test_suite.py           # Automated 11-point health check and validation suite
¦
+-- start_server.bat        # 1-click Windows startup script
+-- run_tests.bat           # 1-click test runner script
+-- requirements.txt        # Python dependency specifications
¦
+-- static/                 # Production WebGL Frontend
¦   +-- index.html          # Responsive single-page application UI
¦   +-- styles.css          # Cyberpunk / Cadastral GIS dark theme styling
¦   +-- app.js              # Application controller & API integration
¦   +-- viewer3d.js         # Three.js 3D viewport, orbit controls & labels
¦   +-- favicon.svg         # High-resolution vector icon
¦
+-- sample_blueprints/      # Pre-packaged test floor plans & cadastre datasets
+-- uploads/                # Dynamic storage for uploaded blueprints & exports
`

---

## ??? Quick Start Guide

### 1. Requirements
- Python 3.9 or higher
- Modern Web Browser (Chrome, Edge, Firefox, Brave)

### 2. Install Dependencies
`ash
pip install -r requirements.txt
`

### 3. Launch the Server
Double-click **start_server.bat** OR run:
`ash
python server.py 8080
`
Open your browser at:
?? **http://localhost:8080**

### 4. Run Automated Tests
`ash
python test_suite.py
`
*(Runs 11 automated verification tests covering CV analysis, ULPIN creation, OBJ/GeoJSON exports, and API endpoints).*

---

## ?? API Reference for Integration

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | /api/cadastre | Retrieves the active building cadastre model, geometry, and units. |
| POST | /api/upload | Ingests a 2D blueprint (content_base64), executes CV extrusion, assigns 3D ULPINs, and returns full 3D cadastre. |
| POST | /api/analyze-blueprint | Runs live computer vision analysis and returns detected room bounding boxes. |
| POST | /api/set-parent-ulpin | Updates the 14-digit parent land parcel ULPIN and re-keys all 3D units. |
| GET | /api/export/obj | Streams 3D Wavefront .obj file for AutoCAD, Blender, or GIS tools. |
| GET | /api/export/geojson | Streams 3D GeoJSON file for QGIS, ArcGIS, or Mapbox. |

---

## ?? Smart India Hackathon (SIH 2026) Notes
- Compliant with **SVAMITVA Scheme Guidelines** and **DoLR Spatial Data Infrastructure standards**.
- Fully autonomous processing pipeline: from raw photo/scan to legal 3D spatial register.
