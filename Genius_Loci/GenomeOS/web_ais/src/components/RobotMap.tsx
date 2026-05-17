import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Robot } from '../store'

interface Props {
  robots: Robot[]
  fullSize?: boolean
}

const RobotMap: React.FC<Props> = ({ robots, fullSize }) => {
  const mapRef = useRef<L.Map | null>(null)
  const markersRef = useRef<Record<string, L.Marker>>({})
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const map = L.map(containerRef.current).setView([0, 0], 18)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 22
    }).addTo(map)

    // Add a warehouse floor plan overlay
    const bounds: L.LatLngBoundsExpression = [[-50, -50], [50, 50]]
    L.rectangle(bounds, { 
      color: '#94a3b8', 
      weight: 2, 
      fillColor: '#f1f5f9', 
      fillOpacity: 0.5 
    }).addTo(map)

    // Add grid lines
    for (let i = -50; i <= 50; i += 10) {
      L.polyline([[i, -50], [i, 50]], { color: '#cbd5e1', weight: 0.5 }).addTo(map)
      L.polyline([[-50, i], [50, i]], { color: '#cbd5e1', weight: 0.5 }).addTo(map)
    }

    // Add some warehouse features
    L.rectangle([[-20, -30], [-10, -20]], { color: '#64748b', fillColor: '#94a3b8' })
      .bindPopup('Storage Rack A').addTo(map)
    L.rectangle([[10, 10], [25, 25]], { color: '#64748b', fillColor: '#94a3b8' })
      .bindPopup('Storage Rack B').addTo(map)
    L.rectangle([[-30, 20], [-20, 35]], { color: '#f59e0b', fillColor: '#fbbf24' })
      .bindPopup('Loading Dock').addTo(map)

    map.fitBounds(bounds)
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Update robot markers
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    robots.forEach(robot => {
      const lat = robot.y
      const lng = robot.x

      const statusColor = 
        robot.status === 'free' ? '#10b981' :
        robot.status === 'busy' ? '#3b82f6' :
        robot.status === 'charging' ? '#f59e0b' :
        robot.status === 'error' ? '#ef4444' : '#9ca3af'

      if (markersRef.current[robot.id]) {
        markersRef.current[robot.id].setLatLng([lat, lng])
        markersRef.current[robot.id].setPopupContent(
          `<b>${robot.name}</b><br/>
           Status: ${robot.status}<br/>
           Battery: ${Math.round(robot.battery)}%<br/>
           Pos: (${robot.x.toFixed(1)}, ${robot.y.toFixed(1)})`
        )
      } else {
        const icon = L.divIcon({
          className: 'custom-robot-marker',
          html: `<div style="
            width: 20px; height: 20px; border-radius: 50%;
            background: ${statusColor}; border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            display: flex; align-items: center; justify-content: center;
            color: white; font-size: 10px; font-weight: bold;
          ">${robot.name.charAt(0)}</div>`,
          iconSize: [20, 20],
          iconAnchor: [10, 10]
        })

        const marker = L.marker([lat, lng], { icon })
          .bindPopup(`<b>${robot.name}</b><br/>Status: ${robot.status}<br/>Battery: ${Math.round(robot.battery)}%`)
          .addTo(map)

        markersRef.current[robot.id] = marker
      }
    })

    // Remove markers for disconnected robots
    Object.keys(markersRef.current).forEach(id => {
      if (!robots.find(r => r.id === id)) {
        markersRef.current[id].remove()
        delete markersRef.current[id]
      }
    })
  }, [robots])

  return (
    <div 
      ref={containerRef} 
      style={{ height: fullSize ? '100%' : '384px', width: '100%' }} 
    />
  )
}

export default RobotMap
