import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import TaskManager from './pages/TaskManager'
import RobotDetails from './pages/RobotDetails'
import MapViewer from './pages/MapViewer'
import LogsViewer from './pages/LogsViewer'
import Settings from './pages/Settings'

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="tasks" element={<TaskManager />} />
          <Route path="robots/:robotId" element={<RobotDetails />} />
          <Route path="map" element={<MapViewer />} />
          <Route path="logs" element={<LogsViewer />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
