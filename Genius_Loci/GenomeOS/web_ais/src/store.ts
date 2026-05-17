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

interface AppState {
  robots: Robot[]
  tasks: Task[]
  selectedRobotId: string | null
  wsConnected: boolean
  mapData: string | null
  setRobots: (robots: Robot[]) => void
  updateRobot: (robot: Robot) => void
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  setSelectedRobot: (id: string | null) => void
  setWsConnected: (connected: boolean) => void
  setMapData: (data: string) => void
}

export const useStore = create<AppState>((set) => ({
  robots: [],
  tasks: [],
  selectedRobotId: null,
  wsConnected: false,
  mapData: null,
  setRobots: (robots) => set({ robots }),
  updateRobot: (robot) => set((state) => ({
    robots: state.robots.map(r => r.id === robot.id ? robot : r)
  })),
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
  setSelectedRobot: (id) => set({ selectedRobotId: id }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setMapData: (data) => set({ mapData: data }),
}))
