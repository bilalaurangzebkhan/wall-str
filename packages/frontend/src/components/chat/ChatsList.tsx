import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { twMerge } from "tailwind-merge";
import { useState, useEffect } from "react";
import { RiMenuUnfoldFill, RiMenuUnfold2Fill } from "react-icons/ri";

import { api } from "@/api";
import { useSSE } from "@/hooks/useSSE";

export default function ChatsList({
  slug,
  className,
  forceCollapse,
}: {
  slug?: string;
  className?: string;
  forceCollapse?: boolean;
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const { data: chats } = useQuery({
    queryKey: ["/chats"],
    queryFn: async () => {
      const { data } = await api.chat.listChats({ throwOnError: true });
      return data;
    },
  });

  const sse = useSSE();
  const queryClient = useQueryClient();
  useEffect(() => {
    if (!sse) return;

    function onChatTitleUpdated() {
      queryClient.invalidateQueries({ queryKey: ["/chats"] });
    }
    sse.on("chat_title_updated", onChatTitleUpdated);
    return () => {
      sse.off("chat_title_updated", onChatTitleUpdated);
    };
  }, [sse, queryClient]);

  useEffect(() => {
    if (forceCollapse) {
      setIsCollapsed(forceCollapse);
    }
  }, [forceCollapse]);

  if (!chats) return null;

  return (
    <div
      className={twMerge(
        "relative py-4 px-2 transition-all duration-300",
        className,
        isCollapsed ? "md:w-12" : "md:w-48",
      )}
    >
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="cursor-pointer md:absolute left-3 top-4 p-2 hover:bg-base-300 rounded-lg transition-colors"
        aria-label={isCollapsed ? "Expand chat list" : "Collapse chat list"}
      >
        {isCollapsed ? (
          <RiMenuUnfoldFill size={18} className="text-base-content/60" />
        ) : (
          <RiMenuUnfold2Fill size={18} className="text-base-content/60" />
        )}
      </button>
      <div className={`md:flex md:flex-col gap-2 md:mt-10 ${isCollapsed ? "hidden md:hidden" : ""}`}>
        <Link
          href="/chat"
          className={`badge badge-md ${!slug ? "badge-neutral" : "badge-ghost"} transition-colors cursor-pointer whitespace-nowrap`}
        >
          New chat...
        </Link>
        {chats.items.map((chat, i) => (
          <Link
            key={chat.id}
            href={`/chat/${chat.slug}`}
            className={`badge badge-md  ml-2 ${
              chat.slug === slug ? "badge-neutral" : "badge-ghost"
            } transition-colors cursor-pointer whitespace-nowrap`}
          >
            {chat.title || `${i + 1}. Chat #${i + 1}`}
          </Link>
        ))}
      </div>
    </div>
  );
}
