import {FaXTwitter} from "react-icons/fa6";

const footerLines = [GithubLine, XLine, YearLine];

export default function FooterLine() {
  const index = Math.round(Math.random() * (footerLines.length - 1));
  const Line = footerLines[index];

  return <Line />;
}

function GithubLine() {
  return (
    <a
      href="https://github.com/limanAI/wallstr"
      target="_blank"
      rel="noopener noreferrer"
      className="link link-hover inline-flex items-center gap-1"
    >
      Star us on GitHub
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="feather feather-star"
      >
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
    </a>
  );
}

function XLine() {
  return (
    <a href="https://x.com" target="_blank" rel="noopener noreferrer" className="link link-hover inline-flex gap-1">
      <span>Share on</span>
      <FaXTwitter className="w-4 h-4 relative -top-0.5" />
    </a>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function LoveLine() {
  return (
    <a
      href="https://x.com"
      target="_blank"
      rel="noopener noreferrer"
      className="link link-hover inline-flex justify-center gap-1"
    >
      <span>Built with</span>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth="1.5"
        stroke="currentColor"
        aria-hidden="true"
        className="inline-block h-4 w-4 relative"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
        ></path>
      </svg>
      <span>by wallstr team</span>
    </a>
  );
}

function YearLine() {
  return <span>2025</span>;
}
