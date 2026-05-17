import React, { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { Bot, Map, ClipboardList, ScrollText, Settings, Menu, X, Wifi, WifiOff } from 'lucide-react'
import { useStore } from '../store'

const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const wsConnected = useStore(s => s.wsConnected)
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Bot },
    { path: '/tasks', label: 'Tasks', icon: ClipboardList },
    { path: '/map', label: 'Map', icon: Map },
    { path: '/logs', label: 'Logs', icon: ScrollText },
    { path: '/settings', label: 'Settings', icon: Settings },
  ]

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 text-white transform transition-transform lg:translate-x-0 lg:static ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <Bot className="w-8 h-8 text-emerald-400" />
            <div>
              <h1 className="text-lg font-bold">Genius Loci</h1>
              <p className="text-xs text-slate-400">Robot Control Center</p>
            </div>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="p-4 space-y-1">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                location.pathname === item.path 
                  ? 'bg-emerald-600 text-white' 
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700">
          <div className="flex items-center gap-2 text-sm">
            {wsConnected ? (
              <><Wifi className="w-4 h-4 text-emerald-400" /><span className="text-emerald-400">Connected</span></>
            ) : (
              <><WifiOff className="w-4 h-4 text-red-400" /><span className="text-red-400">Disconnected</span></>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b px-4 py-3 flex items-center gap-4">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden">
            <Menu className="w-6 h-6" />
          </button>
          <h2 className="text-lg font-semibold">
            {navItems.find(n => n.path === location.pathname)?.label || 'Dashboard'}
          </h2>
        </header>
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
