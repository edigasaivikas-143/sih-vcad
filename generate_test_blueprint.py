"""
Generate a high-precision, CAD-standard architectural test floor plan.
Designed for 100% part-to-part verification of the V-CAD 3D Extrusion Engine.
"""
import cv2
import numpy as np
from pathlib import Path

def create_cad_blueprint(output_path: str):
    # High-resolution canvas: 2200 x 1600 (crisp white background with black/navy CAD lines)
    width, height = 2200, 1600
    canvas = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Outer margins
    ox, oy = 250, 200
    scale = 100 # 1 meter = 100 pixels
    
    # Grid background (subtle architectural drafting grid)
    for gx in range(50, width - 50, 50):
        cv2.line(canvas, (gx, 50), (gx, height - 50), (242, 245, 248), 1)
    for gy in range(50, height - 50, 50):
        cv2.line(canvas, (50, gy), (width - 50, gy), (242, 245, 248), 1)

    # Building Outer Bounds: 16m wide x 11m deep
    bw_px = 16 * scale  # 1600 px
    bl_px = 11 * scale  # 1100 px
    
    # Outer Border Frame
    cv2.rectangle(canvas, (ox - 40, oy - 40), (ox + bw_px + 40, oy + bl_px + 40), (30, 41, 59), 3)
    
    # Room Layout Definitions (x, y, w, h in meters, label, color_tint)
    rooms = [
        (0.0,  0.0,  5.5,  6.0, "LIVING & DINING ROOM", "A301_LIV", "12345678901234-F03-V-PRV-A301_LIV-V01", "5.5m x 6.0m (33.0 sqm)"),
        (5.5,  0.0,  4.5,  3.5, "KITCHEN & PANTRY",     "A301_KIT", "12345678901234-F03-V-PRV-A301_KIT-V01", "4.5m x 3.5m (15.7 sqm)"),
        (5.5,  3.5,  4.5,  2.5, "COMMON RESTROOM",      "TOILET03", "12345678901234-F03-V-COM-TOILET03-V01", "4.5m x 2.5m (11.2 sqm)"),
        (10.0, 0.0,  6.0,  6.0, "MASTER BEDROOM 1",     "A301_BED1","12345678901234-F03-V-PRV-A301_BED1-V01","6.0m x 6.0m (36.0 sqm)"),
        (0.0,  6.0,  5.5,  5.0, "BEDROOM 2 (GUEST)",    "A301_BED2","12345678901234-F03-V-PRV-A301_BED2-V01","5.5m x 5.0m (27.5 sqm)"),
        (5.5,  6.0,  4.5,  5.0, "COMMON CORRIDOR & STAIRS", "STAIR03", "12345678901234-F03-V-COM-STAIR03-V01", "4.5m x 5.0m (22.5 sqm)"),
        (10.0, 6.0,  3.5,  5.0, "ATTACHED BATHROOM",    "A301_BATH","12345678901234-F03-V-PRV-A301_BATH-V01","3.5m x 5.0m (17.5 sqm)"),
        (13.5, 6.0,  2.5,  5.0, "PRIVATE BALCONY",      "A301_BALC","12345678901234-F03-V-PRV-A301_BALC-V01","2.5m x 5.0m (12.5 sqm)"),
    ]
    
    # Draw Room Walls (Thick double-line walls with fill)
    wall_t = 16 # 16px ~ 16cm
    
    # Fill room background tints
    for r in rooms:
        rx = int(ox + r[0] * scale)
        ry = int(oy + r[1] * scale)
        rw = int(r[2] * scale)
        rh = int(r[3] * scale)
        cv2.rectangle(canvas, (rx, ry), (rx + rw, ry + rh), (250, 252, 255), -1)

    # Draw solid black load-bearing structural walls
    for r in rooms:
        rx = int(ox + r[0] * scale)
        ry = int(oy + r[1] * scale)
        rw = int(r[2] * scale)
        rh = int(r[3] * scale)
        cv2.rectangle(canvas, (rx, ry), (rx + rw, ry + rh), (15, 23, 42), wall_t)

    # Cut door openings (simulating architectural door swings)
    doors = [
        (ox + int(2.75 * scale), oy + int(6.0 * scale), 80, 'H'),
        (ox + int(5.5 * scale), oy + int(2.0 * scale), 80, 'V'),
        (ox + int(10.0 * scale), oy + int(3.0 * scale), 80, 'V'),
        (ox + int(5.5 * scale), oy + int(7.5 * scale), 80, 'V'),
        (ox + int(10.0 * scale), oy + int(8.0 * scale), 80, 'V'),
        (ox + int(13.5 * scale), oy + int(8.5 * scale), 80, 'V'),
    ]
    for dx, dy, dw, orient in doors:
        if orient == 'H':
            cv2.rectangle(canvas, (dx - dw//2, dy - wall_t//2 - 2), (dx + dw//2, dy + wall_t//2 + 2), (255, 255, 255), -1)
            cv2.ellipse(canvas, (dx - dw//2, dy), (dw, dw), 0, 0, 90, (148, 163, 184), 2)
        else:
            cv2.rectangle(canvas, (dx - wall_t//2 - 2, dy - dw//2), (dx + wall_t//2 + 2, dy + dw//2), (255, 255, 255), -1)
            cv2.ellipse(canvas, (dx, dy - dw//2), (dw, dw), 0, 0, 90, (148, 163, 184), 2)

    # Draw Text Labels & Dimensions inside each room
    for r in rooms:
        rx = int(ox + r[0] * scale)
        ry = int(oy + r[1] * scale)
        rw = int(r[2] * scale)
        rh = int(r[3] * scale)
        cx = rx + rw // 2
        cy = ry + rh // 2
        
        name = r[4]
        code = r[5]
        ulpin = r[6]
        dims = r[7]
        
        # Name
        cv2.putText(canvas, name, (cx - len(name)*6, cy - 35), cv2.FONT_HERSHEY_DUPLEX, 0.55, (15, 23, 42), 2, cv2.LINE_AA)
        # Tag Badge
        cv2.putText(canvas, f"TAG: {code}", (cx - len(code)*5 - 25, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (2, 132, 199), 1, cv2.LINE_AA)
        # Dimensions
        cv2.putText(canvas, dims, (cx - len(dims)*4 - 15, cy + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 116, 139), 1, cv2.LINE_AA)
        # 3D ULPIN
        cv2.putText(canvas, ulpin, (cx - len(ulpin)*4 - 10, cy + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (217, 119, 6), 1, cv2.LINE_AA)

    # Outer Dimension Witness Lines
    dim_y = oy - 60
    cv2.line(canvas, (ox, dim_y), (ox + bw_px, dim_y), (100, 116, 139), 2)
    cv2.line(canvas, (ox, dim_y - 15), (ox, dim_y + 15), (100, 116, 139), 2)
    cv2.line(canvas, (ox + bw_px, dim_y - 15), (ox + bw_px, dim_y + 15), (100, 116, 139), 2)
    cv2.putText(canvas, "<-------- 16.00 METERS TOTAL BUILDING WIDTH -------->", (ox + bw_px//2 - 280, dim_y - 12), cv2.FONT_HERSHEY_DUPLEX, 0.55, (30, 41, 59), 2, cv2.LINE_AA)

    dim_x = ox - 60
    cv2.line(canvas, (dim_x, oy), (dim_x, oy + bl_px), (100, 116, 139), 2)
    cv2.line(canvas, (dim_x - 15, oy), (dim_x + 15, oy), (100, 116, 139), 2)
    cv2.line(canvas, (dim_x - 15, oy + bl_px), (dim_x + 15, oy + bl_px), (100, 116, 139), 2)
    cv2.putText(canvas, "11.00 METERS LENGTH", (dim_x - 130, oy + bl_px//2), cv2.FONT_HERSHEY_DUPLEX, 0.50, (30, 41, 59), 2, cv2.LINE_AA)

    # Architectural Title Block
    tb_x, tb_y = ox + bw_px - 580, oy + bl_px + 80
    tb_w, tb_h = 580, 160
    cv2.rectangle(canvas, (tb_x, tb_y), (tb_x + tb_w, tb_y + tb_h), (30, 41, 59), 2)
    cv2.rectangle(canvas, (tb_x, tb_y), (tb_x + tb_w, tb_y + 40), (15, 23, 42), -1)
    cv2.putText(canvas, "GOVERNMENT OF INDIA - SVAMITVA 3D CADASTRE", (tb_x + 20, tb_y + 26), cv2.FONT_HERSHEY_DUPLEX, 0.50, (255, 255, 255), 1, cv2.LINE_AA)
    
    cv2.putText(canvas, "PROJECT: 2BHK RESIDENTIAL APARTMENT (FLAT A301)", (tb_x + 15, tb_y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (30, 41, 59), 1, cv2.LINE_AA)
    cv2.putText(canvas, "PARENT 2D LAND PARCEL ULPIN: 12345678901234", (tb_x + 15, tb_y + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (2, 132, 199), 2, cv2.LINE_AA)
    cv2.putText(canvas, "VERTICAL LEVEL: FLOOR 3 (F03) | CLEAR HEIGHT: 3.00m", (tb_x + 15, tb_y + 115), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (71, 85, 105), 1, cv2.LINE_AA)
    cv2.putText(canvas, "STANDARD: DILRMP / SVAMITVA / LADM ISO 19152", (tb_x + 15, tb_y + 140), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (217, 119, 6), 1, cv2.LINE_AA)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, canvas)
    print(f"[OK] High-Precision Architectural Test Blueprint generated at: {output_path}")

if __name__ == "__main__":
    create_cad_blueprint("sample_blueprints/official_test_blueprint.png")
    create_cad_blueprint("storage/blueprints/official_test_blueprint.png")
    create_cad_blueprint("uploads/official_test_blueprint.png")
