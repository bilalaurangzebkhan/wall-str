"use client";
import { createContext } from "react";

import type { ReactNode } from "react";
import type { ConfigResponse } from "@/api/wallstr-sdk";

export const ConfigContext = createContext<ConfigResponse | null>(null);

export default function ConfigProvider({ children, config }: { children: ReactNode; config?: ConfigResponse }) {
  return <ConfigContext.Provider value={config ?? null}>{children}</ConfigContext.Provider>;
}
