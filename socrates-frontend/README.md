# Socrates AI - Frontend

React + TypeScript + Vite-based web interface for the Socrates AI collaborative development platform.

## Overview

The Socrates AI frontend provides a modern, responsive web application for:
- **Project Management** - Create, organize, and manage development projects
- **Real-Time Collaboration** - Live presence indicators, cursor tracking, and document synchronization
- **Code Analysis** - Interactive code visualization and complexity analysis
- **Knowledge Management** - Browse and manage project-specific knowledge base
- **Chat Interface** - Interactive conversations with AI agents for guidance and pair programming
- **Authentication** - Secure JWT-based authentication with multi-factor support

## Tech Stack

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite for fast development and optimized production builds
- **State Management**: React Context API with hooks
- **Styling**: Tailwind CSS for responsive design
- **HTTP Client**: Axios for API communication
- **Real-Time**: WebSocket support via Socket.IO for live collaboration
- **Type Safety**: Full TypeScript support with strict mode

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Socrates AI API server running (see [API Server Setup](../socrates-api/README.md))

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:5173
```

### Configuration

The frontend requires the API server to be running. Configure the API endpoint:

```bash
# Create .env.local file
cp .env.example .env.local

# Edit .env.local with your API server URL
VITE_API_URL=http://localhost:8000
```

### Available Scripts

```bash
# Development server with HMR
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build

# Preview production build locally
npm run preview

# Run linting
npm run lint

# Format code
npm run format
```

## Project Structure

```
socrates-frontend/
├── src/
│   ├── components/          # Reusable React components
│   │   ├── auth/           # Authentication components
│   │   ├── projects/       # Project management components
│   │   ├── chat/           # Chat interface components
│   │   ├── knowledge/      # Knowledge base components
│   │   └── common/         # Shared UI components
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.ts      # Authentication state
│   │   ├── useApi.ts       # API communication
│   │   └── useWebSocket.ts # Real-time updates
│   ├── stores/             # Context providers and state
│   │   ├── AuthStore.tsx   # User authentication state
│   │   ├── ProjectStore.tsx # Project management state
│   │   └── ChatStore.tsx   # Chat state management
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   ├── styles/             # Global styles
│   ├── App.tsx             # Main application component
│   └── main.tsx            # Application entry point
├── public/                 # Static assets
├── index.html              # HTML template
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript configuration
├── tailwind.config.js      # Tailwind CSS configuration
└── package.json            # Project dependencies
```

## Key Features

### Authentication Store

The `AuthStore` context manages user authentication state and session management:
- Login/logout functionality
- JWT token storage and refresh
- User profile information
- Multi-factor authentication support
- Session timeout handling

```tsx
// Usage in components
import { useAuth } from '../hooks/useAuth';

function MyComponent() {
  const { user, login, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated) return <LoginPage />;

  return <Dashboard user={user} onLogout={logout} />;
}
```

### API Client

The frontend communicates with the Socrates AI API server:
- Project CRUD operations
- Chat message handling
- Knowledge base searches
- Real-time collaboration updates
- Analytics and reporting

```tsx
// Example API calls
import { useApi } from '../hooks/useApi';

function ProjectList() {
  const { get, post, loading, error } = useApi();

  const projects = await get('/api/projects');
  const result = await post('/api/projects', { name: 'New Project' });
}
```

### Real-Time Collaboration

WebSocket connection for live collaboration features:
- Presence indicators showing active users
- Cursor position sharing for pair programming
- Document synchronization across sessions
- Real-time chat and notifications

## Environment Variables

Create a `.env.local` file for development:

```bash
# API Server Configuration
VITE_API_URL=http://localhost:8000

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_REALTIME=true

# Logging
VITE_LOG_LEVEL=debug
```

## Component Guide

### Authentication Components

- `LoginForm` - User login with email/password
- `RegisterForm` - New user registration
- `MFASetup` - Multi-factor authentication setup
- `ProtectedRoute` - Route guard for authenticated pages

### Project Components

- `ProjectList` - Browse all user projects
- `ProjectDetail` - Project settings and analytics
- `ProjectCreate` - Create new project with configuration
- `ProjectMembers` - Manage project collaborators

### Chat Components

- `ChatWindow` - Main chat interface
- `ConversationList` - Browse chat history
- `MessageInput` - Message composition and sending
- `AgentSelector` - Choose AI agent for assistance

### Knowledge Components

- `KnowledgeBase` - Browse project knowledge entries
- `KnowledgeSearch` - Search knowledge across projects
- `KnowledgeAdd` - Create new knowledge entries
- `KnowledgeImport` - Bulk import from JSON

## API Integration

The frontend integrates with these API endpoints:

- `GET /api/health` - Server health check
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/projects` - List user projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Project details
- `WS /ws/projects/{id}` - Real-time project updates

See [API Reference](../docs/API_REFERENCE.md) for complete endpoint documentation.

## Development

### Adding Components

```tsx
// Create component file
// src/components/MyComponent.tsx

import React from 'react';
import './MyComponent.css';

interface MyComponentProps {
  title: string;
  onAction?: () => void;
}

export const MyComponent: React.FC<MyComponentProps> = ({
  title,
  onAction
}) => {
  return (
    <div className="my-component">
      <h2>{title}</h2>
      {onAction && <button onClick={onAction}>Action</button>}
    </div>
  );
};
```

### Using Custom Hooks

```tsx
// Create hook file
// src/hooks/useMyHook.ts

import { useState, useEffect } from 'react';

export function useMyHook() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Setup logic
    return () => {
      // Cleanup logic
    };
  }, []);

  return { data };
}
```

## Testing

```bash
# Run tests (when configured)
npm run test

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

## Performance Optimization

- **Code Splitting**: Routes are code-split for faster initial load
- **Image Optimization**: Images are optimized and lazy-loaded
- **Caching**: HTTP responses are cached with appropriate headers
- **Bundle Analysis**: Use `npm run build -- --analyze` to analyze bundle size

## Browser Support

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

## Troubleshooting

### API Connection Issues

If you see "Failed to connect to API" errors:
1. Ensure the API server is running on the configured URL
2. Check `VITE_API_URL` environment variable
3. Verify CORS is properly configured on the API server
4. Check browser console for detailed error messages

### State Management Issues

If component state isn't updating:
1. Verify context providers are wrapping components
2. Check that hooks are called at component top level
3. Ensure state updates trigger re-renders with proper dependencies

### Build Issues

If the production build fails:
1. Run `npm run type-check` to verify TypeScript errors
2. Check that all assets are in the `public/` directory
3. Verify environment variables are set correctly
4. Try clearing `node_modules` and reinstalling dependencies

## Contributing

See [Developer Guide](../docs/DEVELOPER_GUIDE.md) for contribution guidelines.

## License

MIT - See LICENSE file for details
