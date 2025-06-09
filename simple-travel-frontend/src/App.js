import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const abortControllerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const threadId = useRef(null);
  const runId = useRef(null);

  // Generate unique thread and run IDs
  useEffect(() => {
    threadId.current = `thread_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Handle different types of incoming SSE events
  const handleIncomingEvent = useCallback((eventData) => {
    console.log('📨 Received event:', eventData);
    
    // Handle based on the event structure from the logs
    if (eventData.type === 'tool_call' && eventData.content) {
      // Tool call event from ToolCallEvent
      if (eventData.content.tool_calls) {
        eventData.content.tool_calls.forEach(toolCall => {
          if (toolCall.function) {
            addMessage({
              id: `tool_${toolCall.id}`,
              role: 'function_call',
              content: `🔧 Calling function: ${toolCall.function.name}\nArguments: ${toolCall.function.arguments}`,
              timestamp: new Date().toISOString()
            });
          }
        });
      }
      return;
    }

    if (eventData.type === 'input_request' && eventData.content) {
      // Input request event from InputRequestEvent  
      addMessage({
        id: `input_${Date.now()}`,
        role: 'assistant',
        content: eventData.content.prompt,
        timestamp: new Date().toISOString()
      });
      return;
    }

    if (eventData.type === 'text' && eventData.content) {
      // Text event from TextEvent
      addMessage({
        id: `text_${Date.now()}`,
        role: eventData.content.sender === 'travel_agent' ? 'assistant' : 'user',
        content: eventData.content.content,
        timestamp: new Date().toISOString()
      });
      return;
    }

    // Handle workflow started
    if (eventData.type === 'workflow_started') {
      console.log('🚀 Workflow started:', eventData);
      return;
    }

    // Handle using auto reply events  
    if (eventData.type === 'using_auto_reply') {
      console.log('🤖 Using auto reply:', eventData);
      return;
    }

    // Original event handlers for other types
    switch (eventData.type) {
      case 'TEXT_MESSAGE_START':
        setIsTyping(true);
        break;
        
      case 'TEXT_MESSAGE_CONTENT':
        setIsTyping(false);
        if (eventData.delta) {
          setMessages(prev => {
            const existingIndex = prev.findIndex(msg => msg.id === eventData.message_id);
            if (existingIndex >= 0) {
              const updated = [...prev];
              updated[existingIndex] = {
                ...updated[existingIndex],
                content: (updated[existingIndex].content || '') + eventData.delta
              };
              return updated;
            } else {
              return [...prev, {
                id: eventData.message_id,
                role: 'assistant',
                content: eventData.delta,
                timestamp: new Date().toISOString()
              }];
            }
          });
        }
        break;
        
      case 'TEXT_MESSAGE_END':
        setIsTyping(false);
        break;
        
      case 'RUN_STARTED':
        console.log('▶️ Run started');
        setIsLoading(true);
        break;
        
      case 'RUN_FINISHED':
        console.log('⏹️ Run finished');
        setIsLoading(false);
        setIsTyping(false);
        break;
        
      case 'STATE_SNAPSHOT':
      case 'STATE_DELTA':
        console.log('📊 State update:', eventData);
        break;
        
      default:
        console.log('🤷 Unknown event type:', eventData.type, eventData);
    }
  }, []);

  // Add message to the conversation
  const addMessage = (message) => {
    setMessages(prev => [...prev, {
      ...message,
      timestamp: message.timestamp || new Date().toISOString()
    }]);
  };

  // Send message using AG-UI protocol - corrected version
  const sendMessage = useCallback(async (messageContent) => {
    if (!messageContent.trim()) return;

    // Generate new run ID for each message
    runId.current = `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Add user message to UI immediately
    const userMessage = {
      id: `user_${Date.now()}`,
      role: 'user', 
      content: messageContent.trim(),
      timestamp: new Date().toISOString()
    };
    addMessage(userMessage);

    setIsLoading(true);
    setError(null);

    // Abort any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      // Prepare AG-UI payload - matching the exact format expected by the backend
      const payload = {
        thread_id: threadId.current,
        run_id: runId.current,
        messages: [
          {
            role: 'user',
            id: userMessage.id,
            content: messageContent.trim()
          }
        ],
        tools: [],
        context: [],
        state: {
          // Add required state field
          phase: "initialized",
          timestamp: new Date().toISOString()
        },
        forwardedProps: {
          // Add required forwardedProps field
          agent: "travel_agent"
        }
      };

      console.log('📤 Sending AG-UI request:', payload);

      // Send POST request with proper headers for CORS
      const response = await fetch('/fastagency/agui', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
        body: JSON.stringify(payload),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${response.statusText}\n${errorText}`);
      }

      console.log('✅ Connected to AG-UI stream');
      setIsConnected(true);

      // Read the SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      const readStream = async () => {
        try {
          let buffer = '';
          
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              console.log('📡 Stream ended');
              break;
            }

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            
            // Process complete lines
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
              const trimmedLine = line.trim();
              
              if (trimmedLine.startsWith('data: ')) {
                const dataContent = trimmedLine.slice(6);
                
                // Skip ping/heartbeat messages
                if (dataContent === '' || dataContent === '[DONE]') {
                  continue;
                }
                
                try {
                  const eventData = JSON.parse(dataContent);
                  handleIncomingEvent(eventData);
                } catch (parseError) {
                  console.error('❌ Error parsing SSE data:', parseError);
                  console.error('Raw data:', dataContent);
                }
              } else if (trimmedLine.startsWith('event:')) {
                // SSE event type line
                console.log('📋 SSE event:', trimmedLine);
              } else if (trimmedLine.startsWith('id:')) {
                // SSE id line
                console.log('📋 SSE id:', trimmedLine);
              } else if (trimmedLine.startsWith('retry:')) {
                // SSE retry line
                console.log('📋 SSE retry:', trimmedLine);
              } else if (trimmedLine === '') {
                // Empty line - separator between events
                continue;
              } else {
                // Unknown line format
                console.log('📋 Unknown SSE line:', trimmedLine);
              }
            }
          }
        } catch (streamError) {
          if (streamError.name === 'AbortError') {
            console.log('🛑 Stream aborted');
          } else {
            console.error('❌ Stream reading error:', streamError);
            setError('Stream connection lost. Please try again.');
          }
        } finally {
          setIsConnected(false);
          setIsLoading(false);
          setIsTyping(false);
          console.log('🔌 Stream connection closed');
        }
      };

      await readStream();

    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('🛑 Request aborted');
      } else {
        console.error('❌ Error sending message:', err);
        setError(`Failed to send message: ${err.message}`);
      }
      setIsLoading(false);
      setIsTyping(false);
      setIsConnected(false);
    }
  }, [handleIncomingEvent]);

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;
    
    const messageToSend = inputMessage.trim();
    setInputMessage('');
    sendMessage(messageToSend);
  };

  // Start initial conversation
  useEffect(() => {
    // Send initial message to start the conversation
    const timer = setTimeout(() => {
      sendMessage('Hello! I would like to plan a trip.');
    }, 1000);

    return () => clearTimeout(timer);
  }, [sendMessage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

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

  return (
    <div className="app">
      {/* Header */}
      <div className="header">
        <h1>🌍 Simple Travel Assistant</h1>
        <div className="status">
          <div className={`status-indicator ${isConnected ? '' : 'disconnected'}`}></div>
          {isConnected ? 'Connected' : 'Ready'}
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
              placeholder="Type your message..."
              disabled={isLoading}
              className="message-input"
            />
            <button 
              type="submit" 
              disabled={!inputMessage.trim() || isLoading}
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
