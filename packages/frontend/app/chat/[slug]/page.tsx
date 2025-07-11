"use client";
import { useParams } from "next/navigation";
import { InfiniteData, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useCallback, useRef, useEffect } from "react";

import ChatInput from "@/components/chat/ChatInput";
import ChatMessages from "@/components/chat/ChatMessages";
import ChatsList from "@/components/chat/ChatsList";
import { api } from "@/api";
import { getDocumentType } from "@/components/chat/utils";
import type { DocumentPayload, GetChatMessagesResponse } from "@/api/wallstr-sdk";
import dynamic from "next/dynamic";

// https://github.com/wojtekmaj/react-pdf/issues/1811#issuecomment-2284891560
const PDFViewer = dynamic(() => import("@/components/pdf_viewer/PDFViewer"), { ssr: false });

type BoundingBox = {
  points: [[number, number], [number, number], [number, number], [number, number]];
  layoutWidth: number;
  layoutHeight: number;
  pageNumber: number;
};

type TDocument = {
  title: string;
  documentUrl: string;
  page: number;
  bboxes?: BoundingBox[];
};

const MIN_PANEL_WIDTH = 576; // w-xl
const MAX_PANEL_WIDTH = 896; // max-w-4xl
const MD_BREAKPOINT = 768; // md breakpoint in pixels
const CHATS_LIST_COLLAPSE_WIDTH = 700;

