import React from 'react'
import MapViewer from './components/MapViewer'
import NLQueryBox from './components/NLQueryBox'

export default function App() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header style={{ padding: '15px', background: '#102a43', color: 'white' }}>
        <h1>3D ULPIN | Property Records</h1>
      </header>
      
      {/* Module H: Natural Language Query Layer */}
      <NLQueryBox />
      
      {/* 3D Visualizer */}
      <div style={{ flex: 1, position: 'relative' }}>
        <MapViewer />
      </div>
    </div>
  )
}
