"""
V-CAD Automated Verification & Health-Check Suite
Tests all endpoints, 3D ULPIN generation, blueprint ingestion,
dispute elimination, and accurate floor repetition.
"""

import sys
import json
import base64
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8080"

def run_all_tests():
    print("=" * 68)
    print("  V-CAD Engine Test Suite: Accurate 3D Cadastre & Clean Titles")
    print("=" * 68)
    
    passed = 0
    total = 11

    # Test 1: GET /api/cadastre
    try:
        req = urllib.request.urlopen(f"{BASE_URL}/api/cadastre")
        data = json.loads(req.read().decode("utf-8"))
        assert req.status == 200
        assert "cadastre" in data
        assert len(data["cadastre"]["units"]) >= 5
        print(f"[PASS 1/10] GET /api/cadastre: HTTP 200 OK | Units: {len(data['cadastre']['units'])} | Parent: {data['parent_2d_ulpin']}")
        passed += 1
    except Exception as e:
        print(f"[FAIL 1/10] GET /api/cadastre: {e}")

    # Test 2: POST /api/set-parent-ulpin
    try:
        req2 = urllib.request.Request(
            f"{BASE_URL}/api/set-parent-ulpin",
            data=json.dumps({"parent_2d_ulpin": "98765432109876"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res2 = urllib.request.urlopen(req2)
        data2 = json.loads(res2.read().decode("utf-8"))
        assert res2.status == 200
        assert data2["parent_2d_ulpin"] == "98765432109876"
        print(f"[PASS 2/10] POST /api/set-parent-ulpin: HTTP 200 OK | Parent updated to {data2['parent_2d_ulpin']}")
        passed += 1
    except Exception as e:
        print(f"[FAIL 2/10] POST /api/set-parent-ulpin: {e}")

    # Test 3: POST /api/upload with User's Uploaded Blueprint (Screenshot 2026-09-08 074503.png)
    try:
        with open("uploads/Screenshot 2026-09-08 074503.png", "rb") as f:
            b64_stairs = base64.b64encode(f.read()).decode("utf-8")
        req3 = urllib.request.Request(
            f"{BASE_URL}/api/upload",
            data=json.dumps({
                "filename": "Screenshot 2026-09-08 074503.png",
                "content_base64": "data:image/png;base64," + b64_stairs,
                "parent_2d_ulpin": "12345678901234",
                "floors_count": 1
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res3 = urllib.request.urlopen(req3)
        data3 = json.loads(res3.read().decode("utf-8"))
        assert res3.status == 200
        assert data3["floors_count"] == 1
        
        # Verify Zero Disputes / Overlaps
        dispute_geoms = [g for g in data3["geometries"] if g.get("is_dispute") is True]
        assert len(dispute_geoms) == 0, f"Found {len(dispute_geoms)} dispute geometries, expected 0"
        
        # Verify Rooms
        rooms = [g for g in data3["geometries"] if g["type"] == "ROOM"]
        assert len(rooms) >= 4
        
        print(f"[PASS 3/11] POST /api/upload (Apartment Blueprint): 1 Floor Built, 0 Disputes, {len(rooms)} Rooms Extruded")
        passed += 1
    except Exception as e:
        print(f"[FAIL 3/11] POST /api/upload (Stairs Blueprint): {e}")

    # Test 4: Floor Repetition via Blueprint Text Notes ("Typical Floor G+2")
    try:
        with open("uploads/Screenshot 2026-09-08 074503.png", "rb") as f:
            b64_stairs = base64.b64encode(f.read()).decode("utf-8")
        req4 = urllib.request.Request(
            f"{BASE_URL}/api/upload",
            data=json.dumps({
                "filename": "Screenshot 2026-09-08 074503.png",
                "content_base64": "data:image/png;base64," + b64_stairs,
                "parent_2d_ulpin": "12345678901234",
                "floor_notes": "Typical Floor (G+2) 1st to 3rd"
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res4 = urllib.request.urlopen(req4)
        data4 = json.loads(res4.read().decode("utf-8"))
        assert res4.status == 200
        assert data4["floors_count"] == 3, f"Expected 3 floors, got {data4['floors_count']}"
        
        # Check distinct floor codes and unique 3D ULPINs
        f01_rooms = [g for g in data4["geometries"] if g.get("floor") == "F01" and g["type"] == "ROOM"]
        f02_rooms = [g for g in data4["geometries"] if g.get("floor") == "F02" and g["type"] == "ROOM"]
        f03_rooms = [g for g in data4["geometries"] if g.get("floor") == "F03" and g["type"] == "ROOM"]
        assert len(f01_rooms) > 0 and len(f02_rooms) > 0 and len(f03_rooms) > 0
        
        ulpins = set(g["ulpin_3d"] for g in data4["geometries"] if "ulpin_3d" in g)
        assert len(ulpins) >= (len(f01_rooms) * 3)
        print(f"[PASS 4/11] Floor Repetition Text Parsing: Auto-detected 3 Floors (G+2) with {len(ulpins)} Unique 3D ULPINs")
        passed += 1
    except Exception as e:
        print(f"[FAIL 4/11] Floor Repetition Text Parsing: {e}")

    # Test 5: POST /api/upload with User's 1BHK Cottage Blueprint PNG
    try:
        with open("sample_blueprints/user_test_blueprint.png", "rb") as f:
            b64_cottage = base64.b64encode(f.read()).decode("utf-8")
        req_c = urllib.request.Request(
            f"{BASE_URL}/api/upload",
            data=json.dumps({
                "filename": "user_test_blueprint.png",
                "content_base64": "data:image/png;base64," + b64_cottage,
                "parent_2d_ulpin": "12345678901234",
                "floors_count": 1
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res_c = urllib.request.urlopen(req_c)
        data_c = json.loads(res_c.read().decode("utf-8"))
        assert res_c.status == 200
        assert data_c["floors_count"] == 1
        c_walls = [g for g in data_c["geometries"] if g["type"] == "WALL"]
        c_rooms = [g for g in data_c["geometries"] if g["type"] == "ROOM"]
        assert len(c_walls) >= 4
        assert len(c_rooms) >= 4
        print(f"[PASS 5/11] POST /api/upload (User Cottage Blueprint): 1 Floor Built | {len(c_walls)} Extruded Walls, {len(c_rooms)} Rooms")
        passed += 1
    except Exception as e:
        print(f"[FAIL 5/11] POST /api/upload (User Cottage): {e}")

    # Test 6: POST /api/upload with SVG blueprint
    try:
        with open("sample_blueprints/sample_blueprint.svg", "rb") as f:
            b64_svg = base64.b64encode(f.read()).decode("utf-8")
        req6 = urllib.request.Request(
            f"{BASE_URL}/api/upload",
            data=json.dumps({
                "filename": "blueprint.svg",
                "content_base64": "data:image/svg+xml;base64," + b64_svg,
                "parent_2d_ulpin": "12345678901234",
                "floors_count": 1
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res6 = urllib.request.urlopen(req6)
        data6 = json.loads(res6.read().decode("utf-8"))
        assert res6.status == 200
        print(f"[PASS 6/10] POST /api/upload (SVG Vector): HTTP 200 OK | Geometries: {len(data6['geometries'])}")
        passed += 1
    except Exception as e:
        print(f"[FAIL 6/10] POST /api/upload (SVG): {e}")

    # Test 7: POST /api/upload with JSON cadastre
    try:
        with open("sample_blueprints/sample_cadastre.json", "r", encoding="utf-8") as f:
            cad_json = json.load(f)
        req7 = urllib.request.Request(
            f"{BASE_URL}/api/upload",
            data=json.dumps({
                "parent_2d_ulpin": "12345678901234",
                "is_cadastre_json": True,
                "objects": cad_json["objects"],
                "relationships": cad_json["relationships"],
                "floors_count": 1
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res7 = urllib.request.urlopen(req7)
        data7 = json.loads(res7.read().decode("utf-8"))
        assert res7.status == 200
        print(f"[PASS 7/10] POST /api/upload (JSON Dataset): HTTP 200 OK | Units: {len(data7['cadastre']['units'])}")
        passed += 1
    except Exception as e:
        print(f"[FAIL 7/10] POST /api/upload (JSON): {e}")

    # Test 8: GET /api/export/obj
    try:
        res8 = urllib.request.urlopen(f"{BASE_URL}/api/export/obj")
        content8 = res8.read()
        assert res8.status == 200
        assert len(content8) > 500
        print(f"[PASS 8/10] GET /api/export/obj: HTTP 200 OK | Exported Wavefront OBJ ({len(content8)} bytes)")
        passed += 1
    except Exception as e:
        print(f"[FAIL 8/10] GET /api/export/obj: {e}")

    # Test 9: GET /api/export/geojson
    try:
        res9 = urllib.request.urlopen(f"{BASE_URL}/api/export/geojson")
        content9 = res9.read()
        assert res9.status == 200
        assert len(content9) > 50
        print(f"[PASS 9/10] GET /api/export/geojson: HTTP 200 OK | Exported 3D GeoJSON ({len(content9)} bytes)")
        passed += 1
    except Exception as e:
        print(f"[FAIL 9/10] GET /api/export/geojson: {e}")

    # Test 10: GET / & Favicon (Static Frontend)
    try:
        res10 = urllib.request.urlopen(f"{BASE_URL}/")
        html = res10.read().decode("utf-8")
        assert res10.status == 200
        assert "V-CAD" in html
        res_fav = urllib.request.urlopen(f"{BASE_URL}/favicon.ico")
        assert res_fav.status == 200
        print(f"[PASS 10/11] GET / & /favicon.ico: HTTP 200 OK | Frontend HTML and Icons Healthy")
        passed += 1
    except Exception as e:
        print(f"[FAIL 10/11] GET / & Static: {e}")

    # Test 11: POST /api/analyze-blueprint (Live Computer Vision Analysis)
    try:
        with open("sample_blueprints/user_test_blueprint.png", "rb") as f:
            b64_test = base64.b64encode(f.read()).decode("utf-8")
        req11 = urllib.request.Request(
            f"{BASE_URL}/api/analyze-blueprint",
            data=json.dumps({
                "filename": "test_cv.png",
                "content_base64": "data:image/png;base64," + b64_test,
                "floors_count": 1
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res11 = urllib.request.urlopen(req11)
        data11 = json.loads(res11.read().decode("utf-8"))
        assert res11.status == 200
        assert data11["success"] is True
        assert len(data11["analysis"]["rooms"]) >= 4
        assert "pixel_bbox" in data11["analysis"]["rooms"][0]
        print(f"[PASS 11/11] POST /api/analyze-blueprint: Real OpenCV CV Analysis | {len(data11['analysis']['rooms'])} Rooms with Pixel Bounding Boxes")
        passed += 1
    except Exception as e:
        print(f"[FAIL 11/11] POST /api/analyze-blueprint: {e}")

    print("-" * 68)
    print(f"Results: {passed}/{total} Tests Passed ({round(passed/total*100)}% Success Rate)")
    print("=" * 68)
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
