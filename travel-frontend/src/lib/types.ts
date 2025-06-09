// Define types for messages and tools
type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

type ToolExecution = {
  id: string;
  name: string;
  timestamp: string;
  status: "completed" | "failed" | "in_progress";
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  args?: any;
};

// Define the travel agent state type
interface TravelAgentState {
  status: {
    phase:
      | "initialized"
      | "processing"
      | "processing_message"
      | "message_complete"
      | "awaiting_input"
      | "input_received"
      | "executing"
      | "tool_complete"
      | "completed"
      | "thread_completed"
      | "error";
    error: string | null;
    timestamp: string;
  };
  conversation: {
    stage: "starting" | "in_progress" | "completed";
    messages: Message[];
    tools: ToolExecution[];
    completed: boolean;
  };
  agent: {
    name: string;
    capabilities: string[];
    current_task: string | null;
  };
  ui: {
    showProgress: boolean;
    showInput: boolean;
    activeTab: "chat" | "itinerary" | "search";
    loading: boolean;
  };
}

export type { TravelAgentState, Message, ToolExecution };
