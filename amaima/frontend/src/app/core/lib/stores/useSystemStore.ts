import { create } from 'zustand';
import { SystemStatusData, ModelStatus } from '../../types';

interface SystemStore {
  systemStatus: SystemStatusData | null;
  isConnected: boolean;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  lastUpdate: string | null;
  
  setSystemStatus: (status: SystemStatusData) => void;
  updateModelStatus: (modelStatus: ModelStatus) => void;
  setConnected: (connected: boolean) => void;
  setConnectionQuality: (quality: 'excellent' | 'good' | 'poor' | 'disconnected') => void;
  updateMetrics: (metrics: Partial<SystemStatusData>) => void;
}

export const useSystemStore = create<SystemStore>((set) => ({
  systemStatus: null,
  isConnected: false,
  connectionQuality: 'disconnected',
  lastUpdate: null,

  setSystemStatus: (status: SystemStatusData) => {
    set({
      systemStatus: status,
      lastUpdate: new Date().toISOString(),
    });
  },

  updateModelStatus: (modelStatus: ModelStatus) => {
    set((state) => {
      if (!state.systemStatus) return state;
      
      const modelIndex = state.systemStatus.modelStatus.findIndex(
        (m) => m.modelId === modelStatus.modelId
      );
      
      const newModels = [...state.systemStatus.modelStatus];
      if (modelIndex >= 0) {
        newModels[modelIndex] = modelStatus;
      } else {
        newModels.push(modelStatus);
      }
      
      return {
        systemStatus: {
          ...state.systemStatus,
          modelStatus: newModels,
        },
      };
    });
  },

  setConnected: (connected: boolean) => {
    set({ isConnected: connected });
  },

  setConnectionQuality: (quality: 'excellent' | 'good' | 'poor' | 'disconnected') => {
    set({ connectionQuality: quality });
  },

  updateMetrics: (metrics: Partial<SystemStatusData>) => {
    set((state) => {
      if (!state.systemStatus) return state;
      
      return {
        systemStatus: {
          ...state.systemStatus,
          ...metrics,
        },
        lastUpdate: new Date().toISOString(),
      };
    });
  },
}));
