/**
 * System Store - Zustand state management
 *
 * Manages Phase 5 system control endpoints:
 * - Get system help documentation
 * - Get system information
 * - Get system operational status
 * - Get system logs
 * - Get system context
 */

import { create } from 'zustand';
import { apiClient } from '../api/client';
import type { SuccessResponse } from '../api/types';

interface HelpSection {
  section: string;
  description: string;
  commands: string[];
}

interface Workflow {
  name: string;
  steps: string[];
}

interface HelpData {
  system_name: string;
  version: string;
  description: string;
  documentation_sections: HelpSection[];
  common_workflows: Workflow[];
  api_base_url: string;
  documentation_url: string;
  support_email: string;
}

interface SystemComponent {
  status: string;
  response_time_ms?: number;
  uptime_percentage?: number;
  [key: string]: unknown;
}

interface SystemMetrics {
  requests_per_second: number;
  average_response_time_ms: number;
  error_rate_percentage: number;
  successful_requests_today: number;
  failed_requests_today: number;
}

interface SystemStatusData {
  timestamp: string;
  overall_status: 'healthy' | 'degraded' | 'down';
  health_score: number;
  components: Record<string, SystemComponent>;
  metrics: SystemMetrics;
  alerts: string[];
  recommendations: string[];
  maintenance: {
    last_maintenance: string;
    next_maintenance_window: string;
    maintenance_mode: boolean;
  };
}

interface SystemInfo {
  system: {
    name: string;
    version: string;
    environment: string;
    status: string;
  };
  uptime: {
    started_at: string;
    uptime_seconds: number;
  };
  database: {
    status: string;
    type: string;
    location: string;
  };
  features: Record<string, string>;
  api_endpoints: {
    total: number;
    categories: number;
    coverage: string;
  };
  platform_statistics: {
    total_users: number;
    your_projects: number;
    active_sessions: number;
  };
  llm_integration: {
    provider: string;
    model: string;
    status: string;
  };
  system_capacity: Record<string, string>;
  documentation: Record<string, string>;
}

interface LogEntry {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  module: string;
  message: string;
  user?: string;
}

interface ContextData {
  user: {
    username: string;
    authenticated: boolean;
    subscription_tier: string;
  };
  current_timestamp: string;
  active_context: {
    mode: string;
    projects_count: number;
    last_activity: string;
  };
  system_configuration: {
    api_url: string;
    version: string;
    debug_mode: boolean;
    maintenance_mode: boolean;
  };
  feature_availability: Record<string, boolean>;
  rate_limits: Record<string, number>;
}

interface SystemState {
  // State
  help: HelpData | null;
  info: SystemInfo | null;
  status: SystemStatusData | null;
  logs: LogEntry[];
  context: ContextData | null;
  isLoading: boolean;
  isLoadingHelp: boolean;
  isLoadingStatus: boolean;
  isLoadingLogs: boolean;
  error: string | null;
  logFilter: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL' | null;

  // Actions
  getHelp: () => Promise<void>;
  getInfo: () => Promise<void>;
  getStatus: () => Promise<void>;
  getLogs: (limit?: number, logLevel?: string) => Promise<void>;
  getContext: () => Promise<void>;
  setLogFilter: (level: string | null) => Promise<void>;
  refreshAllSystemData: () => Promise<void>;
  clearError: () => void;
}

export const useSystemStore = create<SystemState>((set, get) => ({
  // Initial state
  help: null,
  info: null,
  status: null,
  logs: [],
  context: null,
  isLoading: false,
  isLoadingHelp: false,
  isLoadingStatus: false,
  isLoadingLogs: false,
  error: null,
  logFilter: null,

  // Get help documentation
  getHelp: async () => {
    set({ isLoadingHelp: true, error: null });
    try {
      const response = await apiClient.get<SuccessResponse>('/system/help');

      if (response.success && response.data) {
        set({
          help: response.data,
          isLoadingHelp: false,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get help';
      set({ error: message, isLoadingHelp: false });
      throw err;
    }
  },

  // Get system info
  getInfo: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get<SuccessResponse>('/system/info');

      if (response.success && response.data) {
        set({
          info: response.data,
          isLoading: false,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get system info';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  // Get system status
  getStatus: async () => {
    set({ isLoadingStatus: true, error: null });
    try {
      const response = await apiClient.get<SuccessResponse>('/system/status');

      if (response.success && response.data) {
        set({
          status: response.data,
          isLoadingStatus: false,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get system status';
      set({ error: message, isLoadingStatus: false });
      throw err;
    }
  },

  // Get system logs
  getLogs: async (limit = 100, logLevel = null) => {
    set({ isLoadingLogs: true, error: null });
    try {
      let url = '/system/logs';
      const params = new URLSearchParams();

      if (limit) params.append('limit', limit.toString());
      if (logLevel) params.append('log_level', logLevel);

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await apiClient.post<SuccessResponse>(url, {});

      if (response.success && response.data) {
        set({
          logs: response.data.logs || [],
          isLoadingLogs: false,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get logs';
      set({ error: message, isLoadingLogs: false });
      throw err;
    }
  },

  // Get system context
  getContext: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<SuccessResponse>('/system/context', {});

      if (response.success && response.data) {
        set({
          context: response.data,
          isLoading: false,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get system context';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  // Set log filter and refresh logs
  setLogFilter: async (level: string | null) => {
    set({ logFilter: level as any });

    // Refresh logs with filter
    await get().getLogs(100, level);
  },

  // Refresh all system data
  refreshAllSystemData: async () => {
    try {
      await Promise.all([
        get().getInfo(),
        get().getStatus(),
        get().getContext(),
        get().getLogs(),
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to refresh system data';
      set({ error: message });
      throw err;
    }
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },
}));
