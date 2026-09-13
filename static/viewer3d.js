/**
 * V-CAD High-Clarity Three.js 3D Viewer
 * Features:
 * - 360° auto-spin & smooth OrbitControls
 * - Zoom In & Zoom Out
 * - Floor-to-Floor rendering isolation
 * - Dynamic 3D HTML label projection with collision avoidance (prevents text overlapping)
 * - Vertical Exploded View Slider
 * - Raycaster click-to-inspect with smooth camera focus transitions
 * - Crisp CAD edge rendering & X-Ray glass styles
 */

class Vcad3DViewer {
  constructor(canvasId, overlayId, onSelectCallback) {
    this.canvas = document.getElementById(canvasId);
    this.overlay = document.getElementById(overlayId);
    this.onSelect = onSelectCallback;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    this.meshMap = new Map(); // id -> THREE.Mesh
    this.edgeMap = new Map(); // id -> THREE.LineSegments
    this.unitDataMap = new Map(); // id -> unit metadata
    this.labelElements = new Map(); // id -> DOM HTMLElement

    this.activeFloor = 'all';
    this.explodeFactor = 0.0;
    this.autoSpin = false;
    this.showLabels = true;
    this.renderStyle = 'cad';
    this.selectedId = null;

    this.isAnimatingFocus = false;
    this.focusTarget = new THREE.Vector3(0, 4, 0);

    this.init();
  }

  init() {
    this.container = this.canvas.parentElement || document.getElementById('canvasContainer');
    let width = this.container ? this.container.clientWidth : 0;
    let height = this.container ? this.container.clientHeight : 0;
    if (width <= 50 || height <= 50) {
      width = Math.max(400, window.innerWidth - 660);
      height = Math.max(400, window.innerHeight - 58);
    }

    // 1. Scene setup
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x060c18);

    // Subtle atmospheric fog for architectural depth
    this.scene.fog = new THREE.FogExp2(0x060c18, 0.012);

    // 2. Camera setup
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.camera.position.set(24, 22, 32);

