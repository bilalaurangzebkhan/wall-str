import { useEffect } from "react";

import { settings } from "@/conf";
import EventEmitter from "eventemitter3";

const ee = new EventEmitter();
let eventSource: EventSource | null = null;

export const useSSE = (): EventEmitter => {
  useEffect(() => {
    if (eventSource) return;

    eventSource = new EventSource(`${settings.API_URL}/sse`, {
      withCredentials: true,
    });

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      ee.emit(data.type, data);
    };

    eventSource.onerror = (error) => {
      console.warn("SSE Error:", error);
      eventSource?.close();
      eventSource = null;
    };

    return () => {
      eventSource?.close();
      eventSource = null;
    };
  }, []);

  return ee;
};
