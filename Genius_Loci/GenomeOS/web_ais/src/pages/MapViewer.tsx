import React from 'react'
import RobotMap from '../components/RobotMap'
import { useStore } from '../store'

const MapViewer: React.FC = () => {
  const robots = useStore(s => s.robots)

  return (
    <div className="bg-white rounded-lg shadow h-[calc(100vh-120px)]">
      <RobotMap robots={robots} fullSize />
    </div>
  )
}

export default MapViewer
