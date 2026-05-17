import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Bot, Battery, MapPin, Activity, ArrowLeft } from 'lucide-react'
import { useStore } from '../store'

const RobotDetails: React.FC = () => {
  const { robotId } = useParams<{ robotId: string }>()
  const robots = useStore(s => s.robots)
  const robot = robots.find(r => r.id === robotId)

  if (!robot) {
    return (
      <div className="text-center py-12">
        <Bot className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h2 className="text-lg font-medium text-gray-500">Robot not found</h2>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
            robot.status === 'free' ? 'bg-emerald-100' :
            robot.status === 'busy' ? 'bg-blue-100' :
            robot.status === 'error' ? 'bg-red-100' : 'bg-gray-100'
          }`}>
            <Bot className={`w-8 h-8 ${
              robot.status === 'free' ? 'text-emerald-600' :
              robot.status === 'busy' ? 'text-blue-600' :
              robot.status === 'error' ? 'text-red-600' : 'text-gray-600'
            }`} />
          </div>
          <div>
            <h2 className="text-2xl font-bold">{robot.name}</h2>
            <p className="text-gray-500 capitalize">{robot.status}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-500 mb-1">
              <MapPin className="w-4 h-4" />
              <span className="text-sm">Position</span>
            </div>
            <p className="text-lg font-semibold">
              ({robot.x.toFixed(2)}, {robot.y.toFixed(2)})
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-500 mb-1">
              <Activity className="w-4 h-4" />
              <span className="text-sm">Orientation</span>
            </div>
            <p className="text-lg font-semibold">
              {(robot.theta * 180 / Math.PI).toFixed(1)}°
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-500 mb-1">
              <Battery className="w-4 h-4" />
              <span className="text-sm">Battery</span>
            </div>
            <p className={`text-lg font-semibold ${
              robot.battery > 50 ? 'text-emerald-600' :
              robot.battery > 20 ? 'text-amber-600' : 'text-red-600'
            }`}>
              {Math.round(robot.battery)}%
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-500 mb-1">
              <Bot className="w-4 h-4" />
              <span className="text-sm">Task</span>
            </div>
            <p className="text-lg font-semibold">
              {robot.currentTaskId || 'None'}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold mb-4">Robot Controls</h3>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Send to Charging
          </button>
          <button className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700">
            Emergency Stop
          </button>
          <button className="px-4 py-2 border rounded-lg hover:bg-gray-50">
            Reset Odometry
          </button>
        </div>
      </div>
    </div>
  )
}

export default RobotDetails
