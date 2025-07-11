"use client";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import { useState, useEffect, useMemo } from "react";
import { FaTimes } from "react-icons/fa";
import { Document, Page, pdfjs } from "react-pdf";
import { debounce } from "es-toolkit";

type BoundingBox = {
  points: [[number, number], [number, number], [number, number], [number, number]];
  pageNumber: number;
  layoutWidth: number;
  layoutHeight: number;
};

// Initialize PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PDFViewer({
  documentUrl,
  title,
  width,
  page,
  onClose,
  bboxes = [],
}: {
  documentUrl: string;
  title: string;
  width: number;
  page: number;
  onClose: () => void;
  bboxes?: BoundingBox[];
}) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [debouncedWidth, setDebouncedWidth] = useState(width);

  const debouncedSetWidth = useMemo(() => debounce((value: number) => setDebouncedWidth(value), 100), []);
  useEffect(() => {
    debouncedSetWidth(width);
    return () => {
      debouncedSetWidth.cancel();
    };
  }, [width, debouncedSetWidth]);

  const onLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(page);
  };

  return (
    <>
      <div className="flex justify-between items-center p-4 border-b border-base-300">
        <h3 className="text-lg font-semibold truncate">{title}</h3>
        <div className="flex items-center gap-2">
          <button onClick={onClose} className="btn btn-ghost btn-sm btn-square">
            <FaTimes />
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4" style={{ width: width + 2 }}>
        <Document file={documentUrl} onLoadSuccess={onLoadSuccess} className="flex flex-col items-center">
          <div style={{ position: "relative" }}>
            <Page pageNumber={pageNumber} width={debouncedWidth} renderTextLayer={true} renderAnnotationLayer={true} />
            {bboxes.map((bbox, index) => (
              <HighlightOverlay key={index} bbox={bbox} pageWidth={debouncedWidth} pageNumber={pageNumber} />
            ))}
          </div>
        </Document>
      </div>
      <div className="p-4 border-t border-base-300 flex justify-between items-center">
        <span className="text-sm">
          Page {pageNumber} of {numPages}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPageNumber((prev) => Math.max(prev - 1, 1))}
            disabled={pageNumber <= 1}
            className="btn btn-ghost btn-sm"
          >
            Previous
          </button>
          <button
            onClick={() => setPageNumber((prev) => Math.min(prev + 1, numPages || 1))}
            disabled={pageNumber >= (numPages || 1)}
            className="btn btn-ghost btn-sm"
          >
            Next
          </button>
        </div>
      </div>
    </>
  );
}

function HighlightOverlay({
  bbox,
  pageWidth,
  pageNumber,
}: {
  bbox: BoundingBox;
  pageWidth: number;
  pageNumber: number;
}) {
  if (pageNumber != bbox.pageNumber) return null;
  const scale = pageWidth / bbox.layoutWidth;

  const [[x1, y1], , [x2, y2]] = bbox.points;
  const style = {
    left: x1 * scale,
    top: y1 * scale,
    width: (x2 - x1) * scale,
    height: (y2 - y1) * scale,
  };

  return <div style={style} className="pointer-events-none absolute bg-warning/10" />;
}
