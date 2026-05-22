import React from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bot, Battery, Activity, Package, AlertTriangle,
  Zap, MapPin, Clock, TrendingUp
} from 'lucide-react'
import { useStore } from '../store'
import RobotMap from '../components/RobotMap'
import useWebSocket from '../hooks/useWebSocket'

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
}

const Dashboard: React.FC = () => {
  const robots = useStore(s => s.robots)
  const tasks = useStore(s => s.tasks)
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

  const statCards = [
    { label: 'Total Robots', value: stats.total, icon: Bot, border: 'border-blue-500', iconColor: 'text-blue-500', bg: 'bg-blue-50' },
    { label: 'Active', value: stats.busy, icon: Activity, border: 'border-emerald-500', iconColor: 'text-emerald-500', bg: 'bg-emerald-50' },
    { label: 'Pending Tasks', value: stats.tasksPending, icon: Package, border: 'border-amber-500', iconColor: 'text-amber-500', bg: 'bg-amber-50' },
    { label: 'Errors', value: stats.error, icon: AlertTriangle, border: 'border-red-500', iconColor: 'text-red-500', bg: 'bg-red-50' },
  ]

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'free': return { color: 'bg-emerald-500', label: 'Free' }
      case 'busy': return { color: 'bg-blue-500', label: 'Busy' }
      case 'charging': return { color: 'bg-amber-500', label: 'Charging' }
      case 'error': return { color: 'bg-red-500', label: 'Error' }
      default: return { color: 'bg-gray-400', label: 'Offline' }
    }
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <motion.div
            key={card.label}
            variants={itemVariants}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            className={`bg-white rounded-xl shadow-sm p-5 border-l-4 ${card.border} hover:shadow-md transition-shadow`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 mb-1">{card.label}</p>
                <motion.p
                  key={card.value}
                  initial={{ scale: 1.3, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="text-3xl font-bold text-slate-800"
                >
                  {card.value}
                </motion.p>
              </div>
              <div className={`w-12 h-12 rounded-xl ${card.bg} flex items-center justify-center`}>
                <card.icon className={`w-6 h-6 ${card.iconColor}`} />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Map and Robot List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <motion.div
          variants={itemVariants}
          className="lg:col-span-2 bg-white rounded-xl shadow-sm overflow-hidden"
        >
          <div className="p-4 border-b flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-emerald-600" />
              <h3 className="font-semibold text-slate-800">Live Warehouse Map</h3>
            </div>
            <Link
              to="/map"
              className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
            >
              Full Screen
            </Link>
          </div>
          <div className="h-96">
            <RobotMap robots={robots} />
          </div>
        </motion.div>

        {/* Robot Status Panel */}
        <motion.div
          variants={itemVariants}
          className="bg-white rounded-xl shadow-sm overflow-hidden"
        >
          <div className="p-4 border-b flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-emerald-600" />
              <h3 className="font-semibold text-slate-800">Robot Status</h3>
            </div>
            <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full font-medium">
              {robots.filter(r => r.status !== 'offline').length} online
            </span>
          </div>
          <div className="divide-y max-h-96 overflow-auto">
            <AnimatePresence>
              {robots.map((robot) => {
                const statusCfg = getStatusConfig(robot.status)
                return (
                  <motion.div
                    key={robot.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Link
                      to={`/robots/${robot.id}`}
                      className="block p-4 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="relative">
                            <div className={`w-3 h-3 rounded-full ${statusCfg.color}`} />
                            {robot.status === 'busy' && (
                              <span className="absolute inset-0 rounded-full bg-blue-400 animate-ping opacity-50" />
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-sm text-slate-800">{robot.name}</p>
                            <p className="text-xs text-gray-500 capitalize">{statusCfg.label}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {robot.stabilityScore !== undefined && (
                            <div className="hidden sm:flex items-center gap-1 text-xs text-slate-500">
                              <TrendingUp className="w-3 h-3" />
                              <span>{(robot.stabilityScore * 100).toFixed(0)}%</span>
                            </div>
                          )}
                          <div className="flex items-center gap-1 text-sm">
                            <Battery className={`w-4 h-4 ${
                              robot.battery > 50 ? 'text-emerald-500' :
                              robot.battery > 20 ? 'text-amber-500' : 'text-red-500'
                            }`} />
                            <span className={`font-medium ${
                              robot.battery > 50 ? 'text-emerald-600' :
                              robot.battery > 20 ? 'text-amber-600' : 'text-red-600'
                            }`}>
                              {Math.round(robot.battery)}%
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="mt-2 flex gap-3 text-xs text-slate-400">
                        <span className="flex items-center gap-1">
                          <Zap className="w-3 h-3" />
                          ({robot.x.toFixed(1)}, {robot.y.toFixed(1)})
                        </span>
                        {robot.hasPayload && (
                          <span className="flex items-center gap-1 text-amber-600">
                            <Package className="w-3 h-3" />
                            {robot.payloadWeightKg?.toFixed(1)}kg
                          </span>
                        )}
                      </div>
                    </Link>
                  </motion.div>
                )
              })}
            </AnimatePresence>
            {robots.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="p-8 text-center text-gray-400"
              >
                <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No robots connected</p>
                <p className="text-xs mt-1">Start simulation to see robots</p>
              </motion.div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Task Summary */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        <div className="bg-white rounded-xl shadow-sm p-5 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center">
            <Clock className="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Pending Tasks</p>
            <p className="text-2xl font-bold text-slate-800">{stats.tasksPending}</p>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-5 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
            <Activity className="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <p className="text-sm text-gray-500">In Progress</p>
            <p className="text-2xl font-bold text-slate-800">{stats.tasksActive}</p>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-5 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-emerald-500" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Completed</p>
            <p className="text-2xl font-bold text-slate-800">{stats.tasksCompleted}</p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default Dashboard
