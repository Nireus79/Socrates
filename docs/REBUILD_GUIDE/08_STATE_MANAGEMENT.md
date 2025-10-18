# STATE MANAGEMENT
## Redux Store Architecture and Patterns

---

## REDUX ARCHITECTURE

### Store Structure

```
Store {
  auth: {
    user: User | null
    token: string | null
    isAuthenticated: boolean
    loading: boolean
    error: string | null
  },
  projects: {
    items: Project[]
    currentProject: Project | null
    loading: boolean
    error: string | null
    filters: { status, phase, search }
    pagination: { page, limit, total }
  },
  sessions: {
    items: Session[]
    currentSession: Session | null
    messages: Message[]
    loading: boolean
    error: string | null
    wsConnected: boolean
  },
  instructions: {
    items: UserInstruction[]
    loading: boolean
    error: string | null
  },
  ui: {
    sidebarOpen: boolean
    theme: 'light' | 'dark'
    notification: Notification | null
  }
}
```

---

## SLICE IMPLEMENTATIONS

### Authentication Slice

```typescript
// src/redux/slices/authSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { User, ApiResponse } from '../../types';
import { apiClient } from '../../services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: localStorage.getItem('user')
    ? JSON.parse(localStorage.getItem('user')!)
    : null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  loading: false,
  error: null,
};

// Async thunks
export const initAuth = createAsyncThunk(
  'auth/initAuth',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<User>('/auth/me');
      return response.data;
    } catch (error) {
      return rejectWithValue('Auth initialization failed');
    }
  }
);

export const login = createAsyncThunk(
  'auth/login',
  async (
    { username, password }: { username: string; password: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await apiClient.post<{
        user: User;
        token: string;
      }>('/auth/login', { username, password });

      const { user, token } = response.data!;
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));

      return { user, token };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Login failed');
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (
    data: { username: string; email: string; password: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await apiClient.post<{
        user: User;
        token: string;
      }>('/auth/register', data);

      const { user, token } = response.data!;
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));

      return { user, token };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Registration failed');
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await apiClient.post('/auth/logout');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return null;
    } catch (error) {
      return rejectWithValue('Logout failed');
    }
  }
);

// Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Init Auth
      .addCase(initAuth.pending, (state) => {
        state.loading = true;
      })
      .addCase(initAuth.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(initAuth.rejected, (state) => {
        state.loading = false;
        state.isAuthenticated = false;
        localStorage.removeItem('token');
      })
      // Login
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = true;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      })
      // Register
      .addCase(register.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = true;
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
      });
  },
});

export const { clearError } = authSlice.actions;
export default authSlice.reducer;
```

### Projects Slice

```typescript
// src/redux/slices/projectSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { Project, CreateProjectRequest } from '../../types';
import { apiClient } from '../../services/api';

interface ProjectFilter {
  status?: string;
  phase?: string;
  search?: string;
}

interface ProjectState {
  items: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;
  filters: ProjectFilter;
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
}

const initialState: ProjectState = {
  items: [],
  currentProject: null,
  loading: false,
  error: null,
  filters: {},
  pagination: { page: 1, limit: 10, total: 0 },
};

// Async thunks
export const fetchProjects = createAsyncThunk(
  'projects/fetchProjects',
  async (
    { page = 1, limit = 10, filters = {} }: any,
    { rejectWithValue }
  ) => {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        ...filters,
      });

      const response = await apiClient.get<{
        items: Project[];
        total: number;
      }>(`/projects?${params}`);

      return response.data!;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch projects');
    }
  }
);

export const fetchProjectById = createAsyncThunk(
  'projects/fetchProjectById',
  async (projectId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<Project>(`/projects/${projectId}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch project');
    }
  }
);

export const createProject = createAsyncThunk(
  'projects/createProject',
  async (data: CreateProjectRequest, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<Project>('/projects', data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to create project');
    }
  }
);

