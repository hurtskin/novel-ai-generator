import { create } from 'zustand';
import type { LogEntry, NodeMetric, ChapterMetric, TotalMetric, ProgressData, ChatMessage, MemoryFragment, AppConfig } from '../api/client';

interface AppState {
  connectionStatus: 'disconnected' | 'connecting' | 'connected';
  logs: LogEntry[];
  nodeMetrics: NodeMetric[];
  chapterMetrics: ChapterMetric[];
  totalMetrics: TotalMetric | null;
  progress: ProgressData;
  chatMessages: ChatMessage[];
  memories: MemoryFragment[];
  config: AppConfig | null;
  currentRole: string;
  selectedPanel: 'debug' | 'performance' | 'chat' | 'settings' | 'progress' | 'intervention';
  error: string | null;
  interventionData: {
    needIntervention: boolean;
    versions: string[];
    nodeId: string;
    chapterId: number;
  } | null;

  setConnectionStatus: (status: 'disconnected' | 'connecting' | 'connected') => void;
  addLog: (log: LogEntry) => void;
  clearLogs: () => void;
  addNodeMetric: (metric: NodeMetric) => void;
  addChapterMetric: (metric: ChapterMetric) => void;
  setTotalMetrics: (metrics: TotalMetric) => void;
  setProgress: (progress: Partial<ProgressData>) => void;
  addChatMessage: (message: ChatMessage) => void;
  updateChatMessage: (id: string, content: string) => void;
  clearChatMessages: () => void;
  setMemories: (memories: MemoryFragment[]) => void;
  setConfig: (config: AppConfig) => void;
  setCurrentRole: (role: string) => void;
  setSelectedPanel: (panel: 'debug' | 'performance' | 'chat' | 'settings' | 'progress' | 'intervention') => void;
  setError: (error: string | null) => void;
  setInterventionData: (data: { needIntervention: boolean; versions: string[]; nodeId: string; chapterId: number } | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  connectionStatus: 'disconnected',
  logs: [],
  nodeMetrics: [],
  chapterMetrics: [],
  totalMetrics: null,
  progress: {
    current_chapter: 0,
    total_chapters: 0,
    current_node: '',
    total_nodes: 0,
    status: 'idle',
    is_paused: false,
  },
  chatMessages: [],
  memories: [],
  config: null,
  currentRole: 'all',
  selectedPanel: 'progress',
  error: null,
  interventionData: null,

  setConnectionStatus: (status) => set({ connectionStatus: status }),
  
  addLog: (log) => set((state) => ({ 
    logs: [...state.logs.slice(-999), log] 
  })),
  
  clearLogs: () => set({ logs: [] }),
  
  addNodeMetric: (metric) => set((state) => ({
    nodeMetrics: [...state.nodeMetrics, metric]
  })),
  
  addChapterMetric: (metric) => set((state) => ({
    chapterMetrics: [...state.chapterMetrics, metric]
  })),
  
  setTotalMetrics: (metrics) => set({ totalMetrics: metrics }),
  
  setProgress: (progress) => set((state) => ({
    progress: { ...state.progress, ...progress }
  })),
  
  addChatMessage: (message) => set((state) => ({
    chatMessages: [...state.chatMessages, message]
  })),
  
  updateChatMessage: (id, content) => set((state) => ({
    chatMessages: state.chatMessages.map((msg) =>
      msg.id === id ? { ...msg, content } : msg
    )
  })),
  
  clearChatMessages: () => set({ chatMessages: [] }),
  
  setMemories: (memories) => set({ memories }),
  
  setConfig: (config) => set({ config }),
  
  setCurrentRole: (role) => set({ currentRole: role }),
  
  setSelectedPanel: (panel) => set({ selectedPanel: panel }),
  
  setError: (error) => set({ error }),
  
  setInterventionData: (data) => set({ interventionData: data }),
}));