export default function ChatPage() {
  const { slug } = useParams<{ slug: string }>();
  const queryClient = useQueryClient();
  const [selectedDocument, setSelectedDocument] = useState<TDocument | null>(null);
  const [isMdScreen, setIsMdScreen] = useState(false);
  const [panelWidth, setPanelWidth] = useState(MAX_PANEL_WIDTH);
  const [isExpanded, setIsExpanded] = useState(false);
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  // Handle screen size changes
  useEffect(() => {
    const checkScreenSize = () => {
      setIsMdScreen(window.innerWidth >= MD_BREAKPOINT);
      // Reset panel width when switching to mobile
      if (window.innerWidth < MD_BREAKPOINT) {
        setPanelWidth(MIN_PANEL_WIDTH);
      }
    };

    checkScreenSize();
    window.addEventListener("resize", checkScreenSize);
    return () => window.removeEventListener("resize", checkScreenSize);
  }, []);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (!isMdScreen) return;
      isDragging.current = true;
      startX.current = e.pageX;
      startWidth.current = panelWidth;
      document.body.style.cursor = "col-resize";
      e.preventDefault();
    },
    [panelWidth, isMdScreen],
  );

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging.current || !isMdScreen) return;

      const delta = startX.current - e.pageX;
      const newWidth = Math.min(Math.max(startWidth.current + delta, MIN_PANEL_WIDTH), MAX_PANEL_WIDTH);
      setPanelWidth(newWidth);
    },
    [isMdScreen],
  );

  const handleMouseUp = useCallback(() => {
    if (!isMdScreen) return;
    isDragging.current = false;
    document.body.style.cursor = "default";
  }, [isMdScreen]);

  const onToggleExpand = useCallback(
    (_isExpanded: boolean) => {
      setIsExpanded(_isExpanded);
    },
    [setIsExpanded],
  );

  useEffect(() => {
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  const { mutate, isPending } = useMutation({
    mutationFn: async ({ message, attachedFiles }: { message: string; attachedFiles: File[] }) => {
      const { data } = await api.chat.sendChatMessage({
        path: { slug },
        body: {
          message: message.trim() || null,
          // TODO: generate sha-suffix for documents
          documents: attachedFiles.map(
            (f): DocumentPayload => ({
              filename: f.name,
              doc_type: getDocumentType(f),
            }),
          ),
        },
        throwOnError: true,
      });

      const pendingDocuments = data.pending_documents || [];
      Promise.all(
        pendingDocuments.map(async (document) => {
          const file = attachedFiles.find((file) => file.name === document.filename);
          if (!file) return;

          const response = await fetch(document.presigned_url, {
            method: "PUT",
            body: file,
          });

          if (response.ok) {
            await api.documents.markDocumentUploaded({ path: { id: document.id } });
          }
        }),
      );

      return data;
    },
    onMutate: async ({ message, attachedFiles }) => {
      await queryClient.cancelQueries({ queryKey: ["/chat", slug] });

      const previousMessages = queryClient.getQueryData(["/chat", slug]);

      const optimisticMessage = {
        id: `temp-${Date.now()}`,
        content: message,
        role: "user",
        documents: attachedFiles.map((file) => ({
          id: `temp-${file.name}`,
          filename: file.name,
          status: "uploading",
        })),
      };

      queryClient.setQueryData(["/chat", slug], (old: InfiniteData<GetChatMessagesResponse>) => ({
        pages: [
          {
            items: [optimisticMessage],
            cursor: null,
          },
          ...(old?.pages || []),
        ],
        pageParams: [null, ...(old?.pageParams || [])],
      }));

      return { previousMessages };
    },
    onError: (_, __, context) => {
      if (context?.previousMessages) {
        queryClient.setQueryData(["/chat", slug], context.previousMessages);
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["/chat", slug], (old: InfiniteData<GetChatMessagesResponse>) => {
        if (!old?.pages) return old;

        const updatedPages = old.pages.map((page, index) => {
          if (index === 0) {
            return {
              ...page,
              items: page.items.map((message) => {
                if (message.id.toString().startsWith("temp-") && data.content == message.content) {
                  return data;
                }
                return message;
              }),
            };
          }
          return page;
        });

        return {
          ...old,
          pages: updatedPages,
        };
      });
    },
  });

  const handleRefClick = useCallback(
    async (id: string | null) => {
      if (!id) {
        setSelectedDocument(null);
        return;
      }
      const { data } = await api.documents.getDocumentBySection({
        path: { section_id: id },
      });

      if (!data) return;
      setSelectedDocument({
        title: data.document_title,
        documentUrl: data.document_url,
        page: data.page_number,
        // TODO
        // Remove on defining backend BoundingBox type
        bboxes: data.bboxes.map(
          (bbox) =>
            ({
              points: bbox.points,
              layoutWidth: bbox.layout_width,
              layoutHeight: bbox.layout_height,
              pageNumber: bbox.page_number,
            }) as BoundingBox,
        ),
      });
    },
    [setSelectedDocument],
  );

  const handleDocumentOpen = useCallback(
    async (id: string) => {
      const { data } = await api.documents.getDocumentUrl({
        path: { document_id: id },
      });

      if (!data) return;
      setSelectedDocument({
        title: data.document_title,
        documentUrl: data.document_url,
        page: 1,
      });
    },
    [setSelectedDocument],
  );

  return (
    <div className="flex flex-col md:flex-row flex-1 bg-base-200 w-full">
      {/*
      {isExpanded && <div className="absolute bg-black/60 h-screen w-screen z-1 left-0 top-0"></div>}
      */}
      <ChatsList slug={slug} forceCollapse={!!selectedDocument && panelWidth > CHATS_LIST_COLLAPSE_WIDTH} />

      <div className={`flex-1 flex flex-row ${isExpanded ? "absolute top-0 w-screen h-screen" : ""}`}>
        <div className={`flex-1 flex flex-col ${isExpanded ? "relative" : "overflow-y-scroll"}`}>
          <ChatMessages
            slug={slug}
            className="flex-1 overflow-y-scroll"
            onRefClick={handleRefClick}
            onDocumentOpen={handleDocumentOpen}
            onToggleExpand={onToggleExpand}
          />
          <ChatInput onSubmit={(message, files) => mutate({ message, attachedFiles: files })} isPending={isPending} />
        </div>
        {selectedDocument && (
          <div className="flex flex-row">
            <div
              className="hidden md:block w-1 hover:bg-base-300 cursor-col-resize active:bg-base-300 flex-shrink-0"
              onMouseDown={handleMouseDown}
            />
            <div className="bg-base-100 border-l border-base-300 flex flex-col w-full">
              <PDFViewer {...selectedDocument} onClose={() => setSelectedDocument(null)} width={panelWidth} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
