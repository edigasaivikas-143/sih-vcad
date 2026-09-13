import { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import "cesium/Build/Cesium/Widgets/widgets.css";

export default function MapViewer() {
  const cesiumContainer = useRef(null);

  useEffect(() => {
    // Required to render terrain and high-res base maps in production
    // Without this, the viewer fails to load offline terrain configs properly
    Cesium.Ion.defaultAccessToken = 'YOUR_CESIUM_ION_TOKEN_HERE';

    const viewer = new Cesium.Viewer(cesiumContainer.current, {
      terrainProvider: Cesium.createWorldTerrain(),
      animation: false,
      timeline: false,
    });
    
    // Add 3D buildings layer
    viewer.scene.primitives.add(Cesium.createOsmBuildings());

    // Fly to the designated demonstration city
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(-87.6298, 41.8781, 800), // Chicago coordinates
      orientation: {
        heading: Cesium.Math.toRadians(0),
        pitch: Cesium.Math.toRadians(-45)
      }
    });

    return () => viewer.destroy();
  }, []);

  return <div ref={cesiumContainer} style={{ height: "100%", width: "100%" }} />;
}
