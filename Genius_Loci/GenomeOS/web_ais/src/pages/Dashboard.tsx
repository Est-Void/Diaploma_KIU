import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bot, Battery, Activity, Package, AlertTriangle, CheckCircle } from 'lucide-react'
import { useStore } from '../store'
import RobotMap from '../components/RobotMap'
import useWebSocket from '../hooks/useWebSocket'

const Dashboard: React.FC = () => {
  const robots = useStore(s => s.robots)
  const tasks = useStore(s => s.tasks)
  const wsConnected = useStore(s => s.wsConnected)
  useWebSocket()

  const stats = {
    total: robots.length,
    free: robots.filter(r => r.status === 'free').length,
    busy: robots.filter(r => r.status === 'busy').length,
    error: robots.filter(r => r.status === 'error').length,
    offline: robots.filter(r => r.status === 'offline').length,
    charging: robots.filter(r => r.status === 'charging').length,
    tasksPending: tasks.filter(t => t.status === 'pending').length,
    tasksActive: tasks.filter(t => t.status === 'in_progress').length,
    tasksCompleted: tasks.filter(t => t.status === 'completed').length,
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Robots</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
            <Bot className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-emerald-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Active</p>
              <p className="text-2xl font-bold">{stats.busy}</p>
            </div>
            <Activity className="w-8 h-8 text-emerald-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-amber-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Pending Tasks</p>
              <p className="text-2xl font-bold">{stats.tasksPending}</p>
            </div>
            <Package className="w-8 h-8 text-amber-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Errors</p>
              <p className="text-2xl font-bold">{stats.error}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Map and Robot List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h3 className="font-semibold">Live Map</h3>
          </div>
          <div className="h-96">
            <RobotMap robots={robots} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h3 className="font-semibold">Robot Status</h3>
          </div>
          <div className="divide-y max-h-96 overflow-auto">
            {robots.map(robot => (
              <Link key={robot.id} to={`/robots/${robot.id}`} className="block p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${
                      robot.status === 'free' ? 'bg-emerald-500' :
                      robot.status === 'busy' ? 'bg-blue-500' :
                      robot.status === 'charging' ? 'bg-amber-500' :
                      robot.status === 'error' ? 'bg-red-500' : 'bg-gray-400'
                    }`} />
                    <div>
                      <p className="font-medium text-sm">{robot.name}</p>
                      <p className="text-xs text-gray-500 capitalize">{robot.status}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-sm">
                    <Battery className="w-4 h-4" />
                    <span>{Math.round(robot.battery)}%</span>
                  </div>
                </div>
              </Link>
            ))}
            {robots.length === 0 && (
              <div className="p-8 text-center text-gray-400">
                <Bot className="w-12 h-12 mx-auto mb-2" />
                <p>No robots connected</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
