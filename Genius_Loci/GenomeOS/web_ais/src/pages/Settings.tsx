import React from 'react'
import { Settings, Server, Wifi, Database } from 'lucide-react'

const SettingsPage: React.FC = () => {
  return (
    <div className="max-w-2xl space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Server className="w-5 h-5" /> Server Configuration
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Server Host</label>
            <input type="text" defaultValue="localhost" className="w-full border rounded-lg px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Server Port</label>
            <input type="number" defaultValue={8000} className="w-full border rounded-lg px-3 py-2" />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Wifi className="w-5 h-5" /> WebSocket Settings
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Reconnect Interval (s)</label>
            <input type="number" defaultValue={5} className="w-full border rounded-lg px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Heartbeat Timeout (s)</label>
            <input type="number" defaultValue={10} className="w-full border rounded-lg px-3 py-2" />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Database className="w-5 h-5" /> System Info
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between py-2 border-b">
            <span className="text-gray-500">Version</span>
            <span>0.2.0</span>
          </div>
          <div className="flex justify-between py-2 border-b">
            <span className="text-gray-500">Robot ID</span>
            <span className="font-mono">genius_loci_001</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-500">Build Date</span>
            <span>2026-05-14</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