    // 3. Renderer setup
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: false,
      preserveDrawingBuffer: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(width, height, false);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // 4. OrbitControls
    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.06;
      this.controls.maxPolarAngle = Math.PI / 2 + 0.05; // allow slightly below horizontal
      this.controls.minDistance = 4;
      this.controls.maxDistance = 120;
      this.controls.target.set(0, 5, 0);
    }

    // 5. Architectural Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.65);
    this.scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xe0f2fe, 0.9);
    dirLight1.position.set(30, 45, 25);
    dirLight1.castShadow = true;
    dirLight1.shadow.mapSize.width = 2048;
    dirLight1.shadow.mapSize.height = 2048;
    this.scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x38bdf8, 0.4);
    dirLight2.position.set(-25, 20, -25);
    this.scene.add(dirLight2);

    // Camera headlight ensures underground basements and interior rooms are always brightly lit
    this.cameraLight = new THREE.DirectionalLight(0xffffff, 0.75);
    this.camera.add(this.cameraLight);
    this.scene.add(this.camera);

    // Subtle ground grid
    const grid = new THREE.GridHelper(60, 60, 0x00f0ff, 0x172844);
    grid.position.y = -0.1;
    this.scene.add(grid);

    // 6. Events & Dynamic Responsive Synchronization
    window.addEventListener('resize', () => this.onResize());
    if (window.ResizeObserver && this.container) {
      this.resizeObserver = new ResizeObserver(() => {
        this.onResize();
      });
      this.resizeObserver.observe(this.container);
    }
    this.canvas.addEventListener('pointerdown', (e) => this.onPointerDown(e));

    // Multiple layout ticks to guarantee perfect sync across all screen dimensions
    requestAnimationFrame(() => this.onResize());
    setTimeout(() => this.onResize(), 100);
    setTimeout(() => this.onResize(), 300);

    // 7. Start render loop
    this.animate();
  }

  loadModelData(payload) {
    // Clear old scene meshes
    this.meshMap.forEach(mesh => this.scene.remove(mesh));
    this.edgeMap.forEach(edge => this.scene.remove(edge));
    this.meshMap.clear();
    this.edgeMap.clear();
    this.unitDataMap.clear();
    this.overlay.innerHTML = '';
    this.labelElements.clear();

    const geometries = payload.geometries || [];
    geometries.forEach(g => {
      this.unitDataMap.set(g.id, g);

      // Create Box Geometry
      const geom = new THREE.BoxGeometry(g.width, g.height, g.depth);
      const edges = new THREE.EdgesGeometry(geom);

      // Base Material
      let mat;
      const col = new THREE.Color(g.color);
      const edgeCol = new THREE.Color(g.edge_color);

      if (g.type === 'SLAB') {
        mat = new THREE.MeshStandardMaterial({
          color: col,
          roughness: 0.4,
          metalness: 0.1,
          transparent: true,
          opacity: 0.92
        });
      } else if (g.type === 'GROUND_LAND') {
        mat = new THREE.MeshStandardMaterial({
          color: col,
          roughness: 0.8,
          metalness: 0.05,
          transparent: true,
          opacity: 0.98
        });
      } else if (g.type === 'WALL') {
        mat = new THREE.MeshStandardMaterial({
          color: col,
          roughness: 0.85,
          metalness: 0.1,
          transparent: false,
          opacity: 0.98
        });
      } else if (g.type === 'ROOM') {
        mat = new THREE.MeshStandardMaterial({
          color: col,
          roughness: 0.35,
          metalness: 0.15,
          transparent: true,
          opacity: g.opacity || 0.88
        });
      } else {
        mat = new THREE.MeshStandardMaterial({
          color: col,
          roughness: 0.3,
          metalness: 0.15,
          transparent: true,
          opacity: g.opacity || 0.85
        });
      }

      const mesh = new THREE.Mesh(geom, mat);
      mesh.position.set(g.cx, g.cy, g.cz);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData = { id: g.id, baseCy: g.cy, floor: g.floor, data: g };

      // Crisp CAD Edge Lines
      const edgeMat = new THREE.LineBasicMaterial({
        color: edgeCol,
        linewidth: 1.5,
        transparent: true,
        opacity: 0.85
      });
      const edgeLines = new THREE.LineSegments(edges, edgeMat);
      edgeLines.position.copy(mesh.position);
      edgeLines.userData = { id: g.id, baseCy: g.cy, floor: g.floor };

      this.scene.add(mesh);
      this.scene.add(edgeLines);
      this.meshMap.set(g.id, mesh);
      this.edgeMap.set(g.id, edgeLines);

      // Create Dynamic 3D HTML Label ONLY for cadastral rooms and terraces (never walls, slabs, or plots)
      if (['ROOM', 'FLAT', 'TERRACE', 'PARKING'].includes(g.type)) {
        this.createLabelElement(g);
      }
    });

    this.applyFloorFilter();
    this.updateExplodeView();
    this.fitCameraToScene();
    requestAnimationFrame(() => this.onResize());
  }

  fitCameraToScene() {
    if (!this.camera || !this.controls) return;
    const box = new THREE.Box3();
    let hasObjects = false;
    this.meshMap.forEach((mesh) => {
      if (mesh.visible && mesh.userData?.data?.type !== 'GROUND_LAND') {
        box.expandByObject(mesh);
        hasObjects = true;
      }
    });
    if (!hasObjects) return;

    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z, 10);
    const dist = maxDim * 1.7;

    this.controls.target.copy(center);
    this.camera.position.set(center.x + dist * 0.8, center.y + dist * 0.7, center.z + dist * 1.1);
    this.controls.update();
  }

  toggleLabels(show) {
    this.showLabels = (show !== undefined) ? show : !this.showLabels;
    if (this.overlay) {
      this.overlay.style.display = this.showLabels ? 'block' : 'none';
    }
    this.updateLabelsVisibility();
    return this.showLabels;
  }

  createLabelElement(g) {
    const el = document.createElement('div');
    el.className = 'unit-3d-label';
    if (g.is_dispute) el.classList.add('dispute-label');
    
    // Short tag display e.g. "BED1" or "PARK01" or "STAIR01"
    const tag = g.unit_id || (g.ulpin_3d ? g.ulpin_3d.split('-').slice(-2, -1)[0] : '');
    if (tag && tag !== g.name) {
      el.innerHTML = `<span style="font-weight:700">${g.name}</span><br><span style="font-size:9px;color:#ffd166;font-family:monospace">${tag}</span>`;
    } else {
      el.textContent = g.name;
    }
    el.dataset.id = g.id;

    el.addEventListener('click', (e) => {
      e.stopPropagation();
      this.selectUnit(g.id);
    });

    this.overlay.appendChild(el);
    this.labelElements.set(g.id, el);
  }

  setFloor(floorCode) {
    this.activeFloor = floorCode;
    this.applyFloorFilter();
    this.fitCameraToScene();
  }

  applyFloorFilter() {
    const isAll = this.activeFloor === 'all';

    this.meshMap.forEach((mesh, id) => {
      const g = this.unitDataMap.get(id);
      const edge = this.edgeMap.get(id);
      if (!g) return;

      const isLand = g.floor === 'LAND';
      const match = isAll || (isLand ? this.activeFloor === 'LAND' : g.floor === this.activeFloor);

      if (match) {
        mesh.visible = true;
        if (edge) edge.visible = true;
        mesh.material.opacity = g.opacity || 0.85;
        mesh.material.transparent = true;
      } else {
        if (this.renderStyle === 'wireframe') {
          mesh.visible = false;
          if (edge) {
            edge.visible = true;
            edge.material.opacity = 0.15;
          }
        } else {
          // Dim non-selected floors to subtle ghost wireframe to give spatial context without clutter
          mesh.visible = false;
          if (edge) {
            edge.visible = isAll ? true : false;
          }
        }
      }
    });

    this.updateLabelsVisibility();
  }

  setExplode(val01) {
    this.explodeFactor = Math.max(0.0, Math.min(1.0, val01));
    this.updateExplodeView();
  }

  updateExplodeView() {
    const maxGap = 3.2 * this.explodeFactor;

    this.meshMap.forEach((mesh, id) => {
      const baseCy = mesh.userData.baseCy;
      const flr = String(mesh.userData.floor || '');
      let mult = 0.0;
      if (flr.startsWith('F')) {
        const n = parseInt(flr.replace(/\D/g, ''), 10);
        mult = isNaN(n) ? 1.0 : n;
      } else if (flr.startsWith('B')) {
        const n = parseInt(flr.replace(/\D/g, ''), 10);
        mult = isNaN(n) ? -1.0 : -n;
      } else if (flr === 'R00' || flr === 'ROOF' || flr === 'TERRACE') {
        mult = 12.0;
      } else if (flr === 'LAND' || flr === 'G00') {
        mult = 0.0;
      }
      const newY = baseCy + mult * maxGap;

      mesh.position.y = newY;
      const edge = this.edgeMap.get(id);
      if (edge) edge.position.y = newY;
    });

    this.updateLabelsPositions();
  }

  setRenderStyle(style) {
    this.renderStyle = style;
    this.meshMap.forEach((mesh, id) => {
      const g = this.unitDataMap.get(id);
      if (!g) return;

      if (style === 'wireframe') {
        mesh.material.wireframe = true;
        mesh.material.opacity = 0.35;
      } else if (style === 'glass') {
        mesh.material.wireframe = false;
        mesh.material.opacity = 0.22;
        mesh.material.roughness = 0.1;
        mesh.material.metalness = 0.9;
      } else {
        // Clear CAD
        mesh.material.wireframe = false;
        mesh.material.opacity = g.opacity || 0.85;
        mesh.material.roughness = 0.35;
        mesh.material.metalness = 0.15;
      }
    });
  }

  toggleAutoSpin() {
    this.autoSpin = !this.autoSpin;
    return this.autoSpin;
  }

  zoomIn() {
    if (this.controls) {
      this.camera.position.lerp(this.controls.target, 0.2);
    }
  }

  zoomOut() {
    if (this.controls) {
      const dir = new THREE.Vector3().subVectors(this.camera.position, this.controls.target).normalize();
      this.camera.position.addScaledVector(dir, 4.0);
    }
  }

  resetCamera() {
    this.activeFloor = 'all';
    this.explodeFactor = 0.0;
    this.autoSpin = false;
    if (this.controls) {
      this.controls.target.set(0, 5, 0);
    }
    this.camera.position.set(24, 22, 32);
    this.applyFloorFilter();
    this.updateExplodeView();
  }

  selectUnit(id, animateCam = true) {
    this.selectedId = id;
    const mesh = this.meshMap.get(id);
    const g = this.unitDataMap.get(id);

    // Highlight selected mesh
    this.meshMap.forEach((m, mid) => {
      const isCur = mid === id;
      const unit = this.unitDataMap.get(mid);
      if (!unit) return;

      if (isCur) {
        m.material.emissive = new THREE.Color(0xffd166);
        m.material.emissiveIntensity = 0.45;
      } else {
        m.material.emissive = new THREE.Color(0x000000);
        m.material.emissiveIntensity = 0.0;
      }
    });

    // Update label selection styles
    this.labelElements.forEach((el, lid) => {
      el.classList.toggle('selected', lid === id);
    });

    // If unit is on a floor that's currently hidden, auto-isolate that floor so user sees it clearly
    if (g && g.floor && this.activeFloor !== 'all' && this.activeFloor !== g.floor) {
      // Keep floor or switch
    }

    // Camera Glide Focus Animation
    if (mesh && animateCam) {
      this.focusOnMesh(mesh);
    }

    if (this.onSelect && g) {
      this.onSelect(g);
    }
  }

  focusOnMesh(mesh) {
    const targetPos = new THREE.Vector3();
    mesh.getWorldPosition(targetPos);

    if (this.controls) {
      const fromTarget = this.controls.target.clone();
      const fromCam = this.camera.position.clone();
      const toTarget = targetPos.clone();

      // Desired camera offset relative to target
      const offset = new THREE.Vector3(12, 10, 16);
      const toCam = toTarget.clone().add(offset);

      const startTime = performance.now();
      const duration = 500; // ms

      const animateFocusStep = (now) => {
        const progress = Math.min(1.0, (now - startTime) / duration);
        const ease = 1 - Math.pow(1 - progress, 3); // ease-out cubic

        this.controls.target.lerpVectors(fromTarget, toTarget, ease);
        this.camera.position.lerpVectors(fromCam, toCam, ease);

        if (progress < 1.0) {
          requestAnimationFrame(animateFocusStep);
        }
      };
      requestAnimationFrame(animateFocusStep);
    }
  }

  onPointerDown(event) {
    const rect = this.canvas.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const visibleMeshes = Array.from(this.meshMap.values()).filter(m => m.visible);
    const intersects = this.raycaster.intersectObjects(visibleMeshes);

    if (intersects.length > 0) {
      const topHit = intersects[0].object;
      if (topHit && topHit.userData && topHit.userData.id) {
        this.selectUnit(topHit.userData.id, true);
      }
    }
  }

  updateLabelsVisibility() {
    if (!this.showLabels) {
      this.labelElements.forEach(el => el.style.display = 'none');
      return;
    }
    const isAll = this.activeFloor === 'all';

    this.labelElements.forEach((el, id) => {
      const g = this.unitDataMap.get(id);
      if (!g) {
        el.style.display = 'none';
        return;
      }
      const isLand = g.floor === 'LAND';
      const match = isAll || (isLand ? this.activeFloor === 'LAND' : g.floor === this.activeFloor);
      el.style.display = match ? 'block' : 'none';
    });
  }

  updateLabelsPositions() {
    if (!this.showLabels) return;
    if (!this.canvas || !this.camera) return;

    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    const placedRects = [];

    const isAll = this.activeFloor === 'all';

    // Prioritize selected unit first, then flats, then common spaces
    const entries = Array.from(this.labelElements.entries()).sort((a, b) => {
      const gA = this.unitDataMap.get(a[0]);
      const gB = this.unitDataMap.get(b[0]);
      if (a[0] === this.selectedId) return -1;
      if (b[0] === this.selectedId) return 1;
      if (gA?.rights === 'PRV' && gB?.rights !== 'PRV') return -1;
      return 0;
    });

    for (const [id, el] of entries) {
      const g = this.unitDataMap.get(id);
      const mesh = this.meshMap.get(id);

      if (!g || !mesh || !mesh.visible) {
        el.style.display = 'none';
        continue;
      }

      // Check floor match
      const isLand = g.floor === 'LAND';
      const match = isAll || (isLand ? this.activeFloor === 'LAND' : g.floor === this.activeFloor);
      if (!match) {
        el.style.display = 'none';
        continue;
      }

      // Calculate 3D center in screen coords
      const worldPos = new THREE.Vector3();
      mesh.getWorldPosition(worldPos);
      worldPos.y += (g.height / 2.0) + 0.3; // position above the unit box

      // Project to 2D screen
      const screenPos = worldPos.clone().project(this.camera);

      // Check if behind camera
      if (screenPos.z > 1.0) {
        el.style.display = 'none';
        continue;
      }

      const x = (screenPos.x * 0.5 + 0.5) * width;
      const y = (-(screenPos.y * 0.5) + 0.5) * height;

      // Smart collision avoidance to strictly prevent text overlapping:
      const labelW = 100;
      const labelH = 22;
      const rect = { x1: x - labelW / 2, y1: y - labelH, x2: x + labelW / 2, y2: y };

      let overlaps = false;
      if (id !== this.selectedId) {
        for (const pr of placedRects) {
          if (!(rect.x2 < pr.x1 || rect.x1 > pr.x2 || rect.y2 < pr.y1 || rect.y1 > pr.y2)) {
            overlaps = true;
            break;
          }
        }
      }

      if (overlaps) {
        // Hide overlapping label so the view remains ultra-clear!
        el.style.display = 'none';
      } else {
        el.style.display = 'block';
        el.style.left = `${Math.round(x)}px`;
        el.style.top = `${Math.round(y)}px`;
        placedRects.push(rect);
      }
    }
  }

  onResize() {
    if (!this.renderer || !this.camera) return;
    const container = this.container || this.canvas.parentElement || document.getElementById('canvasContainer');
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    if (width <= 0 || height <= 0) return;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.updateLabelsPositions();
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    if (this.autoSpin && this.controls) {
      this.controls.autoRotate = true;
      this.controls.autoRotateSpeed = 2.0;
    } else if (this.controls) {
      this.controls.autoRotate = false;
    }

    if (this.controls) {
      this.controls.update();
    }

    // Update Cadastral True North Compass
    if (this.camera && this.controls) {
      const dx = this.camera.position.x - this.controls.target.x;
      const dz = this.camera.position.z - this.controls.target.z;
      const theta = Math.atan2(dx, dz);
      const deg = (theta * 180 / Math.PI);
      const dial = document.getElementById('compassDial');
      if (dial) {
        dial.style.transform = `rotate(${-deg}deg)`;
      }
    }

    this.renderer.render(this.scene, this.camera);
    this.updateLabelsPositions();
  }

  takeSnapshot(filename = 'vcad_cadastre_3d_snapshot.png') {
    this.renderer.render(this.scene, this.camera);
    const dataURL = this.renderer.domElement.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = filename;
    link.href = dataURL;
    link.click();
  }
}
