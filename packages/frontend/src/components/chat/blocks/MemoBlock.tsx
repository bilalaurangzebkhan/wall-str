import { useCallback, useEffect, useMemo, useState } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { AgGridReact } from "ag-grid-react";
import {
  ClientSideRowModelModule,
  ColDef,
  RowAutoHeightModule,
  themeAlpine,
  colorSchemeDarkBlue,
} from "ag-grid-community";
import Markdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { convert as htmlToText } from "html-to-text";
import { groupBy } from "es-toolkit";
import { useTheme } from "next-themes";
import { HiOutlineArrowsExpand } from "react-icons/hi";
import { HiOutlineArrowsPointingIn } from "react-icons/hi2";

import CopyButton from "./CopyButton";

import type { MouseEvent } from "react";
import type { MemoSection, ChatMessage } from "@/api/wallstr-sdk/types.gen";

export default function MemoBlock({
  message,
  MarkdownComponents,
  onToggleExpand,
  className,
}: {
  message: ChatMessage;
  MarkdownComponents: Components;
  onToggleExpand: (sExpanded: boolean) => void;
  className?: string;
}) {
  const { resolvedTheme } = useTheme();
  const groupedSections = useMemo(() => groupBy(message.memo?.sections ?? [], (section) => section.group), [message]);
  const pages = useMemo(() => Object.keys(groupedSections).sort(), [groupedSections]);
  const [page, setPage] = useState(0);
  const [data, setData] = useState(groupedSections[pages[page]]);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    setData(
      groupedSections[pages[page]]?.map((section, index) => ({
        ...section,
        value: { index, content: section.content },
      })),
    );
  }, [page, pages, groupedSections]);

  const toggleExpand = useCallback(
    (e: MouseEvent<SVGElement>) => {
      e.preventDefault();
      e.stopPropagation();

      const _isExpanded = !isExpanded;
      onToggleExpand(_isExpanded);
      setIsExpanded(_isExpanded);
    },
    [onToggleExpand, setIsExpanded, isExpanded],
  );

  const onCopy = useCallback(async () => {
    const html = pages
      .map((page) => {
        const sections = groupedSections[page];

        return renderToStaticMarkup(
          <>
            <h1> {page}</h1>
            {sections.map((section) => (
              <>
                <h2>{section.aspect}</h2>
                <Markdown remarkPlugins={[remarkGfm]} components={MarkdownComponents} key={section.id}>
                  {section.content}
                </Markdown>
              </>
            ))}
          </>,
        );
      })
      .join("")
      .replace(/<button[^>]*>.*?<\/button>/g, "");

    navigator.clipboard.write([
      new ClipboardItem({
        "text/html": new Blob([html], { type: "text/html" }),
        "text/plain": new Blob([htmlToText(html)], { type: "text/plain" }),
      }),
    ]);
  }, [pages, groupedSections, MarkdownComponents]);

  const columnDefs: ColDef<MemoSection>[] = useMemo(() => {
    const headerName = pages[page] || "";

    return [
      {
        headerName: "",
        field: "aspect",
        spanHeaderHeight: true,
        maxWidth: 180,
        wrapText: true,
      },
      {
        headerName: headerName,
        wrapText: true,
        autoHeight: true,
        flex: 1,
        editable: true,
        cellRenderer: ({ data }: { data: MemoSection }) => {
          return (
            <div className="prose prose-sm prose-stone">
              <div id={`memo-${message.id}-${data.index}`}>
                <Markdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>
                  {data.content}
                </Markdown>
              </div>

              <div className="text-right">
                <CopyButton
                  className="align-top"
                  onCopy={async () => {
                    let html = "";
                    const elem = document.getElementById(`memo-${message.id}-${data.index}`);
                    if (elem) {
                      html = elem.innerHTML.trim();
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
            </div>
          );
        },
      },
    ];
  }, [pages, page, MarkdownComponents, message.id]);

  return (
    <div
      className={`${className || ""} flex flex-col ${isExpanded ? "absolute z-3 top-0 left-0 h-screen w-full bg-base-100" : "h-[calc(100vh-10em)]"}`}
    >
      <div className="relative flex-1">
        <div className="absolute top-2 right-2 p-2 z-2 flex flex-row gap-2">
          <CopyButton onCopy={onCopy} />
          {isExpanded ? (
            <HiOutlineArrowsPointingIn className="w-4 h-4 cursor-pointer animate-press" onClick={toggleExpand} />
          ) : (
            <HiOutlineArrowsExpand className="w-4 h-4 cursor-pointer animate-press" onClick={toggleExpand} />
          )}
        </div>

        <AgGridReact
          modules={[ClientSideRowModelModule, RowAutoHeightModule]}
          theme={resolvedTheme === "light" ? themeAlpine : themeAlpine.withPart(colorSchemeDarkBlue)}
          domLayout="normal"
          columnDefs={columnDefs}
          rowData={data}
        />
      </div>

      {pages.length > 1 && (
        <div className="my-2 relative flex justify-center">
          <ul className="join">
            {Array.from({ length: pages.length }, (_, index) => (
              <button
                className={`join-item btn btn-sm ${page === index ? "btn-active dark:bg-black/80" : ""}`}
                key={index}
                onClick={() => setPage(index)}
              >
                {index + 1}
              </button>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
