import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { MapPin, Layers, Bot } from 'lucide-react'
import { useStore } from '../store'
import RobotMap from '../components/RobotMap'

const MapViewer: React.FC = () => {
  const robots = useStore(s => s.robots)
  const [showZones, setShowZones] = useState(true)
  const [showTrails, setShowTrails] = useState(true)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      {/* Map Controls */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-xl shadow-sm p-4 flex flex-wrap items-center gap-4"
      >
        <div className="flex items-center gap-2">
          <MapPin className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-slate-800">Warehouse Map</h3>
        </div>

        <div className="ml-auto flex items-center gap-3">
          {/* Legend */}
          <div className="flex items-center gap-4 text-xs text-slate-500 mr-4">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-slate-400 opacity-30 inline-block border border-slate-400" /> Racks
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-amber-400 opacity-25 inline-block border border-amber-400" /> Docks
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-emerald-400 opacity-20 inline-block border border-emerald-400" /> Charging
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> Free
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" /> Busy
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> Error
            </span>
          </div>

          {/* Toggles */}
          <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
            <input
              type="checkbox"
              checked={showZones}
              onChange={(e) => setShowZones(e.target.checked)}
              className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
            />
            <Layers className="w-4 h-4" />
            Zones
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
            <input
              type="checkbox"
              checked={showTrails}
              onChange={(e) => setShowTrails(e.target.checked)}
              className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
            />
            Trails
          </label>
        </div>
      </motion.div>

      {/* Robot List Overlay */}
      {robots.length > 0 && (
        <motion.div
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="flex gap-2 flex-wrap"
        >
          {robots.map(robot => (
            <motion.div
              key={robot.id}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium ${
                robot.status === 'free' ? 'bg-emerald-50 text-emerald-700' :
                robot.status === 'busy' ? 'bg-blue-50 text-blue-700' :
                robot.status === 'charging' ? 'bg-amber-50 text-amber-700' :
                robot.status === 'error' ? 'bg-red-50 text-red-700' :
                'bg-gray-50 text-gray-600'
              }`}
            >
              <Bot className="w-3.5 h-3.5" />
              {robot.name}
              <span className="text-xs opacity-60">
                ({robot.x.toFixed(0)}, {robot.y.toFixed(0)})
              </span>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Map */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-xl shadow-sm overflow-hidden"
        style={{ height: 'calc(100vh - 280px)', minHeight: '500px' }}
      >
        <RobotMap robots={robots} fullSize />
      </motion.div>
    </motion.div>
  )
}

export default MapViewer
