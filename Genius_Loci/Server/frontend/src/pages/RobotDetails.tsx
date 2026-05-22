import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Bot, Battery, MapPin, Activity, ArrowLeft,
  Zap, Gauge, GripHorizontal, Weight, RotateCcw,
  Radio, Crosshair, Shield, Play, Square, Home
} from 'lucide-react'
import { useStore } from '../store'

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } }
}

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0 }
}

const RobotDetails: React.FC = () => {
  const { robotId } = useParams<{ robotId: string }>()
  const robots = useStore(s => s.robots)
  const robot = robots.find(r => r.id === robotId)

  if (!robot) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-12"
      >
        <Bot className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h2 className="text-lg font-medium text-gray-500">Robot not found</h2>
        <Link to="/" className="text-emerald-600 hover:underline mt-2 inline-block">
          Back to Dashboard
        </Link>
      </motion.div>
    )
  }

  const statusConfig = {
    free: { color: 'bg-emerald-100 text-emerald-700', icon: 'Ready' },
    busy: { color: 'bg-blue-100 text-blue-700', icon: 'Active' },
    charging: { color: 'bg-amber-100 text-amber-700', icon: 'Charging' },
    error: { color: 'bg-red-100 text-red-700', icon: 'Error' },
    offline: { color: 'bg-gray-100 text-gray-700', icon: 'Offline' },
  }
  const cfg = statusConfig[robot.status] || statusConfig.offline

  const infoCards = [
    {
      label: 'Position (X, Y)',
      value: `(${robot.x.toFixed(2)}, ${robot.y.toFixed(2)})`,
      unit: 'm',
      icon: MapPin,
      color: 'text-blue-600',
      bg: 'bg-blue-50'
    },
    {
      label: 'Orientation',
      value: `${(robot.theta * 180 / Math.PI).toFixed(1)}`,
      unit: 'deg',
      icon: RotateCcw,
      color: 'text-purple-600',
      bg: 'bg-purple-50'
    },
    {
      label: 'Linear Velocity',
      value: robot.velocity ? robot.velocity.linear.toFixed(2) : '0.00',
      unit: 'm/s',
      icon: Gauge,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50'
    },
    {
      label: 'Angular Velocity',
      value: robot.velocity ? robot.velocity.angular.toFixed(2) : '0.00',
      unit: 'rad/s',
      icon: Activity,
      color: 'text-orange-600',
      bg: 'bg-orange-50'
    },
    {
      label: 'Stability Score',
      value: robot.stabilityScore ? (robot.stabilityScore * 100).toFixed(1) : '100.0',
      unit: '%',
      icon: Shield,
      color: 'text-teal-600',
      bg: 'bg-teal-50'
    },
    {
      label: 'Battery Level',
      value: `${Math.round(robot.battery)}`,
      unit: '%',
      icon: Battery,
      color: robot.battery > 50 ? 'text-emerald-600' : robot.battery > 20 ? 'text-amber-600' : 'text-red-600',
      bg: robot.battery > 50 ? 'bg-emerald-50' : robot.battery > 20 ? 'bg-amber-50' : 'bg-red-50'
    },
  ]

  const odometryCards = [
    {
      label: 'Left Encoder',
      value: robot.encoder ? robot.encoder.left.toFixed(0) : '0',
      icon: Crosshair,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50'
    },
    {
      label: 'Right Encoder',
      value: robot.encoder ? robot.encoder.right.toFixed(0) : '0',
      icon: Crosshair,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50'
    },
    {
      label: 'IMU Pitch',
      value: robot.imu ? robot.imu.pitch.toFixed(2) : '0.00',
      unit: 'rad',
      icon: Activity,
      color: 'text-cyan-600',
      bg: 'bg-cyan-50'
    },
    {
      label: 'IMU Roll',
      value: robot.imu ? robot.imu.roll.toFixed(2) : '0.00',
      unit: 'rad',
      icon: Activity,
      color: 'text-cyan-600',
      bg: 'bg-cyan-50'
    },
  ]

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6 max-w-6xl"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center gap-4">
        <Link
          to="/"
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-500" />
        </Link>
        <div>
          <h2 className="text-xl font-semibold text-slate-800">Robot Details</h2>
          <p className="text-sm text-gray-500">ID: {robot.id}</p>
        </div>
      </motion.div>

      {/* Robot Identity Card */}
      <motion.div
        variants={itemVariants}
        className="bg-white rounded-xl shadow-sm p-6"
      >
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
          <motion.div
            whileHover={{ scale: 1.05 }}
            className={`w-20 h-20 rounded-2xl flex items-center justify-center ${cfg.color.split(' ')[0]}`}
          >
            <Bot className={`w-10 h-10 ${cfg.color.split(' ')[1]}`} />
          </motion.div>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <h2 className="text-2xl font-bold text-slate-800">{robot.name}</h2>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${cfg.color}`}>
                {robot.status.toUpperCase()}
              </span>
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Radio className="w-3.5 h-3.5" />
                Last seen: {new Date(robot.lastSeen).toLocaleTimeString()}
              </span>
              <span className="flex items-center gap-1">
                <Zap className="w-3.5 h-3.5" />
                Battery: {Math.round(robot.battery)}%
              </span>
              {robot.currentTaskId && (
                <span className="flex items-center gap-1 text-blue-600">
                  <Play className="w-3.5 h-3.5" />
                  Task: {robot.currentTaskId}
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {robot.hasPayload && (
              <div className="flex items-center gap-2 bg-amber-50 text-amber-700 px-3 py-2 rounded-lg">
                <Weight className="w-4 h-4" />
                <span className="text-sm font-medium">
                  {robot.payloadWeightKg?.toFixed(1)}kg
                </span>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Telemetry Grid */}
      <motion.div variants={itemVariants}>
        <h3 className="text-lg font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <Gauge className="w-5 h-5 text-emerald-600" />
          Real-Time Telemetry
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {infoCards.map((card) => (
            <motion.div
              key={card.label}
              whileHover={{ y: -3 }}
              className="bg-white rounded-xl shadow-sm p-4 border border-gray-100"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-8 h-8 rounded-lg ${card.bg} flex items-center justify-center`}>
                  <card.icon className={`w-4 h-4 ${card.color}`} />
                </div>
                <span className="text-xs text-gray-500">{card.label}</span>
              </div>
              <p className="text-xl font-bold text-slate-800">
                {card.value}
                <span className="text-xs font-normal text-gray-400 ml-1">{card.unit}</span>
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Odometry Section */}
      <motion.div variants={itemVariants}>
        <h3 className="text-lg font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <Crosshair className="w-5 h-5 text-blue-600" />
          Odometry & IMU
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {odometryCards.map((card) => (
            <motion.div
              key={card.label}
              whileHover={{ y: -3 }}
              className="bg-white rounded-xl shadow-sm p-4 border border-gray-100"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-8 h-8 rounded-lg ${card.bg} flex items-center justify-center`}>
                  <card.icon className={`w-4 h-4 ${card.color}`} />
                </div>
                <span className="text-xs text-gray-500">{card.label}</span>
              </div>
              <p className="text-xl font-bold text-slate-800">
                {card.value}
                {card.unit && <span className="text-xs font-normal text-gray-400 ml-1">{card.unit}</span>}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Gripper & Payload Status */}
      <motion.div variants={itemVariants}>
        <h3 className="text-lg font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <GripHorizontal className="w-5 h-5 text-amber-600" />
          Gripper & Payload
        </h3>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl ${robot.gripperState === 'holding' ? 'bg-emerald-50' : 'bg-gray-50'} flex items-center justify-center`}>
                <GripHorizontal className={`w-6 h-6 ${robot.gripperState === 'holding' ? 'text-emerald-600' : 'text-gray-400'}`} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Gripper State</p>
                <p className="font-semibold text-slate-800 capitalize">{robot.gripperState || 'idle'}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl ${robot.hasPayload ? 'bg-amber-50' : 'bg-gray-50'} flex items-center justify-center`}>
                <Weight className={`w-6 h-6 ${robot.hasPayload ? 'text-amber-600' : 'text-gray-400'}`} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Payload</p>
                <p className="font-semibold text-slate-800">
                  {robot.hasPayload ? `${robot.payloadWeightKg?.toFixed(1)} kg` : 'None'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
                <Shield className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">SLAM Keyframes</p>
                <p className="font-semibold text-slate-800">{robot.slamKeyframes ?? 0}</p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Controls */}
      <motion.div variants={itemVariants}>
        <h3 className="text-lg font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <Zap className="w-5 h-5 text-red-600" />
          Robot Controls
        </h3>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex flex-wrap gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              <Home className="w-4 h-4" />
              Send to Charging
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
            >
              <Square className="w-4 h-4" />
              Emergency Stop
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 px-4 py-2.5 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors font-medium text-slate-700"
            >
              <RotateCcw className="w-4 h-4" />
              Reset Odometry
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 px-4 py-2.5 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors font-medium text-slate-700"
            >
              <Play className="w-4 h-4" />
              Resume Task
            </motion.button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default RobotDetails
