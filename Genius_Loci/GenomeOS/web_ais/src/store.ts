import { create } from 'zustand'

export interface Robot {
  id: string
  name: string
  status: 'free' | 'busy' | 'charging' | 'error' | 'offline'
  x: number
  y: number
  theta: number
  battery: number
  currentTaskId?: string
  lastSeen: string
  // Extended telemetry
  velocity?: { linear: number; angular: number }
  stabilityScore?: number
  gripperState?: string
  hasPayload?: boolean
  payloadWeightKg?: number
  imu?: { pitch: number; roll: number; yaw: number }
  encoder?: { left: number; right: number }
  slamKeyframes?: number
  pathWaypoints?: number
}

export interface Task {
  id: string
  taskId: string
  type: string
  status: string
  pickupX: number
  pickupY: number
  dropoffX: number
  dropoffY: number
  priority: number
  robotId?: string
  createdAt: string
}

export interface User {
  id: number
  username: string
  role: 'operator' | 'admin'
}

interface AppState {
  robots: Robot[]
  tasks: Task[]
  selectedRobotId: string | null
  wsConnected: boolean
  mapData: string | null
  // Auth
  user: User | null
  token: string | null
  isAuthenticated: boolean
  // Actions
  setRobots: (robots: Robot[]) => void
  updateRobot: (robot: Robot) => void
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  setSelectedRobot: (id: string | null) => void
  setWsConnected: (connected: boolean) => void
  setMapData: (data: string) => void
  // Auth actions
  login: (user: User, token: string) => void
  logout: () => void
}

export const useStore = create<AppState>((set) => ({
  robots: [],
  tasks: [],
  selectedRobotId: null,
  wsConnected: false,
  mapData: null,
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),

  setRobots: (robots) => set({ robots }),
  updateRobot: (robot) => set((state) => ({
    robots: state.robots.map(r => r.id === robot.id ? robot : r)
  })),
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
  setSelectedRobot: (id) => set({ selectedRobotId: id }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setMapData: (data) => set({ mapData: data }),

  login: (user, token) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ user, token, isAuthenticated: true })
  },
  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ user: null, token: null, isAuthenticated: false })
  }
}))
