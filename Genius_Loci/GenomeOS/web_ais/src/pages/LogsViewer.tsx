import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ScrollText, Filter, AlertTriangle, Info, AlertCircle, Bug, Wifi, WifiOff } from 'lucide-react'
import { useStore } from '../store'

interface LogEntry {
  id: string
  timestamp: string
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG'
  module: string
  message: string
}

const LogsViewer: React.FC = () => {
  const wsConnected = useStore(s => s.wsConnected)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filter, setFilter] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('ALL')

  // Simulated logs for demo
  useEffect(() => {
    const sampleLogs: LogEntry[] = [
      { id: '1', timestamp: new Date(Date.now() - 1000).toISOString(), level: 'INFO', module: 'SLAM.Main', message: 'GraphSLAM initialized with resolution 0.05m' },
      { id: '2', timestamp: new Date(Date.now() - 3000).toISOString(), level: 'INFO', module: 'Nav.Planner', message: 'A* planner initialized with 200x200 grid' },
      { id: '3', timestamp: new Date(Date.now() - 5000).toISOString(), level: 'DEBUG', module: 'Sensors.IMU', message: 'MPU6050 initialized, calibration complete' },
      { id: '4', timestamp: new Date(Date.now() - 7000).toISOString(), level: 'INFO', module: 'Server.WS', message: 'Robot GL-001 connected via WebSocket' },
      { id: '5', timestamp: new Date(Date.now() - 10000).toISOString(), level: 'WARNING', module: 'Motion.DWA', message: 'Obstacle detected at (12.5, -8.3), replanning path' },
      { id: '6', timestamp: new Date(Date.now() - 12000).toISOString(), level: 'INFO', module: 'Tasks.Exec', message: 'Task TASK-4521 assigned to GL-002' },
      { id: '7', timestamp: new Date(Date.now() - 15000).toISOString(), level: 'ERROR', module: 'Stereo.Depth', message: 'Camera sync timeout, retrying...' },
      { id: '8', timestamp: new Date(Date.now() - 18000).toISOString(), level: 'INFO', module: 'SLAM.Grid', message: 'Keyframe 42 created at (15.2, 8.7)' },
      { id: '9', timestamp: new Date(Date.now() - 20000).toISOString(), level: 'DEBUG', module: 'Balancer.PID', message: 'Stability score: 0.97, no adjustment needed' },
      { id: '10', timestamp: new Date(Date.now() - 25000).toISOString(), level: 'INFO', module: 'Gripper.Ctrl', message: 'Payload detected, gripper holding 12.5kg' },
      { id: '11', timestamp: new Date(Date.now() - 28000).toISOString(), level: 'WARNING', module: 'Battery.Mon', message: 'GL-003 battery at 18%, initiating charging protocol' },
      { id: '12', timestamp: new Date(Date.now() - 30000).toISOString(), level: 'INFO', module: 'Server.Auth', message: 'User admin logged in from 192.168.1.105' },
    ]
    setLogs(sampleLogs)
  }, [])

  const getLevelStyle = (level: string) => {
    switch (level) {
      case 'ERROR': return { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', icon: Bug }
      case 'WARNING': return { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', icon: AlertTriangle }
      case 'DEBUG': return { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', icon: AlertCircle }
      default: return { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', icon: Info }
    }
  }

  const filteredLogs = logs.filter(log => {
    const matchesLevel = levelFilter === 'ALL' || log.level === levelFilter
    const matchesSearch = !filter ||
      log.message.toLowerCase().includes(filter.toLowerCase()) ||
      log.module.toLowerCase().includes(filter.toLowerCase())
    return matchesLevel && matchesSearch
  })

  const levels = ['ALL', 'INFO', 'WARNING', 'ERROR', 'DEBUG']

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <motion.div
        initial={{ y: -10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between"
      >
        <div>
          <h2 className="text-lg font-semibold text-slate-800">System Logs</h2>
          <p className="text-sm text-gray-500">Real-time log monitoring and filtering</p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          {wsConnected ? (
            <><Wifi className="w-4 h-4 text-emerald-500" /><span className="text-emerald-600">Live</span></>
          ) : (
            <><WifiOff className="w-4 h-4 text-gray-400" /><span className="text-gray-500">Offline</span></>
          )}
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-xl shadow-sm p-4"
      >
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative flex-1 min-w-[200px]">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={filter}
              onChange={e => setFilter(e.target.value)}
              placeholder="Filter logs by message or module..."
              className="w-full border border-gray-300 rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div className="flex gap-2">
            {levels.map(level => (
              <button
                key={level}
                onClick={() => setLevelFilter(level)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  levelFilter === level
                    ? 'bg-emerald-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Log Counts */}
      <div className="grid grid-cols-4 gap-4">
        {levels.filter(l => l !== 'ALL').map(level => {
          const count = logs.filter(l => l.level === level).length
          const style = getLevelStyle(level)
          return (
            <motion.div
              key={level}
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className={`${style.bg} rounded-xl p-3 text-center`}
            >
              <p className={`text-xl font-bold ${style.text}`}>{count}</p>
              <p className="text-xs text-gray-500">{level}</p>
            </motion.div>
          )
        })}
      </div>

      {/* Logs Table */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-xl shadow-sm overflow-hidden"
      >
        <div className="p-4 border-b flex items-center gap-2">
          <ScrollText className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-slate-800">Log Entries</h3>
          <span className="ml-auto text-sm text-gray-500">{filteredLogs.length} entries</span>
        </div>

        <div className="divide-y max-h-[600px] overflow-auto">
          <AnimatePresence>
            {filteredLogs.map((log, index) => {
              const style = getLevelStyle(log.level)
              const Icon = style.icon
              return (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: index * 0.02 }}
                  className="p-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 w-6 h-6 rounded-md ${style.bg} flex items-center justify-center flex-shrink-0`}>
                      <Icon className={`w-3.5 h-3.5 ${style.text}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${style.bg} ${style.text} border ${style.border}`}>
                          {log.level}
                        </span>
                        <span className="text-xs font-mono text-slate-500">{log.module}</span>
                        <span className="text-xs text-gray-400 ml-auto">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-slate-700 mt-1">{log.message}</p>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
          {filteredLogs.length === 0 && (
            <div className="p-12 text-center text-gray-400">
              <ScrollText className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No logs match the current filter</p>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}

export default LogsViewer
