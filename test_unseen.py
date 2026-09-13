import cv2
import numpy as np
import urllib.request
import json
import base64

# Create a brand-new custom 2D blueprint (800x600)
img = np.ones((600, 800, 3), dtype=np.uint8) * 250

# Draw outer exterior walls (black, 6px)
cv2.rectangle(img, (80, 80), (720, 520), (30, 30, 30), 6)

# Interior dividing wall 1 (vertical at x=400)
cv2.line(img, (400, 80), (400, 520), (30, 30, 30), 4)
# Doorway cut in wall 1
cv2.line(img, (400, 260), (400, 320), (250, 250, 250), 6)

# Interior dividing wall 2 (horizontal at y=300 on right side)
cv2.line(img, (400, 300), (720, 300), (30, 30, 30), 4)
# Doorway cut in wall 2
cv2.line(img, (530, 300), (590, 300), (250, 250, 250), 6)

cv2.imwrite("uploads/new_unseen_blueprint.png", img)

with open("uploads/new_unseen_blueprint.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

req = urllib.request.Request(
    "http://localhost:8080/api/upload",
    data=json.dumps({
        "filename": "new_unseen_blueprint.png",
        "content_base64": "data:image/png;base64," + b64,
        "parent_2d_ulpin": "55554444333322",
        "floors_count": 1
    }).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode("utf-8"))

print("=== Unseen Arbitrary Blueprint Upload Result ===")
print("Parent ULPIN:", data["parent_2d_ulpin"])
print("Blueprint Type:", data["blueprint_type"])
print("Building Dimensions:", data["building_dimensions_m"])
print("Total Geometries:", len(data["geometries"]))
rooms = [g for g in data["geometries"] if g["type"] == "ROOM"]
walls = [g for g in data["geometries"] if g["type"] == "WALL"]
print(f"Rooms Extruded ({len(rooms)}):")
for r in rooms:
    print(f"  - {r['name']}: {r['carpet_area_sqm']} m2 | 3D ULPIN: {r['ulpin_3d']}")
print(f"Walls Extruded ({len(walls)}):")
for w in walls[:6]:
    print(f"  - {w['name']}: ({w['width']}m x {w['depth']}m)")
