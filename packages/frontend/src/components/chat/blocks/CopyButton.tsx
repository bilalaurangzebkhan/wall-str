"use client";
import { useState } from "react";
import { HiOutlineDuplicate, HiOutlineCheck } from "react-icons/hi";
import { twMerge } from "tailwind-merge";

export default function CopyButton({ onCopy, className }: { onCopy: () => void; className?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    onCopy();
    setCopied(true);
    setTimeout(() => {
      setCopied(false);
    }, 750);
  };

  return (
    <button
      onClick={handleCopy}
      className={twMerge("inline-flex items-center gap-1 text-xs transition-colors cursor-pointer", className)}
    >
      <span className={`opacity-0 transition-opacity ${copied ? "opacity-100" : "opacity-0"}`}>Copied</span>
      {copied ? (
        <HiOutlineCheck className="w-4 h-4" />
      ) : (
        <>
          <HiOutlineDuplicate className="w-4 h-4 animate-press" />
          <span className="sr-only">Copy</span>
        </>
      )}
    </button>
  );
}
