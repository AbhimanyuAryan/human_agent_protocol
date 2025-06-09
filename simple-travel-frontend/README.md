# Simple Travel Frontend

A clean, simple React frontend for the Travel Assistant application built with plain React and CSS.

## Features

- **Pure React**: No complex dependencies, just React and CSS
- **WebSocket Communication**: Real-time messaging with the backend
- **Responsive Design**: Works on desktop and mobile
- **Connection Management**: Auto-reconnection and status indicators
- **Clean UI**: Modern, accessible interface

## Getting Started

### Prerequisites

- Node.js 16+
- Backend server running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start the development server
npm start
```

The application will open at `http://localhost:3000`.

### Usage

1. Ensure the backend travel agent server is running on port 8000
2. Open the frontend at `http://localhost:3000`
3. Start chatting with the AI travel assistant
4. Try member IDs like P12345, P67890, S12345, S67890 for demo data

## Project Structure

```
src/
├── App.js          # Main React component with WebSocket logic
├── App.css         # Component styling
├── index.js        # React entry point
└── index.css       # Global styles

public/
└── index.html      # HTML template
```

## Communication Protocol

The frontend communicates with the backend via WebSocket using simple JSON messages:

**Sending to Backend:**
```json
{
  "type": "user_message",
  "content": "Hello, I need help planning a trip"
}
```

**Receiving from Backend:**
```json
{
  "type": "message",
  "data": {
    "id": "msg_123",
    "role": "assistant", 
    "content": "I'd be happy to help you plan a trip!",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

## Customization

The application uses pure CSS for styling. Customize the appearance by editing `App.css` and `index.css`.

## Backend Integration

This frontend is designed to work with the AG-UI travel agent backend. Make sure the backend is running on `http://localhost:8000` before starting the frontend.
