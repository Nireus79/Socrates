# FRONTEND STRUCTURE
## React Component Architecture with TypeScript

---

## FRONTEND ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        App.tsx (Root Component)                      │  │
│  │  - Route configuration                              │  │
│  │  - Global error boundary                            │  │
│  │  - Redux provider setup                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌────────────────┬──────────────────┬──────────────────┐  │
│  │  Pages/        │  Components/     │  Services/       │  │
│  │  ├─Dashboard   │  ├─Navigation    │  ├─api.ts        │  │
│  │  ├─Projects    │  ├─Forms         │  ├─auth.ts       │  │
│  │  ├─Sessions    │  ├─Panels        │  └─websocket.ts  │  │
│  │  ├─CodeEditor  │  ├─Modals        │                  │  │
│  │  └─Settings    │  └─Common        │  Redux/          │  │
│  │                │                  │  ├─store.ts      │  │
│  │                │                  │  └─slices/       │  │
│  │                │                  │                  │  │
│  └────────────────┴──────────────────┴──────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
        │ API Calls (Axios) │ WebSocket │ Redux Updates
        │
        ├─────────────────────────────────────────────────┐
        │                                                 │
   ┌────▼─────────────────────────────────────────────────────┐
   │          FASTAPI BACKEND (Running on :8000)              │
   │                                                          │
   │  Routes → Services → Agents → Database                  │
   └───────────────────────────────────────────────────────────┘
```

---

## PROJECT STRUCTURE

```
frontend/
├── src/
│   ├── index.tsx                 # Entry point
│   ├── App.tsx                   # Root component
│   │
│   ├── pages/                    # Page-level components
│   │   ├── Dashboard.tsx
│   │   ├── Projects.tsx
│   │   ├── Sessions.tsx
│   │   ├── CodeEditor.tsx
│   │   ├── Settings.tsx
│   │   └── Admin.tsx
│   │
│   ├── components/               # Reusable components
│   │   ├── navigation/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Navigation.tsx
│   │   │
│   │   ├── forms/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── ProjectForm.tsx
│   │   │   └── InstructionForm.tsx
│   │   │
│   │   ├── panels/
│   │   │   ├── InstructionsPanel.tsx
│   │   │   ├── MetricsPanel.tsx
│   │   │   └── ActivityPanel.tsx
│   │   │
│   │   ├── modals/
│   │   │   ├── ConfirmModal.tsx
│   │   │   ├── ErrorModal.tsx
│   │   │   └── CreateProjectModal.tsx
│   │   │
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Input.tsx
│   │       ├── Select.tsx
│   │       ├── Spinner.tsx
│   │       └── ErrorBoundary.tsx
│   │
│   ├── services/
│   │   ├── api.ts                # Axios instance with interceptors
│   │   ├── auth.ts               # Authentication service
│   │   ├── agents.ts             # Agent routing service
│   │   └── websocket.ts          # WebSocket management
│   │
│   ├── redux/
│   │   ├── store.ts              # Redux store configuration
│   │   ├── slices/
│   │   │   ├── authSlice.ts      # Authentication state
│   │   │   ├── projectSlice.ts   # Projects state
│   │   │   ├── sessionSlice.ts   # Sessions state
│   │   │   ├── instructionSlice.ts
│   │   │   ├── uiSlice.ts        # UI state
│   │   │   └── asyncThunks.ts    # Async actions
│   │   └── hooks.ts              # Redux hooks
│   │
│   ├── types/
│   │   ├── index.ts              # Type definitions
│   │   ├── api.ts                # API types
│   │   ├── models.ts             # Domain models
│   │   └── forms.ts              # Form types
│   │
│   ├── styles/
│   │   ├── globals.css           # Global styles
│   │   ├── tailwind.config.js    # Tailwind config
│   │   └── variables.css         # CSS variables
│   │
│   └── utils/
│       ├── formatting.ts         # Format utilities
│       ├── validation.ts         # Validation utilities
│       ├── constants.ts          # App constants
│       └── error-handler.ts      # Error handling
│
├── public/
│   └── index.html
│
├── package.json
├── tsconfig.json
├── .env
└── .gitignore
```

---

## CORE COMPONENTS

### Root Component: App.tsx

```typescript
// src/App.tsx
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from './redux/hooks';
import { initAuth } from './redux/slices/authSlice';

// Pages
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Sessions from './pages/Sessions';
import CodeEditor from './pages/CodeEditor';
import Settings from './pages/Settings';

