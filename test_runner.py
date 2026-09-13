import cv2
import numpy as np
from pathlib import Path

def extract_universal_blueprint_cv(
    image_path: str,
    target_building_width_m: float = 12.0,
    floor_height_m: float = 2.80,
    floors_count: int = 1
):
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    h_px, w_px = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if np.mean(gray) < 127:
        gray = 255 - gray
        
    margin_y = max(6, int(h_px * 0.035))
    margin_x = max(6, int(w_px * 0.035))
    gray[:margin_y, :] = 255
    gray[-margin_y:, :] = 255
    gray[:, :margin_x] = 255
    gray[:, -margin_x:] = 255
    
    _, bin_w = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(bin_w)
    wall_mask = np.zeros_like(bin_w)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_WIDTH] >= 25 or stats[i, cv2.CC_STAT_HEIGHT] >= 25 or stats[i, cv2.CC_STAT_AREA] >= 120:
            wall_mask[labels == i] = 255
            
    pts = cv2.findNonZero(wall_mask)
    if pts is None:
        pts = cv2.findNonZero(bin_w)
    bx, by, bw, bh = cv2.boundingRect(pts)
    
    scale = target_building_width_m / max(10, bw)
    bl_m = round(bh * scale, 2)
    cx_px = bx + bw / 2.0
    cy_px = by + bh / 2.0
    
    # Doorway closing kernel
    door_k = max(9, int(min(bw, bh) * 0.042))
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (door_k, door_k))
    closed = cv2.morphologyEx(wall_mask, cv2.MORPH_CLOSE, k)
    cv2.rectangle(closed, (bx, by), (bx+bw, by+bh), 255, 4)
    
    env = np.zeros_like(bin_w)
    env[by+3:by+bh-3, bx+3:bx+bw-3] = 255
    rooms_mask = cv2.bitwise_and(cv2.bitwise_not(closed), env)
    
    cnts, _ = cv2.findContours(rooms_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = (bw * bh) * 0.012
    raw_rooms = []
    for c in cnts:
        a = cv2.contourArea(c)
        if a >= min_area:
            rx, ry, rw, rh = cv2.boundingRect(c)
            if rw < bw * 0.95 and rh < bh * 0.95:
                raw_rooms.append({'rx': rx, 'ry': ry, 'rw': rw, 'rh': rh, 'area_px': a})
                
    raw_rooms.sort(key=lambda r: r['area_px'], reverse=True)
    
    # Semantic naming pool
    room_types_pool = [
        ('Living Room / Great Room', 'LIV', 'V', 'PRV', '#1e3a5f', '#00f0ff'),
        ('Master Bedroom', 'BED1', 'V', 'PRV', '#1e3a8a', '#fbbf24'),
        ('Kitchen & Dining', 'KIT', 'V', 'PRV', '#155e75', '#22d3ee'),
        ('Bedroom 2', 'BED2', 'V', 'PRV', '#1e3a8a', '#fbbf24'),
        ('Office / Study', 'OFF', 'V', 'PRV', '#3730a3', '#a78bfa'),
        ('Central Corridor / Stairs', 'STAIR', 'V', 'COM', '#4a1c24', '#ffd166'),
        ('Bathroom & Shower', 'BATH', 'V', 'PRV', '#0f766e', '#2dd4bf'),
        ('Laundry & Utility', 'LAU', 'U', 'PRV', '#3730a3', '#a78bfa'),
        ('Powder Room (WC)', 'WC', 'V', 'PRV', '#14532d', '#34d399'),
        ('Pantry / Storage', 'PAN', 'U', 'PRV', '#1e293b', '#a78bfa'),
        ('Covered Porch / Balcony', 'BAL', 'S', 'COM', '#064e3b', '#10b981'),
    ]
    
    rooms_3d = []
    for idx, r in enumerate(raw_rooms):
        name_t, tag_t, s_class, rights, col, edge_col = room_types_pool[idx % len(room_types_pool)]
        if idx >= len(room_types_pool):
            name_t = f'Room {idx+1}'
            tag_t = f'R{idx+1:02d}'
            
        r_cx = round((r['rx'] + r['rw']/2.0 - cx_px) * scale, 2)
        r_cz = round((r['ry'] + r['rh']/2.0 - cy_px) * scale, 2)
        r_w = max(0.6, round(r['rw'] * scale, 2))
        r_l = max(0.6, round(r['rh'] * scale, 2))
        sqm = round(r_w * r_l, 2)
        
        rooms_3d.append({
            'room_index': idx + 1,
            'id': f'room_{idx+1}',
            'name': name_t,
            'type': 'ROOM',
            'unit_tag': f'A101_{tag_t}',
            'space_class': s_class,
            'rights': rights,
            'owner': 'Owner A (Suresh Gowda)' if rights == 'PRV' else 'Community',
            'dimensions_m': {'width': r_w, 'length': r_l},
            'area_sqm': sqm,
            'area_sqft': round(sqm * 10.7639, 1),
            'center_m': {'x': r_cx, 'y': r_cz},
            'bbox_m': {
                'x_min': round(r_cx - r_w/2.0, 2), 'x_max': round(r_cx + r_w/2.0, 2),
                'y_min': round(r_cz - r_l/2.0, 2), 'y_max': round(r_cz + r_l/2.0, 2)
            },
            'color': col,
            'edge_color': edge_col
        })
        
    # Extract interior walls from line contours
    kh = cv2.getStructuringElement(cv2.MORPH_RECT, (max(12, int(bw*0.04)), 2))
    kv = cv2.getStructuringElement(cv2.MORPH_RECT, (2, max(12, int(bh*0.04))))
    h_w = cv2.morphologyEx(wall_mask, cv2.MORPH_OPEN, kh)
    v_w = cv2.morphologyEx(wall_mask, cv2.MORPH_OPEN, kv)
    comb = cv2.bitwise_or(h_w, v_w)
    
    cnts_w, _ = cv2.findContours(comb, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    walls_3d = []
    
    # 4 Exterior Envelope Walls
    ext_th = 0.22
    walls_3d.append({'id': 'ext_n', 'name': 'North Exterior Wall', 'wall_type': 'EXTERIOR', 'cx': 0.0, 'cy': floor_height_m/2.0, 'cz': -bl_m/2.0, 'width': target_building_width_m, 'height': floor_height_m, 'depth': ext_th, 'color': '#1e293b', 'edge_color': '#38bdf8'})
    walls_3d.append({'id': 'ext_s', 'name': 'South Exterior Wall', 'wall_type': 'EXTERIOR', 'cx': 0.0, 'cy': floor_height_m/2.0, 'cz': bl_m/2.0, 'width': target_building_width_m, 'height': floor_height_m, 'depth': ext_th, 'color': '#1e293b', 'edge_color': '#38bdf8'})
    walls_3d.append({'id': 'ext_w', 'name': 'West Exterior Wall', 'wall_type': 'EXTERIOR', 'cx': -target_building_width_m/2.0, 'cy': floor_height_m/2.0, 'cz': 0.0, 'width': ext_th, 'height': floor_height_m, 'depth': bl_m, 'color': '#1e293b', 'edge_color': '#38bdf8'})
    walls_3d.append({'id': 'ext_e', 'name': 'East Exterior Wall', 'wall_type': 'EXTERIOR', 'cx': target_building_width_m/2.0, 'cy': floor_height_m/2.0, 'cz': 0.0, 'width': ext_th, 'height': floor_height_m, 'depth': bl_m, 'color': '#1e293b', 'edge_color': '#38bdf8'})
    
    w_idx = 1
    for cw in cnts_w:
        area_px = cv2.contourArea(cw)
        if area_px < 25: continue
        wx, wy, ww, wh = cv2.boundingRect(cw)
        if ww > bw * 0.92 and wh > bh * 0.92: continue
        wcx = round((wx + ww/2.0 - cx_px) * scale, 2)
        wcz = round((wy + wh/2.0 - cy_px) * scale, 2)
        ww_m = max(0.14, round(ww * scale, 2))
        wd_m = max(0.14, round(wh * scale, 2))
        
        # Don't duplicate outer perimeter
        if abs(wcx) > (target_building_width_m / 2.0 - 0.3) and (ww_m < 0.3 or wd_m > target_building_width_m * 0.6): continue
        if abs(wcz) > (bl_m / 2.0 - 0.3) and (wd_m < 0.3 or ww_m > bl_m * 0.6): continue
        
        walls_3d.append({
            'id': f'int_wall_{w_idx}',
            'name': f'Partition Wall {w_idx}',
            'wall_type': 'INTERIOR',
            'cx': wcx, 'cy': floor_height_m/2.0, 'cz': wcz,
            'width': ww_m, 'height': floor_height_m, 'depth': wd_m,
            'color': '#1e293b', 'edge_color': '#38bdf8'
        })
        w_idx += 1
        
    return {
        'format': 'RASTER_CV',
        'blueprint_type': 'UNIVERSAL_CV_EXTRUSION',
        'building_dimensions_m': {'width': target_building_width_m, 'length': bl_m, 'height': floor_height_m * floors_count},
        'floors_count': floors_count,
        'floor_height_m': floor_height_m,
        'rooms_detected': len(rooms_3d),
        'rooms': rooms_3d,
        'walls': walls_3d,
        'units_summary': [
            {
                'unit_id': 'APT_01',
                'name': 'Extruded Cadastre Unit',
                'total_carpet_sqm': round(sum(r['area_sqm'] for r in rooms_3d if r['rights'] == 'PRV'), 2),
                'rooms_count': len([r for r in rooms_3d if r['rights'] == 'PRV']),
                'side': 'FULL_DWELLING'
            }
        ]
    }

if __name__ == "__main__":
    test_files = [
        "uploads/Screenshot 2026-09-08 074503.png",
        "uploads/Screenshot 2026-09-08 074533.png",
        "sample_blueprints/sample_floor_2unit.jpg",
        "sample_blueprints/user_test_blueprint.png"
    ]
    for p in test_files:
        res = extract_universal_blueprint_cv(p)
        print(f"File: {p}")
        print(f"  Rooms detected: {res['rooms_detected']}")
        print(f"  Walls detected: {len(res['walls'])}")
        print(f"  Dimensions: {res['building_dimensions_m']['width']}m x {res['building_dimensions_m']['length']}m x {res['building_dimensions_m']['height']}m")
        for r in res['rooms'][:4]:
            print(f"    - {r['name']}: {r['area_sqm']} m2 at ({r['center_m']['x']}, {r['center_m']['y']})")
        print("-" * 50)
