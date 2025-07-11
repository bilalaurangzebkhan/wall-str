"use client";
import { AnchorHTMLAttributes, useEffect, useMemo, useState } from "react";
import { InfiniteData, useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { twMerge } from "tailwind-merge";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { api } from "@/api";
import type {
  ChatMessageRole,
  ChatMessageType,
  DocumentStatus,
  GetChatMessagesResponse,
} from "@/api/wallstr-sdk/types.gen";
import { useSSE } from "@/hooks/useSSE";

import IncomeMessageBlock from "./blocks/IncomeMessageBlock";

interface StreamingMessage {
  id: string;
  content: string;
  loading?: boolean;
}

type TReferencesMap = {
  [key: string]: number;
};

export default function ChatMessages({
  slug,
  onRefClick,
  onDocumentOpen,
  onToggleExpand,
  className,
}: {
  slug?: string;
  onRefClick?: (id: string | null) => void;
  onDocumentOpen?: (id: string) => void;
  onToggleExpand?: (isExpanded: boolean) => void;
  className?: string;
}) {
  const [streamingMessages, setStreamingMessages] = useState<StreamingMessage[]>([]);
  const [referencesMap, setReferencesMap] = useState<TReferencesMap>({});
  const [selectedRef, selectRef] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading } = useInfiniteQuery({
    queryKey: ["/chat", slug],
    queryFn: async ({ pageParam }) => {
      const { data } = await api.chat.getChatMessages({
        path: { slug: slug as string },
        query: { cursor: pageParam },
        throwOnError: true,
      });
      return data;
    },
    getNextPageParam: (lastPage) => lastPage?.cursor,
    initialPageParam: 0,
    enabled: !!slug,
  });

  const sse = useSSE();

  useEffect(() => {
    if (!sse) return;

    // TODO: Add types for SSE events
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    function onMessageStart(data: any) {
      setStreamingMessages((streamingMessages) => [...streamingMessages, { id: data.id, content: "", loading: true }]);
    }

    // TODO: Add types for SSE events
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    function onMessage(data: any) {
      setStreamingMessages((streamingMessages) => {
        const index = streamingMessages.findIndex((message) => message.id === data.id);
        if (index === -1) return streamingMessages;

        return [
          ...streamingMessages.slice(0, index),
          { id: data.id, content: streamingMessages[index].content + data.content },
          ...streamingMessages.slice(index + 1),
        ];
      });
    }

    // TODO: Add types for SSE events
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    function onMessageEnd(data: any) {
      setStreamingMessages((streamingMessages) => {
        const index = streamingMessages.findIndex((message) => message.id === data.id);
        if (index === -1) return streamingMessages;

        return [...streamingMessages.slice(0, index), ...streamingMessages.slice(index + 1)];
      });

      // Update the cache with the completed message using the new ID
      queryClient.setQueryData<InfiniteData<GetChatMessagesResponse>>(["/chat", slug], (old) => {
        if (!old) return old;

        const completedMessage = {
          id: data.new_id,
          content: data.content,
          role: "assistant" as ChatMessageRole,
          message_type: "text" as ChatMessageType,
          created_at: data.created_at,
          documents: [],
        };

        return {
          pages: [
            {
              items: [completedMessage, ...old.pages[0].items],
              cursor: old.pages[0].cursor,
            },
            ...old.pages.splice(1),
          ],
          pageParams: old.pageParams,
        };
      });
    }

    function onDocumentStatus(data: { id: string; status: DocumentStatus }) {
      queryClient.setQueryData<InfiniteData<GetChatMessagesResponse>>(["/chat", slug], (old) => {
        if (!old) return old;

        return {
          pages: old.pages.map((page) => ({
            ...page,
            items: page.items.map((message) => ({
              ...message,
              documents: message.documents?.map((doc) => (doc.id === data.id ? { ...doc, status: data.status } : doc)),
            })),
          })),
          pageParams: old.pageParams,
        };
      });
    }

    sse.on("message_start", onMessageStart);
    sse.on("message", onMessage);
    sse.on("message_end", onMessageEnd);
    sse.on("document_status", onDocumentStatus);

    return () => {
      sse.off("message_start", onMessageStart);
      sse.off("message", onMessage);
      sse.off("message_end", onMessageEnd);
      sse.off("document_status", onDocumentStatus);
    };
  }, [sse, setStreamingMessages, queryClient, slug]);

  const messages = useMemo(() => data?.pages.flatMap((page) => page?.items).reverse() ?? [], [data]);
  // parse content and find references
  useEffect(() => {
    if (!messages.length) return;

    const newRefs: TReferencesMap = { ...referencesMap };
    let nextIndex = Object.keys(referencesMap).length + 1;
    let hasChanges = false;

    const regExp = /\[([^\]]+)\]\(([^)]+)\)/g;
    messages.forEach((message) => {
      const matches: string[] = message.content.match(regExp) || [];

      if (message.memo?.sections) {
        message.memo.sections.map((memoSection) => {
          const memoSectionMatch = memoSection.content.match(regExp);
          if (memoSectionMatch) {
            matches.push(...memoSectionMatch);
          }
        });
      }

      if (!matches.length) return;

      matches.forEach((match: string) => {
        const href = match.match(/\(([^)]+)\)/)?.[1];
        if (!href) return;

        const ids = href.split(",").map((id) => id.trim());
        ids.forEach((id) => {
          if (!newRefs[id]) {
            newRefs[id] = nextIndex++;
            hasChanges = true;
          }
        });
      });
    });

    if (hasChanges) {
      setReferencesMap(newRefs);
    }
  }, [messages, referencesMap, setReferencesMap]);

  const MarkdownComponents = useMemo(
    () => ({
      a: ({ href }: AnchorHTMLAttributes<HTMLAnchorElement>) => (
        <ReferenceLink
          href={href}
          onRefClick={(id: string | null) => {
            if (id === selectedRef) {
              id = null;
            }
            if (onRefClick) {
              onRefClick(id);
            }
            selectRef(id);
          }}
          referencesMap={referencesMap}
          selectedId={selectedRef}
        />
      ),
    }),
    [referencesMap, selectedRef, onRefClick],
  );

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mx-auto max-w-4xl flex flex-col justify-end items-stretch h-full">
          <div className="animate-pulse space-y-4">
            <div className="chat chat-end">
              <div className="chat-bubble bg-neutral/20 text-neutral-content w-2/3 md:w-1/2 h-20"></div>
            </div>
            <div className="chat chat-start">
              <div className="chat-bubble w-full md:w-2/3 h-56"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={twMerge("flex flex-col justify-end px-3 md:px-0", className)}>
      <div className="flex flex-col-reverse w-full overflow-y-scroll">
        <div className="space-y-4 w-full max-w-4xl mx-auto">
          {hasNextPage && (
            <button
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
              className="btn btn-ghost btn-sm w-full"
            >
              {isFetchingNextPage ? "Loading more..." : "Load more"}
            </button>
          )}

          {messages.map((message) => (
            <IncomeMessageBlock
              key={message.id}
              message={message}
              onDocumentOpen={onDocumentOpen}
              onToggleExpand={onToggleExpand}
              MarkdownComponents={MarkdownComponents}
            />
          ))}

          {streamingMessages.map((message) => (
            <div className="chat chat-start" key={message.id}>
              <div className="chat-bubble prose prose-sm">
                <Markdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>
                  {message.loading ? "..." : message.content}
                </Markdown>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ReferenceLink({
  href,
  onRefClick,
  referencesMap,
  selectedId,
}: {
  href?: string;
  onRefClick: (id: string) => void;
  referencesMap: TReferencesMap;
  selectedId: string | null;
}) {
  if (!href) return null;

  const ids = href.split(",").map((id: string) => id.trim());
  if (ids.length === 0) return null;

  return (
    <span className="inline-flex flex-wrap gap-1">
      {ids.map((id, i) => (
        <button
          key={`${id}-${i}`}
          onClick={() => onRefClick(id)}
          className={twMerge(
            "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs",
            "transition-colors duration-200 cursor-pointer",
            selectedId === id ? "bg-primary text-primary-content" : "bg-base-200 hover:bg-base-300",
          )}
        >
          <span className="font-medium">{referencesMap[id] || ""}.</span>
        </button>
      ))}
    </span>
  );
}
