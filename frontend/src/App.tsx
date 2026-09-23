import { useState } from 'react'
import './App.css'

function App() {
  const [backendStatus, setBackendStatus] = useState('Not checked')

  async function checkBackend() {
    const response = await fetch('/health')
    const data = await response.json()

    setBackendStatus(data.status)
  }

  return (
    <main>
      <button type="button" onClick={checkBackend}>
        Check backend
      </button>
      <h1>ApplyPilot</h1>
      <p>A workspace for tracking job applications and preparing for target roles.</p>
      <p>Backend status: {backendStatus}</p>
    </main>
  )
}

export default App
