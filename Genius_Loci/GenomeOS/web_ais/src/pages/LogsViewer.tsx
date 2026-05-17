import React, { useState, useEffect } from 'react'
import { ScrollText, Filter } from 'lucide-react'

interface LogEntry {
  id: number
  timestamp: string
  level: string
  source: string
  message: string
  robot_id?: string
}

const LogsViewer: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filter, setFilter] = useState('')
  const [levelFilter, setLevelFilter] = useState('')

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/v1/logs?limit=200')
      if (res.ok) {
        const data = await res.json()
        setLogs(data)
      }
    } catch (e) {
      // Use sample data if API not available
      setLogs([
        { id: 1, timestamp: new Date().toISOString(), level: 'INFO', source: 'SLAM', message: 'Map updated, 15 keyframes' },
        { id: 2, timestamp: new Date().toISOString(), level: 'INFO', source: 'Planner', message: 'Path computed: 24 waypoints' },
        { id: 3, timestamp: new Date().toISOString(), level: 'WARNING', source: 'Balancer', message: 'Stability score: 0.72' },
      ])
    }
  }

  const levelColors: Record<string, string> = {
    DEBUG: 'text-gray-500',
    INFO: 'text-blue-600',
    WARNING: 'text-amber-600',
    ERROR: 'text-red-600',
  }

  const filtered = logs.filter(l => 
    l.message.toLowerCase().includes(filter.toLowerCase()) &&
    (!levelFilter || l.level === levelFilter)
  )

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search logs..."
            value={filter}
            onChange={e => setFilter(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
          />
        </div>
        <select value={levelFilter} onChange={e => setLevelFilter(e.target.value)}
          className="border rounded-lg px-4 py-2">
          <option value="">All Levels</option>
          <option value="DEBUG">DEBUG</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
        </select>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="max-h-[calc(100vh-200px)] overflow-auto">
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium">Time</th>
                <th className="px-4 py-2 text-left text-xs font-medium">Level</th>
                <th className="px-4 py-2 text-left text-xs font-medium">Source</th>
                <th className="px-4 py-2 text-left text-xs font-medium">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y text-sm">
              {filtered.map(log => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-500 font-mono text-xs">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </td>
                  <td className={`px-4 py-2 font-medium ${levelColors[log.level] || ''}`}>
                    {log.level}
                  </td>
                  <td className="px-4 py-2 text-gray-600">{log.source}</td>
                  <td className="px-4 py-2">{log.message}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">No logs</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default LogsViewer
