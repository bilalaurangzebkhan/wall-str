import { useRef, memo } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { noop } from "es-toolkit";
import { convert as htmlToText } from "html-to-text";
import { format } from "date-fns";

import CopyButton from "./CopyButton";
import DocumentsInlineBlock from "./DocumentsInlineBlock";
import MemoBlock from "./MemoBlock";

import type { Components } from "react-markdown";
import type { ChatMessage } from "@/api/wallstr-sdk/types.gen";

export default memo(function IncomeMessageBlock({
  message,
  onDocumentOpen,
  onToggleExpand,
  MarkdownComponents,
}: {
  message: ChatMessage;
  MarkdownComponents: Components;
  onToggleExpand?: (isExpanded: boolean) => void;
  onDocumentOpen?: (id: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  if (message.message_type === "memo") {
    return (
      <MemoBlock message={message} MarkdownComponents={MarkdownComponents} onToggleExpand={onToggleExpand || noop} />
    );
  }

  return (
    <div className={`chat ${message.role === "user" ? "chat-end" : "chat-start"}`}>
      {message.documents.length > 0 && (
        <DocumentsInlineBlock documents={message.documents} onDocumentOpen={onDocumentOpen} />
      )}
      {message.content && (
        <>
          <div
            className={`chat-bubble prose prose-sm relative ${
              message.role === "user" ? "bg-neutral text-neutral-content whitespace-pre-wrap" : ""
            }`}
          >
            <div
              ref={ref}
              className={`prose prose-sm ${
                message.role === "user" ? "bg-neutral text-neutral-content whitespace-pre-wrap" : ""
              }`}
            >
              <Markdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>
                {message.content}
              </Markdown>
            </div>
            {message.role === "assistant" && (
              <div className="text-right -mt-1 -mr-1 align-bottom">
                <CopyButton
                  className="align-bottom"
                  onCopy={async () => {
                    let html = "";
                    if (ref.current) {
                      html = ref.current.innerHTML.trim();
                      // remove all links to the documents sections
                      html = html.replace(/<button[^>]*>.*?<\/button>/g, "");
                    }
                    navigator.clipboard.write([
                      new ClipboardItem({
                        "text/html": new Blob([html], { type: "text/html" }),
                        "text/plain": new Blob([htmlToText(html)], { type: "text/plain" }),
                      }),
                    ]);
                  }}
                />
              </div>
            )}
          </div>

          {message.created_at && (
            <div className="chat-footer opacity-50 mt-0.5">{format(new Date(message.created_at), "p")}</div>
          )}
        </>
      )}
    </div>
  );
});
