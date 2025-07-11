import type { DocumentType } from "@/api/wallstr-sdk";

export const getDocumentType = (file: File): DocumentType => {
  switch (file.type) {
    case "application/pdf":
      return "pdf";
    default:
      throw new Error("Unsupported file type");
  }
};
