import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, MapPin, Target, Trash2, ClipboardList, CheckCircle2, Clock, Loader2 } from 'lucide-react'
import { useStore } from '../store'

const TaskManager: React.FC = () => {
  const tasks = useStore(s => s.tasks)
  const robots = useStore(s => s.robots)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    pickupX: '',
    pickupY: '',
    dropoffX: '',
    dropoffY: '',
    priority: '1',
    robotId: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'transport',
          status: 'pending',
          pickup_x: parseFloat(formData.pickupX),
          pickup_y: parseFloat(formData.pickupY),
          dropoff_x: parseFloat(formData.dropoffX),
          dropoff_y: parseFloat(formData.dropoffY),
          priority: parseInt(formData.priority),
          robot_id: formData.robotId || null
        })
      })

      setFormData({ pickupX: '', pickupY: '', dropoffX: '', dropoffY: '', priority: '1', robotId: '' })
      setShowForm(false)
    } catch (error) {
      console.error('Failed to create task:', error)
      // Create local task for demo
      useStore.setState(s => ({
        tasks: [{
          id: `task_${Date.now()}`,
          taskId: `TASK-${Math.floor(Math.random() * 9000 + 1000)}`,
          type: 'transport',
          status: 'pending',
          pickupX: parseFloat(formData.pickupX) || 0,
          pickupY: parseFloat(formData.pickupY) || 0,
          dropoffX: parseFloat(formData.dropoffX) || 0,
          dropoffY: parseFloat(formData.dropoffY) || 0,
          priority: parseInt(formData.priority) || 1,
          robotId: formData.robotId || undefined,
          createdAt: new Date().toISOString()
        }, ...s.tasks]
      }))
      setFormData({ pickupX: '', pickupY: '', dropoffX: '', dropoffY: '', priority: '1', robotId: '' })
      setShowForm(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-emerald-100 text-emerald-700'
      case 'in_progress': return 'bg-blue-100 text-blue-700'
      case 'pending': return 'bg-amber-100 text-amber-700'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-4 h-4" />
      case 'in_progress': return <Loader2 className="w-4 h-4 animate-spin" />
      case 'pending': return <Clock className="w-4 h-4" />
      default: return <Clock className="w-4 h-4" />
    }
  }

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
          <h2 className="text-lg font-semibold text-slate-800">Task Management</h2>
          <p className="text-sm text-gray-500">Create and monitor warehouse transport tasks</p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2.5 rounded-lg hover:bg-emerald-700 transition-colors font-medium"
        >
          <Plus className="w-4 h-4" />
          New Task
        </motion.button>
      </motion.div>

      {/* Create Form */}
      <AnimatePresence>
        {showForm && (
          <motion.form
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            onSubmit={handleSubmit}
            className="bg-white rounded-xl shadow-sm p-6 overflow-hidden"
          >
            <h3 className="text-sm font-semibold text-slate-800 mb-4">Create Transport Task</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Pickup X</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                  <input
                    type="number"
                    step="0.1"
                    value={formData.pickupX}
                    onChange={e => setFormData({ ...formData, pickupX: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg pl-8 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    placeholder="-30"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Pickup Y</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.pickupY}
                  onChange={e => setFormData({ ...formData, pickupY: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  placeholder="-30"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Dropoff X</label>
                <div className="relative">
                  <Target className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                  <input
                    type="number"
                    step="0.1"
                    value={formData.dropoffX}
                    onChange={e => setFormData({ ...formData, dropoffX: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg pl-8 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    placeholder="30"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Dropoff Y</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.dropoffY}
                  onChange={e => setFormData({ ...formData, dropoffY: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  placeholder="30"
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Priority (1-10)</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.priority}
                  onChange={e => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Assign Robot (optional)</label>
                <select
                  value={formData.robotId}
                  onChange={e => setFormData({ ...formData, robotId: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="">Auto-assign</option>
                  {robots.filter(r => r.status === 'free').map(r => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-3">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={isSubmitting}
                className="bg-emerald-600 text-white px-5 py-2 rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50"
              >
                {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Create Task
              </motion.button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="border border-gray-300 text-slate-600 px-5 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
              >
                Cancel
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Pending', value: tasks.filter(t => t.status === 'pending').length, color: 'text-amber-600', bg: 'bg-amber-50' },
          { label: 'In Progress', value: tasks.filter(t => t.status === 'in_progress').length, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: 'Completed', value: tasks.filter(t => t.status === 'completed').length, color: 'text-emerald-600', bg: 'bg-emerald-50' },
        ].map(stat => (
          <motion.div
            key={stat.label}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`${stat.bg} rounded-xl p-4 text-center`}
          >
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Task List */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-xl shadow-sm overflow-hidden"
      >
        <div className="p-4 border-b flex items-center gap-2">
          <ClipboardList className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-slate-800">Tasks</h3>
          <span className="ml-auto text-sm text-gray-500">{tasks.length} total</span>
        </div>

        <div className="divide-y">
          <AnimatePresence>
            {tasks.map((task, index) => (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ delay: index * 0.03 }}
                className="p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg ${getStatusStyle(task.status)} flex items-center justify-center`}>
                      {getStatusIcon(task.status)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-sm text-slate-800">{task.taskId}</p>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusStyle(task.status)}`}>
                          {task.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">
                        From ({task.pickupX}, {task.pickupY}) → To ({task.dropoffX}, {task.dropoffY})
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {task.robotId && (
                      <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded">
                        {task.robotId}
                      </span>
                    )}
                    <span className="text-xs text-gray-400">
                      Priority: {task.priority}
                    </span>
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                      title="Cancel task"
                    >
                      <Trash2 className="w-4 h-4" />
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {tasks.length === 0 && (
            <div className="p-12 text-center text-gray-400">
              <ClipboardList className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No tasks yet</p>
              <p className="text-xs mt-1">Click "New Task" to create one</p>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}

export default TaskManager
