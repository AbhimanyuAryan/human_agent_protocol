import Chat from "./Chat";
import {
  useCopilotChat,
  useCoAgent,
  useCoAgentStateRender,
  useCopilotAction,
} from "@copilotkit/react-core";
import { useRef } from "react";
import { TravelAgentState } from "@/lib/types";

function Travel() {
  const { visibleMessages } = useCopilotChat();
  const isTravelInProgress = useRef(false);

  // Connect to the travel agent's state using CopilotKit's useCoAgent hook
  const { state, stop: stopTravelAgent } = useCoAgent<TravelAgentState>({
    name: "travelAgent",
    initialState: {
      status: {
        phase: "initialized",
        error: null,
        timestamp: new Date().toISOString(),
      },
      conversation: {
        stage: "starting",
        messages: [
          {
            id: "placeholder",
            role: "assistant",
            content: "",
            timestamp: new Date().toISOString(),
          },
        ],
        tools: [],
        completed: false,
      },
      agent: {
        name: "Travel Assistant",
        capabilities: ["search", "recommend", "book"],
        current_task: null,
      },
      ui: {
        showProgress: false,
        showInput: false,
        activeTab: "chat",
        loading: false,
      },
    },
  });
  // Implement useCopilotAction for looking up a member
  useCopilotAction({
    name: "lookup_member",
    description:
      "Look up a travel club member from the database by name, email, or ID",
    parameters: [
      {
        name: "message",
        type: "string",
        description:
          "A message to display to the user when showing member search results",
        required: true,
      },
    ],
    renderAndWaitForResponse: ({ args, respond }) => {
      console.log("lookup_member action called with args:", args);

      const message =
        args?.message ||
        "I am about to check your travel membership. Reply with 'continue' to proceed or 'exit' to end the conversation.";

      if (!respond) {
        return (
          <div className="member-lookup mt-6 pt-4 border-t border-b border-gray-200">
            <div className="mb-3">
              {" "}
              <div className="flex items-center gap-2 mb-2">
                <span className="text-blue-500 text-xl">👤</span>
                <span className="font-medium text-blue-600">
                  Travel Assistant
                </span>
              </div>
              <h3 className="text-lg font-medium mb-2">{message}</h3>
            </div>{" "}
          </div>
        );
      }

      return (
        <div className="member-lookup mt-6 pt-4 border-t border-gray-200">
          <div className="mb-3">
            {" "}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-blue-500 text-xl">👤</span>
              <span className="font-medium text-blue-600">
                Travel Assistant
              </span>
            </div>
            <h3 className="text-lg font-medium mb-2">{message}</h3>
          </div>{" "}
          <div className="flex gap-3">
            <button
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors cursor-pointer"
              onClick={() => {
                respond("continue");
              }}>
              Continue
            </button>
            <button
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors cursor-pointer"
              onClick={() => {
                respond("exit");
              }}>
              Exit
            </button>
          </div>
        </div>
      );
    },
  });
  // Add useCopilotAction for creating a travel itinerary
  useCopilotAction({
    name: "create_itinerary",
    description:
      "Create a new travel itinerary with details like destination, dates, and activities",
    parameters: [
      {
        name: "message",
        type: "string",
        description: "A message to display when asking for confirmation",
        required: true,
      },
    ],
    renderAndWaitForResponse: ({ args, respond }) => {
      console.log("create_itinerary action called with args:", args);

      const message =
        args?.message ||
        "I am about to create your travel itinerary. Reply with 'continue' to proceed or 'exit' to end the conversation.";

      if (!respond) {
        return (
          <div className="itinerary-creation mt-6 pt-4 border-t border-b border-gray-200">
            <div className="mb-4">
              {" "}
              <div className="flex items-center gap-2 mb-2">
                <span className="text-blue-500 text-xl">👤</span>
                <span className="font-medium text-blue-600">
                  Travel Assistant
                </span>
              </div>
              <h3 className="text-lg font-medium mb-3">{message}</h3>
            </div>{" "}
          </div>
        );
      }

      return (
        <div className="itinerary-creation mt-6 pt-4 border-t border-gray-200">
          <div className="mb-4">
            {" "}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-blue-500 text-xl">📋</span>
              <span className="font-medium text-blue-600">
                Travel Assistant
              </span>
            </div>
            <h3 className="text-lg font-medium mb-3">{message}</h3>
          </div>{" "}
          <div className="flex gap-3">
            <button
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
              onClick={() => {
                respond("continue");
              }}>
              Continue
            </button>
            <button
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
              onClick={() => {
                respond("exit");
              }}>
              Exit
            </button>
          </div>
        </div>
      );
    },
  });

  // Helper function for type-safe phase comparison
  // const isPhase = (
  //   phase: string | undefined,
  //   comparePhase: TravelAgentState["status"]["phase"]
  // ): boolean => {
  //   return phase === comparePhase;
  // };

  // Implement useCoAgentStateRender hook
  useCoAgentStateRender({
    name: "travelAgent",
    handler: ({ nodeName }) => {
      // Stop the travel agent when the "__end__" node is reached
      if (nodeName === "__end__") {
        setTimeout(() => {
          isTravelInProgress.current = false;
          stopTravelAgent();
        }, 1000);
      }
    },
    render: ({ status }) => {
      if (status === "inProgress") {
        isTravelInProgress.current = true;
        return (
          <div className="travel-in-progress bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center gap-2 mb-3">
              <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent"></div>
              <p className="font-medium text-gray-800">{getStatusText()}</p>
            </div>

            {state?.ui?.showProgress && (
              <div className="status-container mb-3">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="text-sm font-medium text-gray-700">
                    {state.agent.current_task || "Processing your request..."}
                  </div>
                </div>
              </div>
            )}

            {state?.conversation?.tools?.length > 0 && (
              <div className="text-xs text-gray-500 flex items-center gap-1.5">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round">
                  <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M13 12H3"></path>
                </svg>
                {state?.conversation?.tools?.length ?? 0} tool
                {(state?.conversation?.tools?.length ?? 0) !== 1
                  ? "s"
                  : ""}{" "}
                used
              </div>
            )}
          </div>
        );
      }

      if (status === "complete") {
        isTravelInProgress.current = false;
        return null;
      }

      return null;
    },
  });

  // Helper function to format the status for display
  const getStatusText = () => {
    switch (state?.status?.phase) {
      case "initialized":
        return "Ready to help with your travel plans";
      case "processing":
        return "Processing your request...";
      case "processing_message":
        return "Processing message...";
      case "message_complete":
        return "Message processed";
      case "awaiting_input":
        return "Waiting for your input...";
      case "input_received":
        return "Processing your input...";
      case "executing":
        return "Executing tool...";
      case "tool_complete":
        return "Tool execution complete";
      case "completed":
        return "Travel planning complete";
      case "thread_completed":
        return "Conversation complete";
      case "error":
        return `Error: ${state.status.error || "Unknown error"}`;
      default:
        return "Ready to assist";
    }
  };

  // Show loading state when travel planning is in progress
  if (
    state?.status &&
    state.status.phase !== "completed" &&
    (isTravelInProgress.current || state.ui.loading)
  ) {
    return (
      <div className="flex flex-col gap-4 h-full max-w-4xl mx-auto">
        <div className="p-6 bg-white border rounded-lg shadow-sm w-full">
          <h3 className="text-xl font-semibold mb-4">
            Travel Planning in Progress
          </h3>

          <div className="status-container mb-6">
            <div className="flex items-center justify-between mb-2">
              <div className="font-medium text-gray-800">{getStatusText()}</div>
            </div>

            {state.ui.showProgress && (
              <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-blue-600 rounded-full transition-all duration-300 ease-in-out animate-pulse" />
              </div>
            )}
          </div>

          {/* Tool execution history */}
          {state?.conversation?.tools?.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Recent Actions
              </h4>
              <div className="space-y-2">
                {state.conversation.tools.slice(-3).map((tool) => (
                  <div
                    key={tool.id}
                    className="text-sm text-gray-600 flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    {tool.name}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className="w-screen bg-white flex flex-col overflow-hidden"
      style={{ height: "100vh" }}>
      {/* Welcome message that disappears when there are messages */}
      {(!visibleMessages || visibleMessages.length === 0) && (
        <div className="absolute top-[25%] left-0 right-0 mx-auto w-full max-w-3xl z-40 pl-10">
          <h1 className="text-4xl font-bold text-black mb-3">
            Hello, I am your Travel agent!
          </h1>
          <p className="text-2xl text-gray-500">
            I can create detailed, personalized day-by-day travel itineraries
            for any destination.
          </p>
          {state?.agent?.capabilities && (
            <div className="mt-4 flex gap-2">
              {state.agent.capabilities.map((capability) => (
                <span
                  key={capability}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                  {capability}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <Chat />
    </div>
  );
}

export default Travel;
