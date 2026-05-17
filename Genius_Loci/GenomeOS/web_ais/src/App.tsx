import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { useStore } from './store'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import TaskManager from './pages/TaskManager'
import RobotDetails from './pages/RobotDetails'
import MapViewer from './pages/MapViewer'
import LogsViewer from './pages/LogsViewer'
import Settings from './pages/Settings'

const pageVariants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 }
}

const AnimatedPage: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <motion.div
    variants={pageVariants}
    initial="initial"
    animate="animate"
    exit="exit"
    transition={{ duration: 0.3, ease: 'easeInOut' }}
  >
    {children}
  </motion.div>
)

const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useStore(s => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }>
            <Route index element={<AnimatedPage><Dashboard /></AnimatedPage>} />
            <Route path="tasks" element={<AnimatedPage><TaskManager /></AnimatedPage>} />
            <Route path="robots/:robotId" element={<AnimatedPage><RobotDetails /></AnimatedPage>} />
            <Route path="map" element={<AnimatedPage><MapViewer /></AnimatedPage>} />
            <Route path="logs" element={<AnimatedPage><LogsViewer /></AnimatedPage>} />
            <Route path="settings" element={<AnimatedPage><Settings /></AnimatedPage>} />
          </Route>
        </Routes>
      </AnimatePresence>
    </BrowserRouter>
  )
}

export default App
