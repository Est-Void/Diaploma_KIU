import React, { useState } from 'react'
import { Plus, MapPin, Target, Trash2 } from 'lucide-react'
import { useStore } from '../store'

const TaskManager: React.FC = () => {
  const tasks = useStore(s => s.tasks)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    pickupX: 0, pickupY: 0,
    dropoffX: 10, dropoffY: 10,
    priority: 1, payloadDescription: '', payloadWeight: 0
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pickup_x: formData.pickupX,
          pickup_y: formData.pickupY,
          dropoff_x: formData.dropoffX,
          dropoff_y: formData.dropoffY,
          priority: formData.priority,
          payload_description: formData.payloadDescription,
          payload_weight_kg: formData.payloadWeight
        })
      })
      if (res.ok) {
        setShowForm(false)
      }
    } catch (err) {
      console.error('Failed to create task:', err)
    }
  }

  const statusColors: Record<string, string> = {
    pending: 'bg-amber-100 text-amber-800',
    assigned: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-emerald-100 text-emerald-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-gray-100 text-gray-800',
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Task Management</h2>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700">
          <Plus className="w-4 h-4" /> New Task
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold mb-4">Create Transport Task</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Pickup X</label>
              <input type="number" step="0.1" value={formData.pickupX}
                onChange={e => setFormData({...formData, pickupX: parseFloat(e.target.value)})}
                className="w-full border rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Pickup Y</label>
              <input type="number" step="0.1" value={formData.pickupY}
                onChange={e => setFormData({...formData, pickupY: parseFloat(e.target.value)})}
                className="w-full border rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Dropoff X</label>
              <input type="number" step="0.1" value={formData.dropoffX}
                onChange={e => setFormData({...formData, dropoffX: parseFloat(e.target.value)})}
                className="w-full border rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Dropoff Y</label>
              <input type="number" step="0.1" value={formData.dropoffY}
                onChange={e => setFormData({...formData, dropoffY: parseFloat(e.target.value)})}
                className="w-full border rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Priority</label>
              <select value={formData.priority}
                onChange={e => setFormData({...formData, priority: parseInt(e.target.value)})}
                className="w-full border rounded-lg px-3 py-2">
                <option value={1}>Normal</option>
                <option value={2}>High</option>
                <option value={3}>Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Payload Weight (kg)</label>
              <input type="number" value={formData.payloadWeight}
                onChange={e => setFormData({...formData, payloadWeight: parseFloat(e.target.value)})}
                className="w-full border rounded-lg px-3 py-2" />
            </div>
            <div className="col-span-2 flex justify-end gap-2">
              <button type="button" onClick={() => setShowForm(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">
                Create Task
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">Task ID</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Pickup</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Dropoff</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Priority</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Robot</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {tasks.map(task => (
              <tr key={task.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-mono">{task.taskId}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[task.status] || 'bg-gray-100'}`}>
                    {task.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">({task.pickupX}, {task.pickupY})</td>
                <td className="px-4 py-3 text-sm">({task.dropoffX}, {task.dropoffY})</td>
                <td className="px-4 py-3 text-sm">{task.priority}</td>
                <td className="px-4 py-3 text-sm">{task.robotId || '-'}</td>
              </tr>
            ))}
            {tasks.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No tasks yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default TaskManager
