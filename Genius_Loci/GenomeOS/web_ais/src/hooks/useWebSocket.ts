import { useEffect, useRef } from 'react'
import { useStore } from '../store'

export default function useWebSocket() {
  const setRobots = useStore(s => s.setRobots)
  const setWsConnected = useStore(s => s.setWsConnected)
  const setTasks = useStore(s => s.setTasks)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/client')

      ws.onopen = () => {
        console.log('WebSocket connected')
        setWsConnected(true)

        // Request initial data
        ws.send(JSON.stringify({ type: 'get_robots' }))
        ws.send(JSON.stringify({ type: 'get_tasks' }))
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)

          if (msg.type === 'telemetry') {
            const data = msg.data
            useStore.setState(state => ({
              robots: state.robots.map(r => 
                r.id === msg.robot_id 
                  ? { ...r, x: data.pose?.x ?? r.x, y: data.pose?.y ?? r.y,
                      theta: data.pose?.theta ?? r.theta, 
                      battery: data.battery_percent ?? r.battery,
                      status: data.status ?? r.status }
                  : r
              )
            }))
          } else if (msg.type === 'robot_connected') {
            // Fetch updated robot list
          } else if (msg.type === 'task_assigned') {
            // Refresh tasks
          }
        } catch (e) {
          console.error('WS message error:', e)
        }
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setWsConnected(false)
        wsRef.current = null
        // Reconnect after 5s
        setTimeout(connect, 5000)
      }

      ws.onerror = (err) => {
        console.error('WebSocket error:', err)
        ws.close()
      }

      wsRef.current = ws
    }

    connect()

    return () => {
      wsRef.current?.close()
    }
  }, [])
}
