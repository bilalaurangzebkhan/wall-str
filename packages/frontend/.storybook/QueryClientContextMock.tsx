import React from "react";
import type { Decorator } from "@storybook/react";

import QueryClientProvider from "@/providers/QueryClientProvider";
import { client } from "@/api/wallstr-sdk";
import { requestAuthInterceptor } from "@/api";

export const withQueryClientContext: Decorator = (Story, context) => {
  // eject interceptors
  client.interceptors.request.eject(requestAuthInterceptor);

  return (
    <QueryClientProvider>
      <Story {...context} />
    </QueryClientProvider>
  );
};
