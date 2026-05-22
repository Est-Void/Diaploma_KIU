import React, { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Robot } from '../store'

interface Props {
  robots: Robot[]
  fullSize?: boolean
}

// Warehouse zone definitions
const WAREHOUSE_ZONES = {
  racks: [
    { name: 'Storage Rack A', bounds: [[-70, -80], [-50, -40]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack B', bounds: [[-70, -30], [-50, 10]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack C', bounds: [[-70, 20], [-50, 60]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack D', bounds: [[-70, 70], [-50, 90]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack E', bounds: [[-20, -80], [0, -40]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack F', bounds: [[-20, -30], [0, 10]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack G', bounds: [[-20, 20], [0, 60]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack H', bounds: [[-20, 70], [0, 90]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack I', bounds: [[30, -80], [50, -40]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack J', bounds: [[30, -30], [50, 10]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack K', bounds: [[30, 20], [50, 60]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack L', bounds: [[30, 70], [50, 90]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack M', bounds: [[60, -60], [80, -20]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack N', bounds: [[60, -10], [80, 30]] as L.LatLngBoundsExpression, color: '#64748b' },
    { name: 'Storage Rack O', bounds: [[60, 40], [80, 80]] as L.LatLngBoundsExpression, color: '#64748b' },
  ],
  docks: [
    { name: 'Loading Dock 1', bounds: [[-90, 85], [-75, 98]] as L.LatLngBoundsExpression, color: '#f59e0b' },
    { name: 'Loading Dock 2', bounds: [[75, 85], [90, 98]] as L.LatLngBoundsExpression, color: '#f59e0b' },
    { name: 'Loading Dock 3', bounds: [[-98, -60], [-75, -45]] as L.LatLngBoundsExpression, color: '#f59e0b' },
  ],
  charging: [
    { name: 'Charging Station', bounds: [[80, -98], [95, -80]] as L.LatLngBoundsExpression, color: '#10b981' },
  ],
  obstacles: [
    { name: 'Pillar 1', center: [-40, -40] as L.LatLngExpression, radius: 3 },
    { name: 'Pillar 2', center: [40, 40] as L.LatLngExpression, radius: 3 },
    { name: 'Pillar 3', center: [0, 0] as L.LatLngExpression, radius: 2.5 },
    { name: 'Pillar 4', center: [-40, 50] as L.LatLngExpression, radius: 2.5 },
    { name: 'Pillar 5', center: [50, -50] as L.LatLngExpression, radius: 3 },
  ]
}

const RobotMap: React.FC<Props> = ({ robots, fullSize }) => {
  const mapRef = useRef<L.Map | null>(null)
  const markersRef = useRef<Record<string, L.Marker>>({})
  const trailsRef = useRef<Record<string, L.Polyline>>({})
  const containerRef = useRef<HTMLDivElement>(null)
  const [trailPoints] = useState<Record<string, L.LatLng[]>>({})

  useEffect(() => {
    if (!containerRef.current) return

    const map = L.map(containerRef.current, {
      crs: L.CRS.Simple,
      minZoom: -3,
      maxZoom: 4,
      zoomControl: true,
      attributionControl: false
    })

    // Warehouse floor plan
    const warehouseBounds: L.LatLngBoundsExpression = [[-100, -100], [100, 100]]

    // Floor background
    L.rectangle(warehouseBounds, {
      color: '#334155',
      weight: 3,
      fillColor: '#f8fafc',
      fillOpacity: 1
    }).addTo(map)

    // Grid lines
    for (let i = -100; i <= 100; i += 10) {
      L.polyline([[i, -100], [i, 100]], { color: '#e2e8f0', weight: 0.5, dashArray: '4,4' }).addTo(map)
      L.polyline([[-100, i], [100, i]], { color: '#e2e8f0', weight: 0.5, dashArray: '4,4' }).addTo(map)
    }

    // Coordinate labels
    for (let i = -80; i <= 80; i += 20) {
      L.marker([i, -102], { icon: L.divIcon({
        className: 'coord-label',
        html: `<span style="font-size:10px;color:#94a3b8">${i}m</span>`,
        iconSize: [30, 12]
      })}).addTo(map)
      L.marker([-102, i], { icon: L.divIcon({
        className: 'coord-label',
        html: `<span style="font-size:10px;color:#94a3b8">${i}m</span>`,
        iconSize: [30, 12]
      })}).addTo(map)
    }

    // Storage racks
    WAREHOUSE_ZONES.racks.forEach(rack => {
      L.rectangle(rack.bounds, {
        color: rack.color,
        weight: 1.5,
        fillColor: rack.color,
        fillOpacity: 0.3
      }).bindPopup(`<b>${rack.name}</b><br/>Storage Zone`).addTo(map)
    })

    // Loading docks
    WAREHOUSE_ZONES.docks.forEach(dock => {
      L.rectangle(dock.bounds, {
        color: dock.color,
        weight: 2,
        fillColor: dock.color,
        fillOpacity: 0.25,
        dashArray: '6,3'
      }).bindPopup(`<b>${dock.name}</b><br/>Loading/Unloading`).addTo(map)
    })

    // Charging station
    WAREHOUSE_ZONES.charging.forEach(ch => {
      L.rectangle(ch.bounds, {
        color: ch.color,
        weight: 2,
        fillColor: ch.color,
        fillOpacity: 0.2,
        dashArray: '4,4'
      }).bindPopup(`<b>${ch.name}</b><br/>Robot Charging`).addTo(map)
    })

    // Pillars (obstacles)
    WAREHOUSE_ZONES.obstacles.forEach(obs => {
      L.circle(obs.center, {
        radius: obs.radius,
        color: '#ef4444',
        weight: 1,
        fillColor: '#ef4444',
        fillOpacity: 0.2
      }).bindPopup(`<b>${obs.name}</b><br/>Obstacle`).addTo(map)
    })

    // Aisle labels
    const aisles = [
      { pos: [-60, -60] as L.LatLngExpression, text: 'Aisle Alpha' },
      { pos: [-60, 15] as L.LatLngExpression, text: 'Aisle Beta' },
      { pos: [-60, 65] as L.LatLngExpression, text: 'Aisle Gamma' },
      { pos: [10, -60] as L.LatLngExpression, text: 'Aisle Delta' },
      { pos: [10, 15] as L.LatLngExpression, text: 'Aisle Epsilon' },
      { pos: [10, 65] as L.LatLngExpression, text: 'Aisle Zeta' },
      { pos: [65, -60] as L.LatLngExpression, text: 'Aisle Eta' },
      { pos: [65, 15] as L.LatLngExpression, text: 'Aisle Theta' },
    ]
    aisles.forEach(aisle => {
      L.marker(aisle.pos, {
        icon: L.divIcon({
          className: 'aisle-label',
          html: `<span style="font-size:11px;color:#64748b;font-weight:500;background:rgba(255,255,255,0.8);padding:2px 6px;border-radius:4px">${aisle.text}</span>`,
          iconSize: [100, 20]
        })
      }).addTo(map)
    })

    map.fitBounds(warehouseBounds)
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Update robot markers and trails
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

      // Update trail
      if (!trailPoints[robot.id]) {
        trailPoints[robot.id] = []
      }
      trailPoints[robot.id].push(L.latLng(lat, lng))
      if (trailPoints[robot.id].length > 50) {
        trailPoints[robot.id].shift()
      }

      if (trailsRef.current[robot.id]) {
        trailsRef.current[robot.id].setLatLngs(trailPoints[robot.id])
      } else if (trailPoints[robot.id].length > 1) {
        const trail = L.polyline(trailPoints[robot.id], {
          color: statusColor,
          weight: 2,
          opacity: 0.4,
          dashArray: '4,4'
        }).addTo(map)
        trailsRef.current[robot.id] = trail
      }

      // Update or create marker
      if (markersRef.current[robot.id]) {
        markersRef.current[robot.id].setLatLng([lat, lng])
        markersRef.current[robot.id].setPopupContent(
          `<div style="min-width:160px">
            <b style="font-size:14px">${robot.name}</b><br/>
            <span style="color:${statusColor};font-weight:600">● ${robot.status.toUpperCase()}</span><br/>
            <hr style="margin:4px 0;border-color:#e2e8f0"/>
            <span style="font-size:12px;color:#64748b">
              🔋 Battery: ${Math.round(robot.battery)}%<br/>
              📍 Pos: (${robot.x.toFixed(1)}, ${robot.y.toFixed(1)})<br/>
              🧭 Orient: ${(robot.theta * 180 / Math.PI).toFixed(0)}°<br/>
              ${robot.velocity ? `⚡ Speed: ${robot.velocity.linear.toFixed(2)} m/s<br/>` : ''}
              ${robot.stabilityScore ? `🛡️ Stability: ${(robot.stabilityScore * 100).toFixed(0)}%` : ''}
            </span>
          </div>`
        )

        // Update icon with rotation
        const iconEl = markersRef.current[robot.id].getElement()
        if (iconEl) {
          const el = iconEl.querySelector('.robot-marker-inner') as HTMLElement
          if (el) {
            el.style.background = statusColor
            el.style.transform = `rotate(${robot.theta}rad)`
          }
        }
      } else {
        const icon = L.divIcon({
          className: 'custom-robot-marker',
          html: `<div class="robot-marker-inner" style="
            width: 22px; height: 22px; border-radius: 50%;
            background: ${statusColor}; border: 2.5px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.35);
            display: flex; align-items: center; justify-content: center;
            color: white; font-size: 9px; font-weight: bold;
            position: relative;
          ">
            <span style="transform:rotate(0deg)">${robot.name.charAt(0)}</span>
            <div style="
              position: absolute; bottom: -4px; left: 50%;
              transform: translateX(-50%);
              width: 0; height: 0;
              border-left: 4px solid transparent;
              border-right: 4px solid transparent;
              border-top: 6px solid ${statusColor};
            "></div>
          </div>`,
          iconSize: [22, 28],
          iconAnchor: [11, 14]
        })

        const marker = L.marker([lat, lng], { icon })
          .bindPopup(
            `<div style="min-width:160px">
              <b style="font-size:14px">${robot.name}</b><br/>
              <span style="color:${statusColor};font-weight:600">● ${robot.status.toUpperCase()}</span><br/>
              <hr style="margin:4px 0;border-color:#e2e8f0"/>
              <span style="font-size:12px;color:#64748b">
                🔋 Battery: ${Math.round(robot.battery)}%<br/>
                📍 Pos: (${robot.x.toFixed(1)}, ${robot.y.toFixed(1)})<br/>
                🧭 Orient: ${(robot.theta * 180 / Math.PI).toFixed(0)}°
              </span>
            </div>`,
            { maxWidth: 220 }
          )
          .addTo(map)

        markersRef.current[robot.id] = marker
      }
    })

    // Remove markers for disconnected robots
    Object.keys(markersRef.current).forEach(id => {
      if (!robots.find(r => r.id === id)) {
        markersRef.current[id].remove()
        delete markersRef.current[id]
        if (trailsRef.current[id]) {
          trailsRef.current[id].remove()
          delete trailsRef.current[id]
        }
        delete trailPoints[id]
      }
    })
  }, [robots])

  return (
    <div
      ref={containerRef}
      className="w-full h-full"
      style={{ height: fullSize ? '100%' : '384px' }}
    />
  )
}

export default RobotMap
