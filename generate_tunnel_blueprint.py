"""
High-Resolution CAD Blueprint Generator for Tunnel Infrastructure
Generates an engineering-grade architectural CAD blueprint for a Twin-Tube Highway Tunnel
with Northbound & Southbound tubes, emergency cross-passages, deep ventilation shaft, and portals.
Saves to sample_blueprints and storage/blueprints.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_tunnel_cad_blueprint(output_path: str = "sample_blueprints/tunnel_infrastructure_blueprint.png"):
    w, h = 1800, 1200
    # CAD Blueprint dark blueprint blue background
    bg_color = (11, 25, 44)       # #0b192c
    grid_fine = (18, 38, 64)      # #122640
    grid_coarse = (26, 54, 93)    # #1a365d
    cad_cyan = (56, 189, 248)     # #38bdf8
    cad_white = (241, 245, 249)   # #f1f5f9
    cad_amber = (251, 191, 36)    # #fbbf24
    cad_green = (74, 222, 128)    # #4ade80
    cad_purple = (167, 139, 250)  # #a78bfa
    cad_gray = (148, 163, 184)    # #94a3b8
    tube1_fill = (20, 35, 70)
    tube2_fill = (22, 40, 78)
    cross_fill = (15, 60, 40)
    vent_fill = (15, 50, 75)

    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Architectural CAD Grid
    grid_sz = 20
    for x in range(0, w, grid_sz):
        col = grid_coarse if x % 100 == 0 else grid_fine
        draw.line([(x, 0), (x, h)], fill=col, width=1)
    for y in range(0, h, grid_sz):
        col = grid_coarse if y % 100 == 0 else grid_fine
        draw.line([(0, y), (w, y)], fill=col, width=1)

    # 2. Outer Technical CAD Border & Margins
    margin = 40
    draw.rectangle([(margin, margin), (w - margin, h - margin)], outline=cad_cyan, width=3)
    draw.rectangle([(margin + 6, margin + 6), (w - margin - 6, h - margin - 6)], outline=grid_coarse, width=1)

    # Font handling - default bitmap or available truetype
    try:
        font_lg = ImageFont.truetype("arial.ttf", 22)
        font_md = ImageFont.truetype("arial.ttf", 15)
        font_sm = ImageFont.truetype("arial.ttf", 12)
        font_title = ImageFont.truetype("arialbd.ttf", 26)
        font_sub = ImageFont.truetype("arialbd.ttf", 16)
    except Exception:
        font_lg = ImageFont.load_default()
        font_md = font_lg
        font_sm = font_lg
        font_title = font_lg
        font_sub = font_lg

    # 3. Header Title Block
    header_h = 100
    draw.rectangle([(margin, margin), (w - margin, margin + header_h)], fill=(15, 23, 42), outline=cad_cyan, width=2)
    draw.text((margin + 25, margin + 15), "NATIONAL HIGHWAYS AUTHORITY OF INDIA (NHAI) / SVAMITVA 3D CADASTRE", fill=cad_amber, font=font_sub)
    draw.text((margin + 25, margin + 40), "SUBTERRANEAN TWIN-TUBE HIGHWAY TUNNEL INFRASTRUCTURE", fill=cad_white, font=font_title)
    draw.text((margin + 25, margin + 75), "ENGINEERING PLAN & GEOMETRICAL SECTION • SPACE CLASS: U (SUBTERRANEAN DEPTH: -14.0m to -6.5m)", fill=cad_cyan, font=font_md)

    # Right side meta box
    meta_x = w - margin - 420
    draw.line([(meta_x, margin), (meta_x, margin + header_h)], fill=cad_cyan, width=2)
    draw.text((meta_x + 15, margin + 15), "PARENT 2D ULPIN: 28045678901240", fill=cad_green, font=font_sub)
    draw.text((meta_x + 15, margin + 40), "3D ULPIN: 28045678901240-B02-U-PUB-TNL_TUBE1-V01", fill=cad_white, font=font_sm)
    draw.text((meta_x + 15, margin + 60), "COORDINATE DATUM: WGS84 / EPSG:7760 (METRIC)", fill=cad_gray, font=font_sm)
    draw.text((meta_x + 15, margin + 80), "SCALE: 1:200 (100px = 10.0 METERS)", fill=cad_amber, font=font_sm)

    # 4. Main Plan View (Horizontal twin-tube tunnel corridor)
    # Tube dimensions: width = 110 px (11 meters), length = 1100 px (110 meters)
    corridor_x0 = 120
    corridor_x1 = 1220
    tube_w_px = 100
    t1_y0 = 230
    t1_y1 = t1_y0 + tube_w_px  # 330
    t2_y0 = 450
    t2_y1 = t2_y0 + tube_w_px  # 550

    # Section View dividing line
    divider_y = 650
    draw.line([(margin, divider_y), (w - margin, divider_y)], fill=cad_cyan, width=2)

    # --- PLAN VIEW DRAWING ---
    draw.text((corridor_x0, 155), "SECTION 1: PLAN VIEW (SUBTERRANEAN INVERT LEVEL Z = -14.0m)", fill=cad_white, font=font_sub)

    # 4a. North Portal (Left Entrance) & Headwall
    portal_w = 40
    p1_x0 = corridor_x0 - portal_w
    p1_x1 = corridor_x0
    draw.rectangle([(p1_x0, t1_y0 - 20), (p1_x1, t2_y1 + 20)], fill=(30, 41, 59), outline=cad_cyan, width=3)
    draw.text((p1_x0 - 20, t1_y0 - 55), "NORTH PORTAL", fill=cad_amber, font=font_md)
    draw.text((p1_x0 - 30, t1_y0 - 35), "CUT & COVER (Z: 0 to -14m)", fill=cad_gray, font=font_sm)

    # 4b. South Portal (Right Exit) & Headwall
    p2_x0 = corridor_x1
    p2_x1 = corridor_x1 + portal_w
    draw.rectangle([(p2_x0, t1_y0 - 20), (p2_x1, t2_y1 + 20)], fill=(30, 41, 59), outline=cad_cyan, width=3)
    draw.text((p2_x0 - 15, t1_y0 - 55), "SOUTH PORTAL", fill=cad_amber, font=font_md)
    draw.text((p2_x0 - 30, t1_y0 - 35), "CUT & COVER (Z: 0 to -14m)", fill=cad_gray, font=font_sm)

    # 4c. Tube 1: Northbound Subterranean Tube
    draw.rectangle([(corridor_x0, t1_y0), (corridor_x1, t1_y1)], fill=tube1_fill, outline=cad_white, width=4)
    # Interior carriageway lanes
    mid_t1 = (t1_y0 + t1_y1) // 2
    for lx in range(corridor_x0 + 10, corridor_x1 - 10, 30):
        draw.line([(lx, mid_t1), (lx + 15, mid_t1)], fill=cad_amber, width=2)
    # Direction arrows (-->)
    for ax in [corridor_x0 + 180, corridor_x0 + 550, corridor_x0 + 920]:
        draw.polygon([(ax, mid_t1 - 6), (ax + 20, mid_t1), (ax, mid_t1 + 6)], fill=cad_cyan)

    draw.text((corridor_x0 + 30, t1_y0 + 14), "TUBE 1: NORTHBOUND HIGHWAY (8.5m DIA / 2 LANES)", fill=cad_white, font=font_sub)
    draw.text((corridor_x0 + 30, t1_y0 + 68), "ULPIN: 28045678901240-B02-U-PUB-TNL_TUBE1-V01 • LEVEL: B02 (Z = -14.0m)", fill=cad_cyan, font=font_sm)

    # 4d. Tube 2: Southbound Subterranean Tube
    draw.rectangle([(corridor_x0, t2_y0), (corridor_x1, t2_y1)], fill=tube2_fill, outline=cad_white, width=4)
    # Interior carriageway lanes
    mid_t2 = (t2_y0 + t2_y1) // 2
    for lx in range(corridor_x0 + 10, corridor_x1 - 10, 30):
        draw.line([(lx, mid_t2), (lx + 15, mid_t2)], fill=cad_amber, width=2)
    # Direction arrows (<--)
    for ax in [corridor_x0 + 200, corridor_x0 + 570, corridor_x0 + 940]:
        draw.polygon([(ax, mid_t2 - 6), (ax - 20, mid_t2), (ax, mid_t2 + 6)], fill=cad_cyan)

    draw.text((corridor_x0 + 30, t2_y0 + 14), "TUBE 2: SOUTHBOUND HIGHWAY (8.5m DIA / 2 LANES)", fill=cad_white, font=font_sub)
    draw.text((corridor_x0 + 30, t2_y0 + 68), "ULPIN: 28045678901240-B02-U-PUB-TNL_TUBE2-V01 • LEVEL: B02 (Z = -14.0m)", fill=cad_cyan, font=font_sm)

    # 4e. Emergency Evacuation Cross-Passage 1 (CPASS01 at x = 380)
    cp1_x = corridor_x0 + 260
    cp_w = 40
    draw.rectangle([(cp1_x, t1_y1), (cp1_x + cp_w, t2_y0)], fill=cross_fill, outline=cad_green, width=3)
    draw.text((cp1_x - 30, (t1_y1 + t2_y0)//2 - 16), "CROSS-PASSAGE 1", fill=cad_green, font=font_sm)
    draw.text((cp1_x - 15, (t1_y1 + t2_y0)//2 + 2), "CPASS01 (U)", fill=cad_white, font=font_sm)

    # 4f. Emergency Evacuation Cross-Passage 2 (CPASS02 at x = 840)
    cp2_x = corridor_x0 + 740
    draw.rectangle([(cp2_x, t1_y1), (cp2_x + cp_w, t2_y0)], fill=cross_fill, outline=cad_green, width=3)
    draw.text((cp2_x - 30, (t1_y1 + t2_y0)//2 - 16), "CROSS-PASSAGE 2", fill=cad_green, font=font_sm)
    draw.text((cp2_x - 15, (t1_y1 + t2_y0)//2 + 2), "CPASS02 (U)", fill=cad_white, font=font_sm)

    # 4g. Central Deep Ventilation & Smoke Exhaust Shaft (VENT_SHAFT01 at x = 500)
    vent_x = corridor_x0 + 500
    vent_sz = 60
    vent_y = (t1_y1 + t2_y0)//2 - vent_sz//2
    draw.rectangle([(vent_x, vent_y), (vent_x + vent_sz, vent_y + vent_sz)], fill=vent_fill, outline=cad_purple, width=3)
    # Duct diagonals
    draw.line([(vent_x, vent_y), (vent_x + vent_sz, vent_y + vent_sz)], fill=cad_purple, width=2)
    draw.line([(vent_x, vent_y + vent_sz), (vent_x + vent_sz, vent_y)], fill=cad_purple, width=2)
    draw.text((vent_x - 45, vent_y - 25), "VENT SHAFT 01 (UTL)", fill=cad_purple, font=font_sub)
    draw.text((vent_x - 35, vent_y + vent_sz + 8), "Z: -14.0m -> +3.5m", fill=cad_cyan, font=font_sm)

    # Plan View Dimension Lines
    # Horizontal dimension
    dim_y = t2_y1 + 45
    draw.line([(corridor_x0, dim_y), (corridor_x1, dim_y)], fill=cad_cyan, width=1)
    draw.line([(corridor_x0, dim_y - 8), (corridor_x0, dim_y + 8)], fill=cad_cyan, width=2)
    draw.line([(corridor_x1, dim_y - 8), (corridor_x1, dim_y + 8)], fill=cad_cyan, width=2)
    draw.text(((corridor_x0 + corridor_x1)//2 - 60, dim_y - 20), "<--- TOTAL LENGTH: 110.0 METERS --->", fill=cad_cyan, font=font_sm)

    # Vertical dimension
    dim_x = corridor_x0 - 55
    draw.line([(dim_x, t1_y0), (dim_x, t2_y1)], fill=cad_cyan, width=1)
    draw.line([(dim_x - 8, t1_y0), (dim_x + 8, t1_y0)], fill=cad_cyan, width=2)
    draw.line([(dim_x - 8, t2_y1), (dim_x + 8, t2_y1)], fill=cad_cyan, width=2)
    draw.text((dim_x - 65, (t1_y0 + t2_y1)//2 - 8), "26.0m", fill=cad_cyan, font=font_sm)

    # --- SECTION VIEW A-A' (Bottom Half) ---
    sec_x0 = 120
    sec_y_ground = 740   # Ground line Z = 0.0m
    sec_y_crown = 880    # Crown arch Z = -6.5m (14px per meter)
    sec_y_invert = 990   # Invert slab Z = -14.0m

    draw.text((sec_x0, divider_y + 15), "SECTION 2: TRANSVERSE GEOMETRICAL ELEVATION & DEPTH CROSS-SECTION (A-A')", fill=cad_white, font=font_sub)

    # Ground Level Line (Z = 0.00m)
    draw.line([(sec_x0, sec_y_ground), (w - margin - 50, sec_y_ground)], fill=cad_green, width=3)
    draw.text((sec_x0, sec_y_ground - 22), "TERRAIN SURFACE LEVEL (Z = 0.00m) • GROUND RIGHT-OF-WAY (SPACE CLASS: S)", fill=cad_green, font=font_sm)

    # Overburden Hatching / Soil Zone
    for hx in range(sec_x0 + 20, w - margin - 60, 50):
        draw.line([(hx, sec_y_ground + 5), (hx + 25, sec_y_ground + 35)], fill=(40, 60, 80), width=1)
    draw.text((w - margin - 350, sec_y_ground + 20), "OVERBURDEN ROCK / SOIL STRATA (6.5m THICK)", fill=cad_gray, font=font_sm)

    # Elevation depth ticks on left side
    draw.line([(sec_x0 + 50, sec_y_ground), (sec_x0 + 50, sec_y_invert + 40)], fill=cad_amber, width=2)
    draw.line([(sec_x0 + 40, sec_y_ground), (sec_x0 + 60, sec_y_ground)], fill=cad_amber, width=2)
    draw.text((sec_x0 - 30, sec_y_ground - 6), "+0.00m", fill=cad_green, font=font_sm)

    draw.line([(sec_x0 + 40, sec_y_crown), (sec_x0 + 60, sec_y_crown)], fill=cad_amber, width=2)
    draw.text((sec_x0 - 30, sec_y_crown - 6), "-6.50m (Crown)", fill=cad_cyan, font=font_sm)

    draw.line([(sec_x0 + 40, sec_y_invert), (sec_x0 + 60, sec_y_invert)], fill=cad_amber, width=2)
    draw.text((sec_x0 - 30, sec_y_invert - 6), "-14.00m (Invert)", fill=cad_amber, font=font_sm)

    # Cross-Section Tunnel Vault 1 (Northbound horseshoe arch)
    v1_cx = 400
    v1_r = 60
    draw.arc([(v1_cx - v1_r, sec_y_crown), (v1_cx + v1_r, sec_y_crown + 2 * v1_r)], start=180, end=0, fill=cad_cyan, width=4)
    draw.line([(v1_cx - v1_r, sec_y_crown + v1_r), (v1_cx - v1_r, sec_y_invert)], fill=cad_cyan, width=4)
    draw.line([(v1_cx + v1_r, sec_y_crown + v1_r), (v1_cx + v1_r, sec_y_invert)], fill=cad_cyan, width=4)
    draw.line([(v1_cx - v1_r, sec_y_invert), (v1_cx + v1_r, sec_y_invert)], fill=cad_white, width=4)
    # Carriageway invert slab
    draw.rectangle([(v1_cx - v1_r + 4, sec_y_invert - 12), (v1_cx + v1_r - 4, sec_y_invert)], fill=(30, 41, 59), outline=cad_amber, width=2)
    draw.text((v1_cx - 40, sec_y_invert - 50), "TUBE 1 (NB)", fill=cad_white, font=font_sub)
    draw.text((v1_cx - 50, sec_y_invert - 30), "SPACE CLASS: U", fill=cad_cyan, font=font_sm)

    # Cross-Section Tunnel Vault 2 (Southbound horseshoe arch)
    v2_cx = 750
    draw.arc([(v2_cx - v1_r, sec_y_crown), (v2_cx + v1_r, sec_y_crown + 2 * v1_r)], start=180, end=0, fill=cad_cyan, width=4)
    draw.line([(v2_cx - v1_r, sec_y_crown + v1_r), (v2_cx - v1_r, sec_y_invert)], fill=cad_cyan, width=4)
    draw.line([(v2_cx + v1_r, sec_y_crown + v1_r), (v2_cx + v1_r, sec_y_invert)], fill=cad_cyan, width=4)
    draw.line([(v2_cx - v1_r, sec_y_invert), (v2_cx + v1_r, sec_y_invert)], fill=cad_white, width=4)
    # Carriageway invert slab
    draw.rectangle([(v2_cx - v1_r + 4, sec_y_invert - 12), (v2_cx + v1_r - 4, sec_y_invert)], fill=(30, 41, 59), outline=cad_amber, width=2)
    draw.text((v2_cx - 40, sec_y_invert - 50), "TUBE 2 (SB)", fill=cad_white, font=font_sub)
    draw.text((v2_cx - 50, sec_y_invert - 30), "SPACE CLASS: U", fill=cad_cyan, font=font_sm)

    # Evacuation Passageway connecting Vault 1 and Vault 2 in section
    draw.rectangle([(v1_cx + v1_r, sec_y_invert - 35), (v2_cx - v1_r, sec_y_invert)], fill=cross_fill, outline=cad_green, width=3)
    draw.text(((v1_cx + v2_cx)//2 - 60, sec_y_invert - 24), "EMERGENCY PASSAGEWAY", fill=cad_green, font=font_sm)

    # Central Exhaust Chimney Shaft in section
    v_shaft_x = 1000
    v_shaft_w = 70
    draw.rectangle([(v_shaft_x, sec_y_ground - 30), (v_shaft_x + v_shaft_w, sec_y_invert)], fill=vent_fill, outline=cad_purple, width=3)
    draw.text((v_shaft_x - 20, sec_y_ground - 55), "SURFACE HEADHOUSE (+3.5m)", fill=cad_amber, font=font_sm)
    draw.text((v_shaft_x + 8, (sec_y_ground + sec_y_invert)//2 - 10), "VENT SHAFT", fill=cad_purple, font=font_sm)

    # 5. Bottom Right Cadastral Legend & Compliance Block
    leg_x = w - margin - 460
    leg_y = divider_y + 40
    leg_w = 440
    leg_h = 360
    draw.rectangle([(leg_x, leg_y), (leg_x + leg_w, leg_y + leg_h)], fill=(15, 23, 42), outline=cad_cyan, width=2)
    draw.text((leg_x + 20, leg_y + 15), "SVAMITVA / LADM CADASTRAL CLASSIFICATION", fill=cad_amber, font=font_sub)

    legend_items = [
        ("Space Class U", "Subterranean Sub-Surface Envelope (Z < 0.0m)", cad_purple),
        ("Space Class S", "Surface Land & Portal Retaining Walls (Z = 0.0m)", cad_green),
        ("Rights: PUB", "National Public Highway Right-of-Way (MoRTH)", cad_cyan),
        ("Rights: UTL", "Critical Public Utility (Ventilation & Safety)", cad_amber),
        ("2D Parent ULPIN", "28045678901240 (Authentic 14-Digit Bhu-Aadhaar)", cad_white),
        ("3D ULPIN Tube 1", "28045678901240-B02-U-PUB-TNL_TUBE1-V01", cad_cyan),
        ("3D ULPIN Tube 2", "28045678901240-B02-U-PUB-TNL_TUBE2-V01", cad_cyan),
        ("Dispute Check", "ZERO OVERLAPS • DISPUTE-FREE SUB-SURFACE REGISTRY", cad_green)
    ]

    for idx, (title, desc, color) in enumerate(legend_items):
        iy = leg_y + 50 + idx * 36
        draw.rectangle([(leg_x + 15, iy), (leg_x + 27, iy + 12)], fill=color)
        draw.text((leg_x + 35, iy - 2), f"{title}:", fill=color, font=font_sm)
        draw.text((leg_x + 160, iy - 2), desc[:36], fill=cad_white, font=font_sm)

    # 6. Save image to designated path
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_p), format="PNG", quality=95)
    print(f"[OK] Generated CAD Tunnel Blueprint: {out_p} ({w}x{h})")
    return str(out_p)

if __name__ == "__main__":
    p1 = generate_tunnel_cad_blueprint("sample_blueprints/tunnel_infrastructure_blueprint.png")
    p2 = generate_tunnel_cad_blueprint("storage/blueprints/tunnel_infrastructure_blueprint.png")
    # Also save to artifact directory so it's viewable by the user
    artifact_dir = Path(r"C:\Users\ediga\.gemini\antigravity\brain\718271d0-21f1-4576-958d-08d8c73c6bba")
    if artifact_dir.exists():
        generate_tunnel_cad_blueprint(str(artifact_dir / "tunnel_infrastructure_blueprint.png"))