// Components
import Header from './components/navigation/Header';
import Sidebar from './components/navigation/Sidebar';
import ErrorBoundary from './components/common/ErrorBoundary';

// Layout
const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="flex h-screen bg-gray-50">
    <Sidebar />
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header />
      <main className="flex-1 overflow-auto">
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  </div>
);

// App Component
const App: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isAuthenticated, loading } = useAppSelector(state => state.auth);

  useEffect(() => {
    dispatch(initAuth());
  }, [dispatch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spinner />
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <Router>
        {isAuthenticated ? (
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/sessions/:projectId" element={<Sessions />} />
              <Route path="/code-editor" element={<CodeEditor />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </Layout>
        ) : (
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        )}
      </Router>
    </ErrorBoundary>
  );
};

export default App;
```

### Type Definitions: types/index.ts

```typescript
// src/types/index.ts

// Models
export interface User {
  id: string;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  status: 'active' | 'inactive' | 'suspended';
  createdAt: string;
}

export interface Project {
  id: string;
  ownerId: string;
  name: string;
  description?: string;
  phase: 'planning' | 'design' | 'development' | 'testing' | 'deployment' | 'completed';
  status: 'active' | 'archived' | 'deleted';
  techStack?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Session {
  id: string;
  projectId: string;
  type: 'socratic' | 'chat' | 'code_review';
  status: 'active' | 'completed' | 'archived';
  title?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  sessionId: string;
  role: 'user' | 'agent';
  agentId?: string;
  content: string;
  metadata?: Record<string, any>;
  createdAt: string;
}

export interface UserInstruction {
  id: string;
  userId: string;
  projectId?: string;
  rules: string;
  parsedRules: Array<{ raw: string; type: string }>;
  categories: Record<string, string[]>;
  isActive: boolean;
  createdAt: string;
}

// API Requests
export interface CreateProjectRequest {
  name: string;
  description?: string;
  techStack?: string;
}

export interface CreateSessionRequest {
  projectId: string;
  type: 'socratic' | 'chat' | 'code_review';
  title?: string;
}

export interface SendMessageRequest {
  sessionId: string;
  content: string;
}

export interface CreateInstructionRequest {
  rules: string;
  projectId?: string;
}

// API Responses
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface ApiError {
  success: false;
  error: string;
  errorCode: string;
  message: string;
  timestamp: string;
}
```

### Redux Store: redux/store.ts

```typescript
// src/redux/store.ts
import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';

import authReducer from './slices/authSlice';
import projectReducer from './slices/projectSlice';
import sessionReducer from './slices/sessionSlice';
import instructionReducer from './slices/instructionSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    projects: projectReducer,
    sessions: sessionReducer,
    instructions: instructionReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore certain actions for non-serializable values
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

### Redux Slices: Example authSlice.ts

```typescript
// src/redux/slices/authSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { User, ApiResponse } from '../../types';
import { authService } from '../../services/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
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
      const response = await authService.getMe();
      return response.data;
    } catch (error) {
      return rejectWithValue('Failed to initialize auth');
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
      const response = await authService.login(username, password);
      localStorage.setItem('token', response.data.token);
      return response.data;
    } catch (error) {
      return rejectWithValue('Login failed');
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout();
      localStorage.removeItem('token');
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
      // Init auth
      .addCase(initAuth.pending, (state) => {
        state.loading = true;
      })
      .addCase(initAuth.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(initAuth.rejected, (state, action) => {
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

### API Service: services/api.ts

```typescript
// src/services/api.ts
import axios, { AxiosInstance, AxiosError } from 'axios';
import { ApiResponse, ApiError } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // Token expired, redirect to login
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string): Promise<ApiResponse<T>> {
    const response = await this.client.get<ApiResponse<T>>(url);
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.client.post<ApiResponse<T>>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.client.put<ApiResponse<T>>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<ApiResponse<T>> {
    const response = await this.client.delete<ApiResponse<T>>(url);
    return response.data;
  }
}

export const apiClient = new ApiClient();
```

---

## KEY COMPONENTS

### InstructionsPanel Component

```typescript
// src/components/panels/InstructionsPanel.tsx
import React, { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../redux/hooks';
import { createInstruction } from '../../redux/slices/instructionSlice';
import Button from '../common/Button';
import Spinner from '../common/Spinner';

interface InstructionsPanelProps {
  projectId?: string;
}

const InstructionsPanel: React.FC<InstructionsPanelProps> = ({ projectId }) => {
  const dispatch = useAppDispatch();
  const { instructions, loading } = useAppSelector((state) => state.instructions);
  const [rules, setRules] = useState('');
  const [showForm, setShowForm] = useState(false);

  const exampleRules = [
    '- Always include tests for new code',
    '- Prioritize security over performance',
    '- Require documentation for breaking changes',
    '- Maintain backward compatibility',
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rules.trim()) return;

    try {
      await dispatch(
        createInstruction({
          rules,
          projectId,
        })
      ).unwrap();

      setRules('');
      setShowForm(false);
    } catch (error) {
      console.error('Failed to create instruction:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-4">AI Instructions</h2>

      {/* Active Instructions */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Active Rules</h3>
        {loading ? (
          <Spinner />
        ) : instructions.length > 0 ? (
          <ul className="space-y-2">
            {instructions.map((inst) => (
              <li
                key={inst.id}
                className="bg-blue-50 p-3 rounded border-l-4 border-blue-500"
              >
                {inst.rules}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No instructions set</p>
        )}
      </div>

      {/* Examples */}
      <div className="mb-6 bg-gray-50 p-4 rounded">
        <h3 className="font-semibold mb-2">Example Rules</h3>
        <ul className="space-y-1 text-sm text-gray-600">
          {exampleRules.map((rule, idx) => (
            <li key={idx}>{rule}</li>
          ))}
        </ul>
      </div>

      {/* Add New Instruction */}
      {showForm ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={rules}
            onChange={(e) => setRules(e.target.value)}
            placeholder="Enter your rules (one per line, starting with -)"
            className="w-full h-32 p-3 border rounded focus:outline-none focus:border-blue-500"
            disabled={loading}
          />
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={loading || !rules.trim()}
              className="bg-blue-500 text-white"
            >
              {loading ? 'Saving...' : 'Save Rules'}
            </Button>
            <Button
              type="button"
              onClick={() => setShowForm(false)}
              className="bg-gray-300"
            >
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <Button
          onClick={() => setShowForm(true)}
          className="bg-blue-500 text-white w-full"
        >
          Add New Rule
        </Button>
      )}
    </div>
  );
};

export default InstructionsPanel;
```

### Sessions Component

```typescript
// src/pages/Sessions.tsx
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../redux/hooks';
import SessionList from '../components/sessions/SessionList';
import ChatInterface from '../components/sessions/ChatInterface';

const Sessions: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const dispatch = useAppDispatch();
  const { sessions, currentSession } = useAppSelector((state) => state.sessions);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  useEffect(() => {
    if (projectId) {
      dispatch(fetchSessions(projectId));
    }
  }, [projectId, dispatch]);

  return (
    <div className="grid grid-cols-4 gap-6 h-full">
      {/* Sessions List */}
      <div className="col-span-1 bg-white rounded-lg shadow overflow-y-auto">
        <SessionList
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          projectId={projectId}
        />
      </div>

      {/* Chat Interface */}
      <div className="col-span-3">
        {activeSessionId ? (
          <ChatInterface sessionId={activeSessionId} />
        ) : (
          <div className="bg-white rounded-lg shadow h-full flex items-center justify-center">
            <p className="text-gray-500">Select a session to start</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sessions;
```

---

## STYLING WITH TAILWIND CSS

### Configuration: tailwind.config.js

```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        secondary: '#1e40af',
        success: '#059669',
        warning: '#f59e0b',
        error: '#dc2626',
      },
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },
    },
  },
  plugins: [],
};
```

### Global Styles: styles/globals.css

```css
/* src/styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom components */
@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition;
  }

  .btn-secondary {
    @apply px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition;
  }

  .card {
    @apply bg-white rounded-lg shadow p-6;
  }

  .input-base {
    @apply w-full px-4 py-2 border rounded focus:outline-none focus:border-blue-500;
  }
}
```

---

## ENVIRONMENT CONFIGURATION

### .env

```
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=development
REACT_APP_LOG_LEVEL=info
```

---

## NEXT STEPS

1. Create all page components
2. Create all reusable components
3. Set up Redux slices and async thunks
4. Implement API services
5. Add WebSocket integration
6. Style with Tailwind CSS
7. Write component tests

**Proceed to 07_USER_INTERFACE.md** for detailed UI/UX design
