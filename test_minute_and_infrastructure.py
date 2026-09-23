"""
test_minute_and_infrastructure.py
Comprehensive verification test suite for:
1. Minute Detail Architectural Feature Extraction (Columns, Thin Walls, Doors, Stairs, Railings).
2. Autonomous Infrastructure Cadastre Generation (Railways, Roads, Govt Spaces, Statues/Monuments, Master Township).
3. 2D Parent ULPIN anchors and 3D ULPIN compliant spatial coding.
4. Authentication credential enforcement (Citizen View-Only vs Admin Full-Access).
5. Specialized Cadastre API handler endpoints.
"""

import unittest
import numpy as np
import cv2
import time
import json
import asyncio

from minute_detail_extractor import extract_minute_details
from infrastructure_cadastre import (
    build_railway_cadastre,
    build_road_network_cadastre,
    build_civic_monument_cadastre,
    build_govt_spaces_cadastre,
    build_master_town_cadastre
)
from ulpin_engine import (
    CadastreUnit,
    make_official_3d_ulpin,
    normalize_2d_ulpin
)
from server import (
    api_auth_login,
    api_get_cadastre_categories,
    api_get_specialized_cadastre
)


class MockRequest:
    """Mock Starlette Request for testing async API handlers without httpx."""
    def __init__(self, json_data=None, path_params=None):
        self._json = json_data or {}
        self.path_params = path_params or {}

    async def json(self):
        return self._json


class TestMinuteDetailExtractor(unittest.TestCase):
    def setUp(self):
        # Create a synthetic 400x400 architectural blueprint image
        self.img = np.ones((400, 400, 3), dtype=np.uint8) * 255
        
        # Outer boundary walls (thick black lines)
        cv2.rectangle(self.img, (30, 30), (370, 370), (0, 0, 0), thickness=6)
        
        # Thin partition wall (thin black line, thickness=2)
        cv2.line(self.img, (200, 40), (200, 180), (0, 0, 0), thickness=2)
        
        # Freestanding structural columns (pillars)
        cv2.rectangle(self.img, (100, 100), (112, 112), (0, 0, 0), -1)
        cv2.rectangle(self.img, (290, 100), (302, 112), (0, 0, 0), -1)
        cv2.rectangle(self.img, (100, 260), (112, 272), (0, 0, 0), -1)
        
        # Staircase hatch lines
        for y in range(80, 130, 6):
            cv2.line(self.img, (50, y), (90, y), (0, 0, 0), thickness=1)

    def test_minute_detail_extraction_speed_and_structure(self):
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        bin_w = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
        
        t0 = time.time()
        features = extract_minute_details(
            gray_img=gray,
            bin_w=bin_w,
            bx=30, by=30, bw=340, bh=340,
            scale=0.05,
            cx_px=200, cy_px=200,
            floor_height_m=2.8,
            flr_tag="F01",
            z0=0.0,
            parent_ulpin="12345678901234"
        )
        dt = time.time() - t0
        
        self.assertLess(dt, 0.5, f"Extraction must be fast (<500ms), took {dt:.3f}s")
        self.assertIn("columns", features)
        self.assertIn("thin_partitions", features)
        self.assertIn("door_lintels", features)
        self.assertIn("stairs", features)
        self.assertIn("railings", features)
        self.assertGreater(features["total_minute_features"], 0)
        
        # Verify columns detected
        self.assertGreater(len(features["columns"]), 0, "Columns should be detected")
        
        # Verify 3D parameters and category tagging
        for k in ["columns", "thin_partitions", "door_lintels", "stairs", "railings"]:
            for item in features[k]:
                self.assertEqual(item.get("category"), "BUILDINGS")
                self.assertIn("ulpin_3d", item)
                self.assertIn("cx", item)
                self.assertIn("cy", item)
                self.assertIn("cz", item)
                self.assertIn("width", item)
                self.assertIn("height", item)
                self.assertIn("depth", item)


