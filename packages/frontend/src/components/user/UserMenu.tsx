"use client";
import { useCallback, useContext, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api";
import { ConfigContext } from "@/providers/ConfigProvider";

import type { MouseEvent } from "react";
import type { UserSettings } from "@/api/wallstr-sdk";

export default function UserMenu() {
  const router = useRouter();
  const config = useContext(ConfigContext);
  const queryClient = useQueryClient();
  const [isLLMDropdownOpen, setLLMDropdownOpen] = useState(false);

  const { isPending, isError, data, error } = useQuery({
    queryKey: ["/auth/me"],
    queryFn: async () => {
      const { data } = await api.auth.getCurrentUser({ throwOnError: true });
      return data;
    },
  });

  const { mutate: changeUserSettings } = useMutation({
    mutationFn: async (llm_model: UserSettings["llm_model"]) => {
      const { data } = await api.auth.updateUserSettings({
        body: { llm_model },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/auth/me"] });
    },
  });

  const { mutate: changeSimpleMode } = useMutation({
    mutationFn: async (simple_mode: boolean) => {
      const { data } = await api.auth.updateUserSettings({
        body: { simple_mode },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/auth/me"] });
    },
  });

  const onLLMDropdownClick = useCallback(
    (e: MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setLLMDropdownOpen((prev) => !prev);
    },
    [setLLMDropdownOpen],
  );

  const onModelChange = useCallback(
    (model: string | null) => {
      changeUserSettings(model as UserSettings["llm_model"]);
      // https://github.com/saadeghi/daisyui/issues/157#issuecomment-1119796119
      setLLMDropdownOpen(false);
    },
    [changeUserSettings, setLLMDropdownOpen],
  );

  const handleSignOut = useCallback(() => {
    router.push("/auth/signout");
  }, [router]);

  if (isPending) {
    return <div className="animate-pulse h-8 w-8 rounded-full bg-gray-200" />;
  }

  if (isError) {
    console.error("Error fetching user:", error);
  }

  return (
    <div className="dropdown dropdown-end">
      <div tabIndex={0} role="button" className="avatar avatar-placeholder btn btn-ghost btn-circle">
        <div className="w-10 rounded-full bg-neutral text-neutral-content">
          <span className="text-lg font-semibold">{data?.username?.[0]?.toUpperCase() ?? "?"}</span>
        </div>
      </div>
      <ul tabIndex={0} className="dropdown-content menu menu-sm z-[1] mt-3 w-52 rounded-box bg-base-100 p-2 shadow">
        <li className="menu-title px-4 py-2">
          <span className="text-xs font-semibold uppercase text-base-content/80">Signed in as</span>
          <span className="text-sm font-medium">{data?.email}</span>
        </li>
        {config && (
          <li>
            <details className="dropdown dropdown-end dropdown-bottom" open={isLLMDropdownOpen}>
              <summary className="btn btn-xs btn-wide outline-none font-normal" onClick={onLLMDropdownClick}>
                LLM: {data?.settings.llm_model || "system"}
              </summary>
              <ul className="menu dropdown-content bg-base-100 rounded-box z-1 w-52 p-2 shadow-sm mt-1">
                <li>
                  <a onClick={() => onModelChange(null)}>system</a>
                </li>
                {config.llm_models.map((model) => (
                  <li key={model}>
                    <a onClick={() => onModelChange(model)}>{model}</a>
                  </li>
                ))}
              </ul>
            </details>
          </li>
        )}
        <li className="mt-2">
          <label className="flex justify-start ">
            <input
              type="checkbox"
              defaultChecked={!!data?.settings.simple_mode}
              className="toggle toggle-xs"
              onChange={(e) => changeSimpleMode(e.target.checked)}
            />
            <span>Simple mode</span>
          </label>
        </li>
        <li className="mt-2">
          <button onClick={handleSignOut}>Sign out</button>
        </li>
      </ul>
    </div>
  );
}
