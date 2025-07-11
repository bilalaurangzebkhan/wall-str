"use client";
import { useState, useRef, useEffect } from "react";
import { IoAttach } from "react-icons/io5";
import { AiOutlineFile, AiOutlineClose } from "react-icons/ai";

import { STORAGE_KEYS } from "@/hooks/useLocalStorage";

const MAX_LINES_HEIGHT = 15;

export default function ChatInput({
  onSubmit,
  isPending,
}: {
  onSubmit: (message: string, attachedFiles: File[]) => void;
  isPending?: boolean;
}) {
  const [message, setMessage] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(STORAGE_KEYS.DRAFT_MESSAGE) || "";
    }
    return "";
  });
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize logic
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    const lineHeight = parseInt(getComputedStyle(textarea).lineHeight);
    const maxHeight = lineHeight * MAX_LINES_HEIGHT;
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);

    textarea.style.height = `${newHeight}px`;
  }, [message]);

  // Save to localStorage on input
  useEffect(() => {
    if (message.trim()) {
      localStorage.setItem(STORAGE_KEYS.DRAFT_MESSAGE, message);
    } else {
      localStorage.removeItem(STORAGE_KEYS.DRAFT_MESSAGE);
    }
  }, [message]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachedFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  const removeFile = (fileToRemove: File) => {
    setAttachedFiles((prev) => prev.filter((file) => file !== fileToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() && attachedFiles.length === 0) return;

    onSubmit(message.trim(), attachedFiles);
    setMessage("");
    setAttachedFiles([]);
    localStorage.removeItem(STORAGE_KEYS.DRAFT_MESSAGE);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Submit on Ctrl+Enter or Cmd+Enter (for Mac)
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="p-4">
      <form onSubmit={handleSubmit} className="mx-auto max-w-4xl relative">
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2">
            {attachedFiles.map((file, index) => (
              <div key={index} className="badge badge-neutral gap-2">
                <AiOutlineFile />
                {file.name}
                <button
                  type="button"
                  onClick={() => removeFile(file)}
                  className="hover:scale-115 active:scale-95 cursor-pointer"
                >
                  <AiOutlineClose />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="relative flex items-start">
          <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" multiple accept=".pdf" />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="absolute left-2 top-1/2 -translate-y-1/2 p-2 cursor-pointer z-2"
          >
            <IoAttach className="text-xl" />
          </button>

          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Ctrl+Enter to send)"
            rows={1}
            className="textarea textarea-bordered w-full pl-12 pr-20 resize-none min-h-[2.5rem] max-h-[10rem] overflow-y-auto max-h-none"
            disabled={isPending}
          />

          <div className="absolute right-0 top-1/2 -translate-y-1/2">
            <button
              type="submit"
              className="btn btn-ghost cursor-pointer hover:bg-transparent hover:border-0 hover:shadow-none border-0 active:bg-transparent active:border-0"
              disabled={(!message.trim() && attachedFiles.length === 0) || isPending}
            >
              {isPending ? "Sending..." : "Send"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
