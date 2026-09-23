# V-CAD: Automated 2D Blueprint to 3D Cadastre Engine & 3D ULPIN Assignment
### Smart India Hackathon (SIH 2026) - SVAMITVA / DILRMP 3D Geospatial Cadastre

**Repository**: [https://github.com/edigasaivikas-143/sih-vcad](https://github.com/edigasaivikas-143/sih-vcad)  
**Live Render Deployment**: Deployable via 1-click on [Render.com](https://render.com) using render.yaml

---

## Authorized Government Access Credentials

| Role | Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Citizen (View-Only)** | user@ulpin.gov.in | user@1221 | Search properties, inspect verified records, view 3D cadastre |
| **Cadastral Administrator (Full Access)** | admin@ulpin.gov.in | adm@4523 | Register/delete public domains, AI blueprint extrusion, deed issuance |

---

## One-Click Deploy on Render

This repository includes a native render.yaml configuration for seamless deployment on Render:

1. Connect the repository: https://github.com/edigasaivikas-143/sih-vcad
2. Go to Render Dashboard (https://dashboard.render.com) -> New -> Blueprint.
3. Connect the sih-vcad repository.
4. Render will automatically detect render.yaml and configure:
   - Environment: Python 3.11
   - Build Command: pip install --upgrade pip && pip install -r requirements.txt
   - Start Command: python server.py
   - Health Check: /healthz
5. Click Apply - your live 3D ULPIN engine will be up in 2 minutes with automatic HTTPS!

---

## Key Features

1. Multi-Elevation Cadastre & Specialized Infrastructure:
   - Subterranean Tunnels: Space Class U (Underground Sub-surface, Z = -14.0m to -6.5m, Level B02), twin tubes, emergency cross-passages, deep ventilation shafts.
   - Elevated Bridges & Viaducts: Space Class E (Elevated Air-rights, Z = +10.0m to +11.2m, Level F01), concrete piers and navigable river channels in Space Class S.
   - Railway Tracks & Terminals: Grade-separated railway corridors, platform rights, signaling infrastructure.
   - National Highway Corridors: Carriageway ROW, medians, service lanes, grade-separated flyovers.
   - Monuments & Statues: Public airspace reservations, tourist plazas, municipal maintenance parcels.

2. Official SVAMITVA / LADM 3D ULPIN Generator:
   - Standard: [Parent 2D ULPIN]-[Vertical Floor Tier]-[Space Class]-[Rights Type]-[Unit ID]-[Version]
   - Example (Tunnel): 28045678901240-B02-U-PUB-TNL_TUBE1-V01
   - Example (Bridge): 28045678901239-F01-E-PUB-BRG_DECK01-V01
   - Generates numeric cadastral identifiers (e.g. 280456789012400020201) for database indexing.

3. Autonomous Computer Vision Extrusion (OpenCV):
   - Reads raw architectural blueprints, CAD elevation drawings, and structural sections.
   - Detects outer perimeters, structural elements, corridors, and functional zones.
   - Preserves metric building aspect ratios and computes accurate carpet areas.

4. Public Infrastructure Domain Registry:
   - Filterable view dedicated to government sectors (Railways, Roads, Bridges, Tunnels, Statues, Govt Spaces).
   - Administrator CRUD controls for registering and removing public infrastructure assets.

5. Interactive 3D WebGL Multi-Floor & Layer Explorer:
   - Built on Three.js with OrbitControls.
   - Interactive unit selection with live Inspector modal showing area, volume, height, elevation range, owner, and tenure.
   - Floor slicing and Category/Sector layer isolation filters.

6. Interoperable Geospatial 3D Exports:
   - Streams 3D Wavefront .obj files for AutoCAD, Blender, or BIM engines.
   - Streams 3D .geojson files for QGIS, ArcGIS, or Mapbox.

---

## Local Development & Setup

### 1. Requirements
- Python 3.9+ (Python 3.11 recommended)
- Modern Web Browser (Chrome, Edge, Firefox, Brave)

### 2. Install Dependencies
pip install -r requirements.txt

### 3. Launch Local Server
python server.py 8080

Open your browser at: http://localhost:8080

### 4. Run Automated Test Suite
python test_suite.py

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | /healthz | System health and daemon status probe. |
| GET | /api/properties | Retrieves all registered 3D properties and infrastructure parcels. |
| GET | /api/infrastructure/categories | Returns count and listing of all public infrastructure sectors. |
| GET | /api/infrastructure/specialized/{category} | Returns 3D cadastre model for tunnels, bridges, railways, roads, or statues. |
| POST | /api/vcad/process | Executes OpenCV blueprint analysis and returns extruded 3D cadastre. |
| GET | /api/vcad/cadastre/{ulpin_3d} | Returns 3D spatial model for specific 3D ULPIN. |
| GET | /api/export/obj | Streams 3D Wavefront .obj CAD geometry. |
| GET | /api/export/geojson | Streams 3D GeoJSON spatial polygons. |

---

## Smart India Hackathon (SIH 2026) Compliance
- Built in alignment with SVAMITVA Scheme Guidelines, DoLR National Geospatial Policy, and LADM (ISO 19152) 3D spatial cadastre standards.
- Designed and developed by Team V-CAD for SIH 2026.
