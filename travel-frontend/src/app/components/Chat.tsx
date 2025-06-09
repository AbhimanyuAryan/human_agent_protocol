import React from "react";
import { CopilotChat } from "@copilotkit/react-ui";

function Chat() {
  return (
    <div className="flex-1 flex justify-center items-center bg-white overflow-y-auto">
      <CopilotChat className="w-full max-w-3xl flex flex-col h-full py-6" />
    </div>
  );
}

export default Chat;
