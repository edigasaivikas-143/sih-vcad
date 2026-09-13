import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.css' // Assumes styles.css is moved here

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
