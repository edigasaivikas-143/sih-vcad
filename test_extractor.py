import cv2
import numpy as np

def extract_blueprint_geometry(img_path, target_width_m=12.0, floor_h=2.8):
    img = cv2.imread(img_path)
    if img is None:
        print("Image not found:", img_path)
        return
    h_px, w_px = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Invert if dark background
    if np.mean(gray) < 127:
        gray = 255 - gray
        
    # Otsu threshold
    _, bin_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Horizontal and vertical structural wall lines
    h_len = max(8, int(w_px * 0.035))
    v_len = max(8, int(h_px * 0.035))
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_len, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_len))
    
    h_lines = cv2.morphologyEx(bin_inv, cv2.MORPH_OPEN, h_kernel)
    v_lines = cv2.morphologyEx(bin_inv, cv2.MORPH_OPEN, v_kernel)
    walls_mask = cv2.bitwise_or(h_lines, v_lines)
    
    # Building envelope
    pts = cv2.findNonZero(walls_mask)
    if pts is None:
        pts = cv2.findNonZero(bin_inv)
    bx, by, bw, bh = cv2.boundingRect(pts)
    
    scale = target_width_m / max(10, bw)
    bl_m = round(bh * scale, 2)
    cx_px = bx + bw / 2.0
    cy_px = by + bh / 2.0
    
    # Extract wall rectangles
    wall_contours, _ = cv2.findContours(walls_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    walls_3d = []
    w_idx = 1
    for c in wall_contours:
        if cv2.contourArea(c) < 25:
            continue
        wx, wy, ww, wh = cv2.boundingRect(c)
        cx_m = round((wx + ww / 2.0 - cx_px) * scale, 2)
        cz_m = round((wy + wh / 2.0 - cy_px) * scale, 2)
        w_m = max(0.18, round(ww * scale, 2))
        d_m = max(0.18, round(wh * scale, 2))
        walls_3d.append({
            'id': f'cv_wall_{w_idx}',
            'cx': cx_m, 'cz': cz_m, 'width': w_m, 'depth': d_m, 'height': floor_h
        })
        w_idx += 1
        
    # Extract rooms: close doors
    close_k = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    closed_walls = cv2.morphologyEx(walls_mask, cv2.MORPH_CLOSE, close_k)
    
    # Crop inside building bounding box
    inner_envelope = np.zeros_like(closed_walls)
    inner_envelope[by+4:by+bh-4, bx+4:bx+bw-4] = 255
    rooms_binary = cv2.bitwise_and(cv2.bitwise_not(closed_walls), inner_envelope)
    
    room_contours, _ = cv2.findContours(rooms_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rooms_3d = []
    min_room_area = (bw * bh) * 0.015
    r_idx = 1
    for c in room_contours:
        area_px = cv2.contourArea(c)
        if area_px < min_room_area:
            continue
        rx, ry, rw, rh = cv2.boundingRect(c)
        cx_m = round((rx + rw / 2.0 - cx_px) * scale, 2)
        cz_m = round((ry + rh / 2.0 - cy_px) * scale, 2)
        rw_m = round(rw * scale, 2)
        rl_m = round(rh * scale, 2)
        sqm = round(rw_m * rl_m, 2)
        rooms_3d.append({
            'id': f'cv_room_{r_idx}',
            'name': f'Room {r_idx}',
            'area_sqm': sqm,
            'cx': cx_m, 'cz': cz_m, 'width': rw_m, 'length': rl_m
        })
        r_idx += 1
        
    print(f"Done {img_path}: Envelope={target_width_m}mx{bl_m}m | Walls={len(walls_3d)} | Rooms={len(rooms_3d)}")
    for r in rooms_3d[:6]:
        print(f"  {r['name']}: {r['area_sqm']} m² at ({r['cx']}, {r['cz']})")

if __name__ == "__main__":
    extract_blueprint_geometry("uploads/Screenshot 2026-09-08 074503.png")
    extract_blueprint_geometry("uploads/Screenshot 2026-09-08 074533.png")
    extract_blueprint_geometry("sample_blueprints/sample_floor_2unit.jpg")
    extract_blueprint_geometry("sample_blueprints/user_test_blueprint.png")
