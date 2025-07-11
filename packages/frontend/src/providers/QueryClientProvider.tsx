"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  DefaultError,
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider as TanstackQueryClientProvider,
} from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { UnauthenticatedError } from "@/utils/errors";
import { settings } from "@/conf";

const RETRIES = 3;

export default function QueryClientProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: (count: number, error: DefaultError) => {
              if (error instanceof UnauthenticatedError) {
                return false;
              }
              return count < RETRIES;
            },
          },
          mutations: {
            retry: (count: number, error: DefaultError) => {
              if (error instanceof UnauthenticatedError) {
                return false;
              }
              return count < RETRIES;
            },
          },
        },
        queryCache: new QueryCache({
          onError: async (error: DefaultError) => {
            if (error instanceof UnauthenticatedError) {
              router.push("/auth/signout");
            }
          },
        }),
        mutationCache: new MutationCache({
          onError: async (error: DefaultError) => {
            if (error instanceof UnauthenticatedError) {
              router.push("/auth/signout");
            }
          },
        }),
      }),
  );

  return (
    <TanstackQueryClientProvider client={queryClient}>
      {children}
      {settings.DEBUG && <ReactQueryDevtools buttonPosition="bottom-left" />}
    </TanstackQueryClientProvider>
  );
}
