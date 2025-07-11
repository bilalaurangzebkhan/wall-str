"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { FaGithub } from "react-icons/fa";

export default function Navbar() {
  const router = useRouter();

  const handleAnchorClick = (e: React.MouseEvent<HTMLAnchorElement>, targetId: string) => {
    e.preventDefault();
    const element = document.getElementById(targetId);
    if (element) {
      element.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  };

  return (
    <nav className="fixed w-full top-0 z-50 px-4 py-3 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center">
          <h1 className="text-xl font-bold text-white">
            <a href="#hero" onClick={(e) => handleAnchorClick(e, "hero")}>
              Wallstr.chat
            </a>
          </h1>
        </div>

        <div className="hidden md:flex space-x-6">
          <a
            href="#features"
            onClick={(e) => handleAnchorClick(e, "features")}
            className="text-white/90 hover:text-blue-300 transition-colors text-sm"
          >
            Features
          </a>
          <a
            href="#demo"
            onClick={(e) => handleAnchorClick(e, "demo")}
            className="text-white/90 hover:text-blue-300 transition-colors text-sm"
          >
            Demo
          </a>
          <a
            href="#equity-research"
            onClick={(e) => handleAnchorClick(e, "equity-research")}
            className="text-white/90 hover:text-blue-300 transition-colors text-sm"
          >
            How it works
          </a>
          <a
            href="#cta"
            onClick={(e) => handleAnchorClick(e, "cta")}
            className="text-white/90 hover:text-blue-300 transition-colors text-sm"
          >
            Try
          </a>
        </div>

        <div className="flex items-center space-x-2">
          <div className="hidden md:flex items-center space-x-1">
            <a
              href="https://github.com/limanAI/wallstr"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 bg-gray-800 hover:bg-gray-700 text-white font-semibold px-2 py-1 rounded transition transform hover:scale-105"
            >
              <FaGithub size={14} />
              <span className="text-xs py-1">Github</span>
            </a>
          </div>
          {/*
          <button
            onClick={() => router.push("/chat")}
            className="relative inline-block overflow-hidden rounded p-[1px] cursor-pointer"
          >
            <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#a9a9a9_0%,#0c0c0c_50%,#a9a9a9_100%)]"></span>
            <div className="inline-flex text-sm rounded bg-neutral px-4 py-1 text-white backdrop-blur-xl hover:bg-black transition-colors">
              Login
            </div>
          </button>
          */}

          <button
            onClick={() => router.push("/chat")}
            className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold px-4 py-2 shadow-md transition-all transform hover:scale-105 rounded cursor-pointer"
          >
            Login
          </button>
        </div>
      </div>
    </nav>
  );
}
