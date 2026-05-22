import { useEffect, useRef } from 'react'
import { useStore } from '../store'

export default function useWebSocket() {
  const setWsConnected = useStore(s => s.setWsConnected)
  const updateRobot = useStore(s => s.updateRobot)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/client')

      ws.onopen = () => {
        console.log('[WS] Connected to server')
        setWsConnected(true)
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
                  ? {
                      ...r,
                      x: data.pose?.x ?? r.x,
                      y: data.pose?.y ?? r.y,
                      theta: data.pose?.theta ?? r.theta,
                      battery: data.battery_percent ?? r.battery,
                      status: data.status ?? r.status,
                      velocity: data.velocity ?? r.velocity,
                      stabilityScore: data.stability_score ?? r.stabilityScore,
                      gripperState: data.gripper_state ?? r.gripperState,
                      hasPayload: data.has_payload ?? r.hasPayload,
                      payloadWeightKg: data.payload_weight_kg ?? r.payloadWeightKg,
                      imu: data.imu ?? r.imu,
                      encoder: data.encoder ?? r.encoder,
                      slamKeyframes: data.slam_keyframes ?? r.slamKeyframes,
                      pathWaypoints: data.path_waypoints ?? r.pathWaypoints,
                      currentTaskId: data.task_id ?? r.currentTaskId,
                      lastSeen: new Date().toISOString()
                    }
                  : r
              )
            }))
          } else if (msg.type === 'robots_list') {
            useStore.setState({
              robots: (msg.robots || []).map((r: any) => ({
                id: r.id,
                name: r.name,
                status: r.status || 'offline',
                x: r.x || 0,
                y: r.y || 0,
                theta: r.theta || 0,
                battery: r.battery || 100,
                currentTaskId: r.currentTaskId,
                lastSeen: r.lastSeen || new Date().toISOString()
              }))
            })
          } else if (msg.type === 'tasks_list') {
            useStore.setState({
              tasks: (msg.tasks || []).map((t: any) => ({
                id: t.id,
                taskId: t.taskId,
                type: t.type || 'transport',
                status: t.status || 'pending',
                pickupX: t.pickupX || 0,
                pickupY: t.pickupY || 0,
                dropoffX: t.dropoffX || 0,
                dropoffY: t.dropoffY || 0,
                priority: t.priority || 1,
                robotId: t.robotId,
                createdAt: t.createdAt || new Date().toISOString()
              }))
            })
          } else if (msg.type === 'robot_connected') {
            console.log('[WS] Robot connected:', msg.robot_id)
          } else if (msg.type === 'robot_disconnected') {
            console.log('[WS] Robot disconnected:', msg.robot_id)
            useStore.setState(state => ({
              robots: state.robots.filter(r => r.id !== msg.robot_id)
            }))
          } else if (msg.type === 'task_assigned') {
            console.log('[WS] Task assigned:', msg.task_id)
          } else if (msg.type === 'telemetry_batch') {
            // Handle batch telemetry from simulation
            if (Array.isArray(msg.robots)) {
              msg.robots.forEach((robotData: any) => {
                const data = robotData.data
                const existing = useStore.getState().robots.find(r => r.id === robotData.robot_id)
                if (existing) {
                  updateRobot({
                    ...existing,
                    x: data.pose?.x ?? existing.x,
                    y: data.pose?.y ?? existing.y,
                    theta: data.pose?.theta ?? existing.theta,
                    battery: data.battery_percent ?? existing.battery,
                    status: data.status ?? existing.status,
                    velocity: data.velocity ?? existing.velocity,
                    stabilityScore: data.stability_score ?? existing.stabilityScore,
                    gripperState: data.gripper_state ?? existing.gripperState,
                    hasPayload: data.has_payload ?? existing.hasPayload,
                    payloadWeightKg: data.payload_weight_kg ?? existing.payloadWeightKg,
                    imu: data.imu ?? existing.imu,
                    encoder: data.encoder ?? existing.encoder,
                    slamKeyframes: data.slam_keyframes ?? existing.slamKeyframes,
                    pathWaypoints: data.path_waypoints ?? existing.pathWaypoints,
                    currentTaskId: data.task_id ?? existing.currentTaskId,
                    lastSeen: new Date().toISOString()
                  })
                } else {
                  // Add new robot
                  useStore.setState(state => ({
                    robots: [...state.robots, {
                      id: robotData.robot_id,
                      name: `Robot ${robotData.robot_id}`,
                      status: data.status || 'free',
                      x: data.pose?.x || 0,
                      y: data.pose?.y || 0,
                      theta: data.pose?.theta || 0,
                      battery: data.battery_percent || 100,
                      currentTaskId: data.task_id,
                      lastSeen: new Date().toISOString(),
                      velocity: data.velocity,
                      stabilityScore: data.stability_score,
                      gripperState: data.gripper_state,
                      hasPayload: data.has_payload,
                      payloadWeightKg: data.payload_weight_kg,
                      imu: data.imu,
                      encoder: data.encoder,
                      slamKeyframes: data.slam_keyframes,
                      pathWaypoints: data.path_waypoints
                    }]
                  }))
                }
              })
            }
          }
        } catch (e) {
          console.error('[WS] Message error:', e)
        }
      }

      ws.onclose = () => {
        console.log('[WS] Disconnected, reconnecting in 5s...')
        setWsConnected(false)
        wsRef.current = null
        setTimeout(connect, 5000)
      }

      ws.onerror = (err) => {
        console.error('[WS] Error:', err)
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
