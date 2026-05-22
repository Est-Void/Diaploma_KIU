import React from 'react'
import { motion } from 'framer-motion'
import { Server, Wifi, Database, Shield, Bot, Activity, HardDrive } from 'lucide-react'
import { useStore } from '../store'

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0 }
}

const Settings: React.FC = () => {
  const wsConnected = useStore(s => s.wsConnected)
  const robots = useStore(s => s.robots)
  const user = useStore(s => s.user)

  const settingsGroups = [
    {
      title: 'Server Configuration',
      icon: Server,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
      items: [
        { label: 'Server Host', value: 'localhost:8000' },
        { label: 'API Version', value: 'v1' },
        { label: 'Protocol', value: 'REST + WebSocket' },
      ]
    },
    {
      title: 'WebSocket Connection',
      icon: Wifi,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
      items: [
        { label: 'Status', value: wsConnected ? 'Connected' : 'Disconnected' },
        { label: 'Endpoint', value: 'ws://localhost:8000/ws/client' },
        { label: 'Auto-reconnect', value: 'Enabled' },
      ]
    },
    {
      title: 'Database',
      icon: Database,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
      items: [
        { label: 'Type', value: 'PostgreSQL 14+' },
        { label: 'ORM', value: 'SQLAlchemy 2.0' },
        { label: 'Migrations', value: 'Alembic' },
      ]
    },
    {
      title: 'Authentication',
      icon: Shield,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
      items: [
        { label: 'Method', value: 'JWT (HS256)' },
        { label: 'Token expiry', value: '30 days' },
        { label: 'Current user', value: user?.username || 'Not logged in' },
        { label: 'Role', value: user?.role || 'N/A' },
      ]
    },
    {
      title: 'Robot Fleet',
      icon: Bot,
      color: 'text-cyan-600',
      bg: 'bg-cyan-50',
      items: [
        { label: 'Connected robots', value: robots.length.toString() },
        { label: 'Max supported', value: '8' },
        { label: 'Communication', value: 'ZeroMQ + WebSocket' },
      ]
    },
    {
      title: 'System Health',
      icon: Activity,
      color: 'text-red-600',
      bg: 'bg-red-50',
      items: [
        { label: 'Status', value: 'Operational' },
        { label: 'Version', value: '0.2.0' },
        { label: 'Environment', value: 'Development' },
      ]
    },
  ]

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <motion.div
        initial={{ y: -10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <h2 className="text-lg font-semibold text-slate-800">System Settings</h2>
        <p className="text-sm text-gray-500">View and manage system configuration</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {settingsGroups.map((group, index) => (
          <motion.div
            key={group.title}
            variants={itemVariants}
            initial="hidden"
            animate="show"
            transition={{ delay: index * 0.06 }}
            className="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow"
          >
            <div className="p-4 border-b">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl ${group.bg} flex items-center justify-center`}>
                  <group.icon className={`w-5 h-5 ${group.color}`} />
                </div>
                <h3 className="font-semibold text-slate-800">{group.title}</h3>
              </div>
            </div>
            <div className="divide-y">
              {group.items.map(item => (
                <div key={item.label} className="px-4 py-3 flex items-center justify-between">
                  <span className="text-sm text-gray-500">{item.label}</span>
                  <span className={`text-sm font-medium ${
                    item.value === 'Connected' ? 'text-emerald-600' :
                    item.value === 'Disconnected' ? 'text-red-600' :
                    item.value === 'Operational' ? 'text-emerald-600' :
                    'text-slate-700'
                  }`}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Storage Info */}
      <motion.div
        variants={itemVariants}
        initial="hidden"
        animate="show"
        className="bg-white rounded-xl shadow-sm p-6"
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center">
            <HardDrive className="w-5 h-5 text-slate-600" />
          </div>
          <h3 className="font-semibold text-slate-800">Storage Information</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Tasks', value: useStore.getState().tasks.length },
            { label: 'Robots', value: robots.length },
            { label: 'Maps', value: '1' },
            { label: 'Log Entries', value: 'Real-time' },
          ].map(item => (
            <div key={item.label} className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-lg font-bold text-slate-800">{item.value}</p>
              <p className="text-xs text-gray-500">{item.label}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  )
}

export default Settings