class TestInfrastructureCadastre(unittest.TestCase):
    def test_railway_cadastre(self):
        parent_ulpin = "28040001000101"
        reg, data = build_railway_cadastre(parent_ulpin)
        
        self.assertEqual(data["parent_2d_ulpin"], parent_ulpin)
        self.assertEqual(data["category"], "RAILWAY")
        self.assertGreater(len(data["geometries"]), 20)
        self.assertGreater(len(data["cadastre"]["units"]), 5)
        
        # Check that FOB has Elevated space class 'E'
        fob_units = [u for u in data["cadastre"]["units"] if "fob" in u["id"].lower()]
        self.assertGreater(len(fob_units), 0, "Foot overbridge must exist")
        self.assertEqual(fob_units[0]["space_class"], "E", "FOB must be space class E")
        self.assertEqual(fob_units[0]["category"], "RAILWAY")
        
        # Check that tracks have Rights code RLW
        track_units = [u for u in data["cadastre"]["units"] if "track" in u["id"].lower()]
        self.assertGreater(len(track_units), 0, "Railway tracks must exist")
        self.assertEqual(track_units[0]["rights"], "RLW")

    def test_road_network_cadastre(self):
        parent_ulpin = "28040001000202"
        reg, data = build_road_network_cadastre(parent_ulpin)
        
        self.assertEqual(data["parent_2d_ulpin"], parent_ulpin)
        self.assertEqual(data["category"], "ROADS")
        self.assertGreater(len(data["geometries"]), 10)
        
        # Check carriageway unit
        units = data["cadastre"]["units"]
        carriageway = [u for u in units if "carriageway" in u["id"].lower()]
        self.assertGreater(len(carriageway), 0)
        self.assertEqual(carriageway[0]["category"], "ROADS")
        self.assertEqual(carriageway[0]["rights"], "PUB")

    def test_civic_monument_cadastre(self):
        parent_ulpin = "28040001000303"
        reg, data = build_civic_monument_cadastre(parent_ulpin)
        
        self.assertEqual(data["parent_2d_ulpin"], parent_ulpin)
        self.assertEqual(data["category"], "MONUMENTS")
        
        units = data["cadastre"]["units"]
        statue_units = [u for u in units if "statue" in u["id"].lower()]
        self.assertGreater(len(statue_units), 0)
        self.assertEqual(statue_units[0]["space_class"], "V")
        self.assertEqual(statue_units[0]["category"], "MONUMENTS")

    def test_govt_spaces_cadastre(self):
        parent_ulpin = "28040001000404"
        reg, data = build_govt_spaces_cadastre(parent_ulpin)
        
        self.assertEqual(data["parent_2d_ulpin"], parent_ulpin)
        self.assertEqual(data["category"], "GOVT_SPACES")
        
        units = data["cadastre"]["units"]
        floor_units = [u for u in units if "govt_floor" in u["id"].lower()]
        self.assertGreater(len(floor_units), 3, "Secretariat should have multiple floors")
        for u in floor_units:
            self.assertEqual(u["rights"], "GOV")
            self.assertEqual(u["category"], "GOVT_SPACES")

    def test_master_town_cadastre(self):
        town_parent = "28040001000000"
        reg, data = build_master_town_cadastre(town_parent)
        
        self.assertEqual(data["parent_2d_ulpin"], town_parent)
        self.assertGreater(len(data["geometries"]), 100)
        
        # Verify all 5 categories are present
        categories = {g.get("category") for g in data["geometries"] if g.get("category")}
        self.assertIn("RAILWAY", categories)
        self.assertIn("ROADS", categories)
        self.assertIn("GOVT_SPACES", categories)
        self.assertIn("MONUMENTS", categories)
        self.assertIn("BUILDINGS", categories)


class TestAuthenticationEnforcement(unittest.TestCase):
    def test_citizen_login_success(self):
        req = MockRequest(json_data={
            "email": "user@ulpin.gov.in",
            "password": "user@1221"
        })
        res = asyncio.run(api_auth_login(req))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.body.decode("utf-8"))
        self.assertEqual(data["role"], "citizen")
        self.assertIn("token", data)
        self.assertTrue(data["success"])

    def test_admin_login_success(self):
        req = MockRequest(json_data={
            "email": "admin@ulpin.gov.in",
            "password": "adm@4523"
        })
        res = asyncio.run(api_auth_login(req))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.body.decode("utf-8"))
        self.assertEqual(data["role"], "admin")
        self.assertIn("token", data)
        self.assertTrue(data["success"])

    def test_invalid_password_rejected(self):
        req = MockRequest(json_data={
            "email": "user@ulpin.gov.in",
            "password": "wrongpassword"
        })
        res = asyncio.run(api_auth_login(req))
        self.assertEqual(res.status_code, 401)

    def test_unknown_user_rejected(self):
        req = MockRequest(json_data={
            "email": "intruder@unknown.com",
            "password": "adm@4523"
        })
        res = asyncio.run(api_auth_login(req))
        self.assertEqual(res.status_code, 401)


class TestSpecializedCadastreAPI(unittest.TestCase):
    def test_get_categories(self):
        res = asyncio.run(api_get_cadastre_categories(MockRequest()))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.body.decode("utf-8"))
        ids = [c["id"] for c in data["categories"]]
        self.assertIn("RAILWAY", ids)
        self.assertIn("ROADS", ids)
        self.assertIn("GOVT_SPACES", ids)
        self.assertIn("MONUMENTS", ids)
        self.assertIn("BUILDINGS", ids)

    def test_get_specialized_cadastre_endpoints(self):
        for sector in ["railway", "roads", "monuments", "govt_spaces", "master"]:
            req = MockRequest(path_params={"category": sector})
            res = asyncio.run(api_get_specialized_cadastre(req))
            self.assertEqual(res.status_code, 200, f"Failed for sector {sector}")
            data = json.loads(res.body.decode("utf-8"))
            self.assertIn("parent_2d_ulpin", data)
            self.assertIn("geometries", data)
            self.assertGreater(len(data["geometries"]), 0)


if __name__ == "__main__":
    unittest.main()