export const updateProject = createAsyncThunk(
  'projects/updateProject',
  async (
    { id, data }: { id: string; data: Partial<Project> },
    { rejectWithValue }
  ) => {
    try {
      const response = await apiClient.put<Project>(`/projects/${id}`, data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update project');
    }
  }
);

export const deleteProject = createAsyncThunk(
  'projects/deleteProject',
  async (projectId: string, { rejectWithValue }) => {
    try {
      await apiClient.delete(`/projects/${projectId}`);
      return projectId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to delete project');
    }
  }
);

// Slice
const projectSlice = createSlice({
  name: 'projects',
  initialState,
  reducers: {
    setCurrentProject: (state, action) => {
      state.currentProject = action.payload;
    },
    setFilters: (state, action) => {
      state.filters = action.payload;
      state.pagination.page = 1; // Reset to first page
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Projects
      .addCase(fetchProjects.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProjects.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.pagination.total = action.payload.total;
      })
      .addCase(fetchProjects.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Fetch Project By ID
      .addCase(fetchProjectById.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProjectById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentProject = action.payload;
      })
      .addCase(fetchProjectById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Create Project
      .addCase(createProject.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
        state.pagination.total++;
      })
      // Update Project
      .addCase(updateProject.fulfilled, (state, action) => {
        const index = state.items.findIndex((p) => p.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        if (state.currentProject?.id === action.payload.id) {
          state.currentProject = action.payload;
        }
      })
      // Delete Project
      .addCase(deleteProject.fulfilled, (state, action) => {
        state.items = state.items.filter((p) => p.id !== action.payload);
        state.pagination.total--;
        if (state.currentProject?.id === action.payload) {
          state.currentProject = null;
        }
      });
  },
});

export const { setCurrentProject, setFilters, clearError } = projectSlice.actions;
export default projectSlice.reducer;
```

### Sessions Slice

```typescript
// src/redux/slices/sessionSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { Session, Message, CreateSessionRequest } from '../../types';
import { apiClient } from '../../services/api';

interface SessionState {
  items: Session[];
  currentSession: Session | null;
  messages: Message[];
  loading: boolean;
  wsConnected: boolean;
  error: string | null;
}

const initialState: SessionState = {
  items: [],
  currentSession: null,
  messages: [],
  loading: false,
  wsConnected: false,
  error: null,
};

// Async thunks
export const fetchSessions = createAsyncThunk(
  'sessions/fetchSessions',
  async (projectId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<Session[]>(`/projects/${projectId}/sessions`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue('Failed to fetch sessions');
    }
  }
);

export const createSession = createAsyncThunk(
  'sessions/createSession',
  async (data: CreateSessionRequest, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<Session>(
        `/projects/${data.projectId}/sessions`,
        data
      );
      return response.data;
    } catch (error: any) {
      return rejectWithValue('Failed to create session');
    }
  }
);

export const fetchMessages = createAsyncThunk(
  'sessions/fetchMessages',
  async (sessionId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<Message[]>(`/sessions/${sessionId}/messages`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue('Failed to fetch messages');
    }
  }
);

export const sendMessage = createAsyncThunk(
  'sessions/sendMessage',
  async (
    { sessionId, content }: { sessionId: string; content: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await apiClient.post<Message>(`/sessions/${sessionId}/message`, {
        content,
      });
      return response.data;
    } catch (error: any) {
      return rejectWithValue('Failed to send message');
    }
  }
);

// Slice
const sessionSlice = createSlice({
  name: 'sessions',
  initialState,
  reducers: {
    setCurrentSession: (state, action) => {
      state.currentSession = action.payload;
    },
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    setWsConnected: (state, action) => {
      state.wsConnected = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Sessions
      .addCase(fetchSessions.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchSessions.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchSessions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Create Session
      .addCase(createSession.fulfilled, (state, action) => {
        state.items.push(action.payload);
      })
      // Fetch Messages
      .addCase(fetchMessages.fulfilled, (state, action) => {
        state.messages = action.payload;
      })
      // Send Message
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.messages.push(action.payload);
      });
  },
});

export const { setCurrentSession, addMessage, setWsConnected, clearMessages, clearError } =
  sessionSlice.actions;
export default sessionSlice.reducer;
```

### Instructions Slice

```typescript
// src/redux/slices/instructionSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { UserInstruction, CreateInstructionRequest } from '../../types';
import { apiClient } from '../../services/api';

interface InstructionState {
  items: UserInstruction[];
  loading: boolean;
  error: string | null;
}

const initialState: InstructionState = {
  items: [],
  loading: false,
  error: null,
};

export const fetchInstructions = createAsyncThunk(
  'instructions/fetchInstructions',
  async (userId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<UserInstruction[]>(
        `/users/${userId}/instructions`
      );
      return response.data;
    } catch (error: any) {
      return rejectWithValue('Failed to fetch instructions');
    }
  }
);

