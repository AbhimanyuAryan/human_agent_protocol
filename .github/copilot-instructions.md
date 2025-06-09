# AG-UI Travel Agent Project Instructions

## Project Structure Guidelines

**DO NOT MODIFY**: The `ag-ui-travel-agent` directory contains the backend travel agent implementation with AutoGen agents, FastAgency adapters, and server endpoints. This backend is complete and should not be changed.

**DO NOT MODIFY**: The `travel-frontend` directory contains a complex Next.js frontend with CopilotKit integration. This frontend is complete and should not be changed.

**MODIFY ONLY**: The `simple-travel-frontend` directory contains a simple React frontend that communicates directly with the backend via WebSocket. All frontend changes should be made only to this directory.

## Technical Stack

- **Backend**: Python with AutoGen agents, FastAgency, FastAPI, and WebSocket support
- **Simple Frontend**: Pure React 18 with vanilla CSS and WebSocket communication
- **Communication**: WebSocket protocol between simple frontend and backend on port 8000

## Code Style and Conventions

When working with the simple React frontend:
- Use functional components with React hooks
- Use vanilla CSS for styling (no CSS frameworks)
- Follow established naming conventions in existing components
- Use WebSocket for real-time communication with the backend
- Handle connection states and error conditions gracefully

## WebSocket Communication Protocol

The simple frontend uses WebSocket messages in this format:
```json
// Outgoing (to backend)
{"type": "user_message", "content": "message text"}

// Incoming (from backend)
{"type": "message", "data": {"role": "assistant", "content": "response"}}
```

## File Organization

- `simple-travel-frontend/src/App.js` - Main component with WebSocket logic
- `simple-travel-frontend/src/App.css` - Component styling
- `simple-travel-frontend/src/index.js` - React entry point
- `simple-travel-frontend/src/index.css` - Global styles

## Development Workflow

1. Backend runs on `http://localhost:8000` (do not modify)
2. Simple frontend runs on `http://localhost:3000` 
3. WebSocket connection to `ws://localhost:8000/ws/{clientId}`
4. Test with member IDs: P12345, P67890, S12345, S67890

When suggesting changes, always specify modifications only for the `simple-travel-frontend` directory and explain how changes integrate with the existing backend API.