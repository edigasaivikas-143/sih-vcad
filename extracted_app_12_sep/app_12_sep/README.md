# 3D ULPIN Generation & Vertical Property Mapping (Localhost Prototype)
### Smart India Hackathon (SIH) — SVAMITVA / DILRMP 3.0 Cadastre Framework

This directory (pp_12_sep) contains the standalone, fully-functional localhost prototype for **3D ULPIN Generation & Vertical Property Mapping**. It integrates blueprint computer vision, multi-level 3D cadastre extrusion, Three.js volumetric visualization, topology/rights validation, and SVAMITVA 3D Property Certificate generation.

---

## Quick Start (How to Run)

### Method 1: One-Click Batch Launcher (Windows)
Double-click:

un_localhost.bat

*Automatically frees port 8080 if previously occupied, launches the server, and opens http://localhost:8080 in your browser.*

### Method 2: Manual Terminal Execution
`ash
# 1. Install dependencies (if not already installed)
pip install -r requirements.txt

# 2. Run the unified Starlette/Uvicorn server
python local_server.py 8080
`
Then navigate to: **http://localhost:8080**

---

## Directory Structure

`
app_12_sep/
├── local_server.py               # Unified Starlette/Uvicorn HTTP backend & REST API
├── run_localhost.bat             # One-click Windows launch script
├── requirements.txt              # Core python dependencies
├── test_multi_level.py           # Test runner for multi-level cadastre generation
├── vcad_engine_sih2026/          # V-CAD Core Engine
│   ├── blueprint_vision.py       # OpenCV blueprint analysis (walls, rooms, dimensions)
│   ├── cad_generator.py          # 3D cadastre builder, Z-range extrusion, OBJ/GeoJSON exporters
│   ├── ulpin_engine.py           # 3D ULPIN generator, validation rules, SHA-256 cert hashing
│   ├── sample_blueprints/        # Built-in reference floor plans
│   └── static/                   # 3D engine assets & Three.js viewer dependencies
├── frontend/                     # Interactive Web Application
│   ├── index.html                # Property registration, Z-axis inputs, 3D modal, certificate UI
│   ├── viewer3d.js               # Three.js 3D cadastre renderer (exploded view, isolation)
│   ├── OrbitControls.js          # WebGL camera controls
│   ├── three.min.js              # Three.js 3D WebGL library
│   ├── config.js                 # Frontend API configuration
│   └── favicon.svg               # Portal icon
├── storage/                      # Local Persistent Subsystem
│   ├── properties.json           # Registry database of demo and submitted properties
│   ├── blueprints/               # Uploaded blueprint storage per 3D ULPIN
│   └── models/                   # Cached .json, .obj, and .geojson volumetric 3D models
└── bp/                           # Pre-loaded sample floor & basement blueprints
    ├── F1.jpeg - F5.jpeg         # Above-ground floor blueprints (F1 to F5)
    └── B1.jpeg - B4.jpeg         # Sub-surface basement blueprints (B1 to B4)
`

---

## Live Demo Walkthrough (Round 1 & 2 Presentation Flow)

1. **Open Portal**: Navigate to http://localhost:8080.
2. **Explore Pre-Registered Demo Properties**:
   - 12345678901234-F03-V-PRV-A301-V01 (*Flat 301 — Reference problem scenario from slide deck*).
   - 11223344556677-F03-V-PRV-C301-V01 (*Royal Tower Unit C301 — 5 Floors, 2 Basements*).
3. **Register / Parameterize a Property**:
   - Set Parent ULPIN (e.g., 12345678901234).
   - Define Z-Bounds: Building Height (e.g. 15.0m, 5 Floors) and Building Depth (e.g. 6.0m, 2 Basements).
   - Select blueprints from the p/ folder matching floors 1-f5 and basements 1-b2.
   - Submit to automatically trigger Computer Vision floor parsing and 3D volumetric extrusion.
4. **Inspect 3D Cadastre**:
   - Click **Open 3D Model** to launch the Three.js viewport.
   - Adjust the **Explode View** slider to separate stacked floors and basements in the vertical axis.
   - Click individual volumetric units to inspect rights, area, bounds, and confidence score.
5. **Generate SVAMITVA 3D Property Certificate**:
   - Click **Generate 3D Certificate**.
   - View cryptographic SHA-256 verification hash, clean title guarantee, and QR code verification link.
6. **Export Interoperable Cadastre**:
   - Export standard **Wavefront .OBJ** 3D model for GIS/BIM software.
   - Export official **GeoJSON** 3D cadastre layer.
