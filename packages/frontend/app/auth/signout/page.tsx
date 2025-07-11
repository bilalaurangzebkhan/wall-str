"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useQueryClient } from "@tanstack/react-query";

import { clearLocalStorage } from "@/hooks/useLocalStorage";
import { settings } from "@/conf";
import { api } from "@/api";

export default function SignOut() {
  const router = useRouter();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!router) return;
    if (!queryClient) return;

    Promise.all([api.auth.signout(), queryClient.cancelQueries()]).finally(() => {
      clearLocalStorage();
      queryClient.clear();
      router.replace(settings.REDIRECT_NON_AUTH_URL);
    });
  }, [router, queryClient]);
  return null;
}
