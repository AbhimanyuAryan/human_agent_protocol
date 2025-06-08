import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [awaitingInput, setAwaitingInput] = useState(false);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const clientId = useRef(Math.random().toString(36).substring(7));

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${clientId.current}`);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('Connected to server');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'message':
          setMessages(prev => [...prev, data.data]);
          setIsLoading(false);
          break;
          
        case 'function_call':
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'system',
            content: `🔧 Calling function: ${data.data.function}`,
            timestamp: data.data.timestamp
          }]);
          break;
          
        case 'input_request':
          setAwaitingInput(true);
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.data.prompt,
            timestamp: data.data.timestamp
          }]);
          break;
          
        default:
          console.log('Unknown message type:', data.type);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('Disconnected from server');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    wsRef.current = ws;
  };

  const sendMessage = () => {
    if (!inputValue.trim() || !isConnected) return;

    const message = {
      type: 'user_message',
      content: inputValue
    };

    // Add user message to UI immediately
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    }]);

    wsRef.current.send(JSON.stringify(message));
    setInputValue('');
    setIsLoading(true);
    setAwaitingInput(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'user': return '#007bff';
      case 'assistant': return '#28a745';
      case 'system': return '#6c757d';
      default: return '#333';
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'user': return '👤';
      case 'assistant': return '🤖';
      case 'system': return '⚙️';
      default: return '💬';
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🧳 Simple Travel Agent</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>

      <main className="chat-container">
        <div className="messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div className="message-header">
                <span className="role-icon">{getRoleIcon(message.role)}</span>
                <span className="role" style={{ color: getRoleColor(message.role) }}>
                  {message.role.charAt(0).toUpperCase() + message.role.slice(1)}
                </span>
                <span className="timestamp">{formatTimestamp(message.timestamp)}</span>
              </div>
              <div className="message-content">
                {message.content.split('\n').map((line, index) => (
                  <div key={index}>{line || '\u00A0'}</div>
                ))}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message assistant">
              <div className="message-header">
                <span className="role-icon">🤖</span>
                <span className="role" style={{ color: '#28a745' }}>Assistant</span>
                <span className="timestamp">now</span>
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          {awaitingInput && (
            <div className="input-hint">
              💡 The agent is waiting for your response. Type "continue" to proceed or provide your input.
            </div>
          )}
          <div className="input-group">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={awaitingInput ? "Type your response or 'continue'..." : "Type your message..."}
              disabled={!isConnected}
              rows="3"
              className="message-input"
            />
            <button 
              onClick={sendMessage} 
              disabled={!isConnected || !inputValue.trim()}
              className="send-button"
            >
              Send
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