export const createInstruction = createAsyncThunk(
  'instructions/createInstruction',
  async (data: CreateInstructionRequest, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<UserInstruction>('/instructions', data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue('Failed to create instruction');
    }
  }
);

export const updateInstruction = createAsyncThunk(
  'instructions/updateInstruction',
  async (
    { id, data }: { id: string; data: Partial<UserInstruction> },
    { rejectWithValue }
  ) => {
    try {
      const response = await apiClient.put<UserInstruction>(`/instructions/${id}`, data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue('Failed to update instruction');
    }
  }
);

export const deleteInstruction = createAsyncThunk(
  'instructions/deleteInstruction',
  async (id: string, { rejectWithValue }) => {
    try {
      await apiClient.delete(`/instructions/${id}`);
      return id;
    } catch (error: any) {
      return rejectWithValue('Failed to delete instruction');
    }
  }
);

const instructionSlice = createSlice({
  name: 'instructions',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInstructions.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchInstructions.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchInstructions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(createInstruction.fulfilled, (state, action) => {
        state.items.push(action.payload);
      })
      .addCase(updateInstruction.fulfilled, (state, action) => {
        const index = state.items.findIndex((i) => i.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(deleteInstruction.fulfilled, (state, action) => {
        state.items = state.items.filter((i) => i.id !== action.payload);
      });
  },
});

export const { clearError } = instructionSlice.actions;
export default instructionSlice.reducer;
```

### UI Slice

```typescript
// src/redux/slices/uiSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  notifications: Notification[];
  modalOpen: boolean;
  modalContent?: any;
}

const initialState: UIState = {
  sidebarOpen: true,
  theme: localStorage.getItem('theme') as 'light' | 'dark' || 'light',
  notifications: [],
  modalOpen: false,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
      localStorage.setItem('theme', action.payload);
    },
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id'>>) => {
      const id = Math.random().toString(36).substr(2, 9);
      state.notifications.push({
        id,
        ...action.payload,
        duration: action.payload.duration || 5000,
      });

      // Auto-remove after duration
      if (action.payload.duration) {
        setTimeout(() => {
          state.notifications = state.notifications.filter((n) => n.id !== id);
        }, action.payload.duration);
      }
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter((n) => n.id !== action.payload);
    },
    openModal: (state, action: PayloadAction<any>) => {
      state.modalOpen = true;
      state.modalContent = action.payload;
    },
    closeModal: (state) => {
      state.modalOpen = false;
      state.modalContent = undefined;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  setTheme,
  addNotification,
  removeNotification,
  openModal,
  closeModal,
} = uiSlice.actions;
export default uiSlice.reducer;
```

---

## CUSTOM HOOKS

### useAppDispatch and useAppSelector

```typescript
// src/redux/hooks.ts
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from './store';

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

### useAsync Hook (for loading states)

```typescript
// src/hooks/useAsync.ts
import { useEffect, useState } from 'react';

interface UseAsyncState<T> {
  status: 'idle' | 'pending' | 'success' | 'error';
  data?: T;
  error?: Error;
}

export function useAsync<T>(
  asyncFunction: () => Promise<T>,
  immediate = true
): UseAsyncState<T> {
  const [state, setState] = useState<UseAsyncState<T>>({
    status: 'idle',
  });

  useEffect(() => {
    if (!immediate) return;

    let isMounted = true;

    const executeAsync = async () => {
      setState({ status: 'pending' });
      try {
        const response = await asyncFunction();
        if (isMounted) {
          setState({ status: 'success', data: response });
        }
      } catch (error) {
        if (isMounted) {
          setState({ status: 'error', error: error as Error });
        }
      }
    };

    executeAsync();

    return () => {
      isMounted = false;
    };
  }, [asyncFunction, immediate]);

  return state;
}
```

---

## MIDDLEWARE

### Logger Middleware

```typescript
// src/redux/middleware/logger.ts
import { Middleware } from 'redux';

export const loggerMiddleware: Middleware = (store) => (next) => (action) => {
  console.group(action.type);
  console.info('dispatching', action);
  const result = next(action);
  console.log('next state', store.getState());
  console.groupEnd();
  return result;
};
```

---

## NEXT STEPS

1. Create all Redux slices
2. Configure store with dev tools
3. Create custom hooks for common patterns
4. Implement async thunks for all API calls
5. Add middleware for logging/error handling
6. Write tests for reducers

**Proceed to 10_API_INTEGRATION.md** for complete API endpoint specifications
