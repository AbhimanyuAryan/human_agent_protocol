import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const clientId = useRef(null);
  const reconnectAttempts = useRef(0);

  // Generate unique client ID
  useEffect(() => {
    clientId.current = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // WebSocket connection management
  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = `ws://localhost:8000/ws/${clientId.current}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 Received:', data);
          
          handleIncomingMessage(data);
        } catch (err) {
          console.error('❌ Error parsing message:', err);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('🔌 WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        setIsTyping(false);
        
        // Attempt to reconnect unless it was a clean close
        if (event.code !== 1000 && reconnectAttempts.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
          console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1})`);
          
          setTimeout(() => {
            reconnectAttempts.current++;
            connectWebSocket();
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setError('Connection error. Please check if the server is running.');
      };

    } catch (err) {
      console.error('❌ Error creating WebSocket:', err);
      setError('Failed to connect to server. Please try again.');
    }
  };

  // Handle different types of incoming messages
  const handleIncomingMessage = (data) => {
    switch (data.type) {
      case 'message':
        // Standard message from assistant
        if (data.data && data.data.content) {
          setIsTyping(false);
          addMessage({
            id: data.data.id || Date.now().toString(),
            role: data.data.role || 'assistant',
            content: data.data.content,
            timestamp: data.data.timestamp || new Date().toISOString()
          });
        }
        break;

      case 'function_call':
        // Function call notification
        setIsTyping(false);
        addMessage({
          id: `func_${Date.now()}`,
          role: 'function_call',
          content: `🔧 Calling function: ${data.data.function}(${JSON.stringify(data.data.args, null, 2)})`,
          timestamp: data.data.timestamp || new Date().toISOString()
        });
        break;

      case 'input_request':
        // Agent is requesting input
        setIsTyping(false);
        if (data.data && data.data.prompt) {
          addMessage({
            id: `input_${Date.now()}`,
            role: 'assistant',
            content: data.data.prompt,
            timestamp: data.data.timestamp || new Date().toISOString()
          });
        }
        break;

      case 'status':
        // Status update (could be used for typing indicators, etc.)
        if (data.data && data.data.status === 'typing') {
          setIsTyping(true);
        } else {
          setIsTyping(false);
        }
        break;

      case 'error':
        // Error from server
        setIsTyping(false);
        setError(data.message || 'An error occurred');
        break;

      default:
        console.log('🤷 Unknown message type:', data.type);
    }
  };

  // Add message to the conversation
  const addMessage = (message) => {
    setMessages(prev => [...prev, {
      ...message,
      timestamp: message.timestamp || new Date().toISOString()
    }]);
  };

  // Send message to server
  const sendMessage = async () => {
    if (!inputMessage.trim() || !isConnected || isLoading) {
      return;
    }

    const userMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    };

    // Add user message to UI immediately
    addMessage(userMessage);
    
    // Clear input and show loading
    const messageToSend = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      // Send via WebSocket
      const payload = {
        type: 'user_message',
        content: messageToSend
      };

      wsRef.current.send(JSON.stringify(payload));
      console.log('📤 Sent:', payload);

    } catch (err) {
      console.error('❌ Error sending message:', err);
      setError('Failed to send message. Please try again.');
      setIsTyping(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  // Format timestamp for display
  const formatTime = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return '';
    }
  };

  // Connect on component mount
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting');
      }
    };
  }, []);

  return (
    <div className="app">
      {/* Header */}
      <div className="header">
        <h1>🌍 Simple Travel Assistant</h1>
        <div className="status">
          <div className={`status-indicator ${isConnected ? '' : 'disconnected'}`}></div>
          {isConnected ? 'Connected' : 'Disconnected'}
          {!isConnected && (
            <button 
              className="reconnect-button" 
              onClick={connectWebSocket}
            >
              Reconnect
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          ⚠️ {error}
          <button 
            onClick={() => setError(null)} 
            style={{ marginLeft: '10px', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Chat Container */}
      <div className="chat-container">
        {/* Messages */}
        <div className="messages">
          {messages.length === 0 && (
            <div className="message system">
              Welcome! I'm your AI travel assistant. I can help you plan trips, look up member information, and create personalized itineraries. 
              <br/><br/>
              Try starting with your member ID (e.g., P12345) or tell me about your travel plans!
            </div>
          )}
          
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div>{message.content}</div>
              <div className="message-time">
                {formatTime(message.timestamp)}
              </div>
            </div>
          ))}
          
          {/* Typing Indicator */}
          {isTyping && (
            <div className="typing-indicator">
              <div className="typing-dots">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="input-container">
          <form onSubmit={handleSubmit} className="input-form">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={isConnected ? "Type your message..." : "Connecting..."}
              disabled={!isConnected || isLoading}
              className="message-input"
            />
            <button 
              type="submit" 
              disabled={!isConnected || !inputMessage.trim() || isLoading}
              className="send-button"
            >
              {isLoading ? '...' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default App;
