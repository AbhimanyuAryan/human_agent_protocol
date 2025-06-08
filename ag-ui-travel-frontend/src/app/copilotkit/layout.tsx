import "@copilotkit/react-ui/styles.css";
import React, { ReactNode } from "react";
import { CopilotKit } from "@copilotkit/react-core";

// Where CopilotKit will proxy requests to. If you're using Copilot Cloud, this environment variable will be empty.
// const runtimeUrl = process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL;
const runtimeUrl = "/api/copilotkit";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <CopilotKit publicApiKey="ck_pub_01f0ba397100d16cd6e3310d0b62aab6"
      runtimeUrl={runtimeUrl}
      agent="travelAgent" // The name of the agent to use
    >
      {children}
    </CopilotKit>
  );
}
