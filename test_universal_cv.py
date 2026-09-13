import cv2
import numpy as np
from pathlib import Path

def extract_blueprint_cv(image_path: str, target_building_width_m: float = 12.0, floor_height_m: float = 2.80, floors_count: int = 1):
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    h_px, w_px = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Remove outer image borders / window frames
    margin_y = max(4, int(h_px * 0.03))
    margin_x = max(4, int(w_px * 0.03))
    gray[:margin_y, :] = 255
    gray[-margin_y:, :] = 255
    gray[:, :margin_x] = 255
    gray[:, -margin_x:] = 255
    
    # Invert if dark background (e.g. classic blueprint or dark mode)
    if np.mean(gray) < 127:
        gray = 255 - gray
        
    # Otsu binary thresholding
    _, bin_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Clean noise (remove single pixel specks)
    kernel_clean = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(bin_inv, cv2.MORPH_OPEN, kernel_clean)
    
    # Find building bounding box
    pts = cv2.findNonZero(cleaned)
    if pts is None:
        pts = cv2.findNonZero(bin_inv)
    bx, by, bw, bh = cv2.boundingRect(pts)
    
    # Metric scale
    scale = target_building_width_m / max(10, bw)
    bl_m = round(bh * scale, 2)
    cx_px = bx + bw / 2.0
    cy_px = by + bh / 2.0
    
    # Extract structural wall lines (horizontal and vertical)
    h_len = max(10, int(bw * 0.035))
    v_len = max(10, int(bh * 0.035))
    h_k = cv2.getStructuringElement(cv2.MORPH_RECT, (h_len, 1))
    v_k = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_len))
    h_walls = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, h_k)
    v_walls = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, v_k)
    walls_mask = cv2.bitwise_or(h_walls, v_walls)
    
    # Find walls contours
    wall_contours, _ = cv2.findContours(walls_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    walls_3d = []
    w_idx = 1
    
    # 4 Exterior Envelope Walls
    ext_th = 0.22
    walls_3d.append({
        "id": "ext_wall_north", "name": "North Exterior Wall", "wall_type": "EXTERIOR",
        "cx": 0.0, "cy": floor_height_m/2.0, "cz": -bl_m/2.0, "width": target_building_width_m, "height": floor_height_m, "depth": ext_th,
        "color": "#1e293b", "edge_color": "#38bdf8"
    })
    walls_3d.append({
        "id": "ext_wall_south", "name": "South Exterior Wall", "wall_type": "EXTERIOR",
        "cx": 0.0, "cy": floor_height_m/2.0, "cz": bl_m/2.0, "width": target_building_width_m, "height": floor_height_m, "depth": ext_th,
        "color": "#1e293b", "edge_color": "#38bdf8"
    })
    walls_3d.append({
        "id": "ext_wall_west", "name": "West Exterior Wall", "wall_type": "EXTERIOR",
        "cx": -target_building_width_m/2.0, "cy": floor_height_m/2.0, "cz": 0.0, "width": ext_th, "height": floor_height_m, "depth": bl_m,
        "color": "#1e293b", "edge_color": "#38bdf8"
    })
    walls_3d.append({
        "id": "ext_wall_east", "name": "East Exterior Wall", "wall_type": "EXTERIOR",
        "cx": target_building_width_m/2.0, "cy": floor_height_m/2.0, "cz": 0.0, "width": ext_th, "height": floor_height_m, "depth": bl_m,
        "color": "#1e293b", "edge_color": "#38bdf8"
    })
    
    # Add interior structural walls
    for c in wall_contours:
        area_px = cv2.contourArea(c)
        if area_px < 35:
            continue
        wx, wy, ww, wh = cv2.boundingRect(c)
        # Skip if it is the full outer border
        if ww > bw * 0.95 and wh > bh * 0.95:
            continue
        w_cx = round((wx + ww/2.0 - cx_px) * scale, 2)
        w_cz = round((wy + wh/2.0 - cy_px) * scale, 2)
        w_w = max(0.14, round(ww * scale, 2))
        w_d = max(0.14, round(wh * scale, 2))
        
        # Don't add walls right on the exterior boundary (already covered by exterior walls)
        if abs(w_cx) > (target_building_width_m / 2.0 - 0.4) and (w_w < 0.3 or w_d > target_building_width_m * 0.7):
            continue
        if abs(w_cz) > (bl_m / 2.0 - 0.4) and (w_d < 0.3 or w_w > bl_m * 0.7):
            continue
            
        walls_3d.append({
            "id": f"int_wall_{w_idx}",
            "name": f"Partition Wall {w_idx}",
            "wall_type": "INTERIOR",
            "cx": w_cx, "cy": floor_height_m/2.0, "cz": w_cz,
            "width": w_w, "height": floor_height_m, "depth": w_d,
            "color": "#1e293b", "edge_color": "#38bdf8"
        })
        w_idx += 1
        
    # Extract Rooms: Close small wall gaps and door cuts
    door_gap = max(12, int(min(bw, bh) * 0.045))
    gap_k = cv2.getStructuringElement(cv2.MORPH_RECT, (door_gap, door_gap))
    closed = cv2.morphologyEx(walls_mask, cv2.MORPH_CLOSE, gap_k)
    
    # Free space inside building
    inside_mask = np.zeros((h_px, w_px), dtype=np.uint8)
    inside_mask[by+6:by+bh-6, bx+6:bx+bw-6] = 255
    rooms_img = cv2.bitwise_and(cv2.bitwise_not(closed), inside_mask)
    
    room_contours, _ = cv2.findContours(rooms_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    min_area = (bw * bh) * 0.015
    raw_rooms = []
    for c in room_contours:
        area_px = cv2.contourArea(c)
        if area_px < min_area:
            continue
        rx, ry, rw, rh = cv2.boundingRect(c)
        # Exclude outer edge overflow
        if rw > bw * 0.95 or rh > bh * 0.95:
            continue
        raw_rooms.append({
            "rx": rx, "ry": ry, "rw": rw, "rh": rh, "area_px": area_px
        })
        
    # If no separate rooms detected due to wide open floorplan, segment by major partition spines
    if len(raw_rooms) <= 1:
        # Distance transform to find local room centers
        dist = cv2.distanceTransform(inside_mask, cv2.DIST_L2, 5)
        # Divide into quadrants or detect regions
        pass
        
    # Sort rooms by area descending
    raw_rooms.sort(key=lambda r: r["area_px"], reverse=True)
    
    # Classify rooms dynamically
    classified_rooms = []
    room_types_pool = [
        ("Living Room / Great Room", "LIV", "V", "PRV", "#1e3a5f", "#00f0ff"),
        ("Master Bedroom", "BED1", "V", "PRV", "#1e3a8a", "#fbbf24"),
        ("Kitchen & Dining", "KIT", "V", "PRV", "#155e75", "#22d3ee"),
        ("Bedroom 2", "BED2", "V", "PRV", "#1e3a8a", "#fbbf24"),
        ("Office / Study", "OFF", "V", "PRV", "#3730a3", "#a78bfa"),
        ("Central Corridor / Stairs", "STAIR", "V", "COM", "#4a1c24", "#ffd166"),
        ("Bathroom & Shower", "BATH", "V", "PRV", "#0f766e", "#2dd4bf"),
        ("Laundry & Utility", "LAU", "U", "PRV", "#3730a3", "#a78bfa"),
        ("Powder Room (WC)", "WC", "V", "PRV", "#14532d", "#34d399"),
        ("Pantry / Storage", "PAN", "U", "PRV", "#1e293b", "#a78bfa"),
        ("Covered Porch / Balcony", "BAL", "S", "COM", "#064e3b", "#10b981"),
    ]
    
    for idx, r in enumerate(raw_rooms):
        name_t, tag_t, s_class, rights, col, edge_col = room_types_pool[idx % len(room_types_pool)]
        if idx >= len(room_types_pool):
            name_t = f"Room {idx+1}"
            tag_t = f"R{idx+1:02d}"
            
        r_cx = round((r["rx"] + r["rw"]/2.0 - cx_px) * scale, 2)
        r_cz = round((r["ry"] + r["rh"]/2.0 - cy_px) * scale, 2)
        r_w = max(0.6, round(r["rw"] * scale, 2))
        r_l = max(0.6, round(r["rh"] * scale, 2))
        sqm = round(r_w * r_l, 2)
        
        classified_rooms.append({
            "room_index": idx + 1,
            "id": f"room_{idx+1}",
            "name": name_t,
            "type": "ROOM",
            "unit_tag": f"A101_{tag_t}",
            "space_class": s_class,
            "rights": rights,
            "owner": "Owner A (Suresh Gowda)" if rights == "PRV" else "Community",
            "dimensions_m": {"width": r_w, "length": r_l},
            "area_sqm": sqm,
            "area_sqft": round(sqm * 10.7639, 1),
            "center_m": {"x": r_cx, "y": r_cz},
            "bbox_m": {
                "x_min": round(r_cx - r_w/2.0, 2), "x_max": round(r_cx + r_w/2.0, 2),
                "y_min": round(r_cz - r_l/2.0, 2), "y_max": round(r_cz + r_l/2.0, 2)
            },
            "color": col,
            "edge_color": edge_col
        })
        
    print(f"[{image_path}] Extracted {len(walls_3d)} 3D walls and {len(classified_rooms)} architectural rooms:")
    for cr in classified_rooms:
        print(f"  - {cr['name']} ({cr['unit_tag']}): {cr['area_sqm']} m² at ({cr['center_m']['x']}, {cr['center_m']['y']})")
        
    return {
        "format": "RASTER_CV",
        "blueprint_type": "UNIVERSAL_CV_EXTRUSION",
        "building_dimensions_m": {"width": target_building_width_m, "length": bl_m, "height": floor_height_m * floors_count},
        "floors_count": floors_count,
        "floor_height_m": floor_height_m,
        "rooms_detected": len(classified_rooms),
        "rooms": classified_rooms,
        "walls": walls_3d,
        "units_summary": [
            {
                "unit_id": "APT_01",
                "name": "Custom Blueprint Extrusion",
                "total_carpet_sqm": round(sum(r["area_sqm"] for r in classified_rooms if r["rights"] == "PRV"), 2),
                "rooms_count": len([r for r in classified_rooms if r["rights"] == "PRV"]),
                "side": "FULL_DWELLING"
            }
        ]
    }

if __name__ == "__main__":
    for img_p in [
        "uploads/Screenshot 2026-09-08 074503.png",
        "uploads/Screenshot 2026-09-08 074533.png",
        "sample_blueprints/sample_floor_2unit.jpg",
        "sample_blueprints/user_test_blueprint.png"
    ]:
        extract_blueprint_cv(img_p)
