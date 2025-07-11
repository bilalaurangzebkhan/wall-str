import type { Meta, StoryObj } from "@storybook/react";

import DocumentsInlineBlock from "../DocumentsInlineBlock";
import { fn } from "@storybook/test";
import { http, HttpResponse } from "msw";

const meta: Meta<typeof DocumentsInlineBlock> = {
  title: "components/chat/blocks/DocumentsInlineBlock",
  component: DocumentsInlineBlock,
  parameters: {
    msw: {
      handlers: {
        process: http.post(`${process.env.NEXT_PUBLIC_API_URL}/documents/:id/process`, () =>
          HttpResponse.json(null, { status: 204 }),
        ),
      },
    },
  },
  args: {
    onDocumentOpen: fn(),
    documents: [
      {
        id: "id1",
        filename: "CR_Nvidia_Corp_NVDA_Key_Takeaways_from_CES_2025_Keynote__Focus_on_Physical.pdf",
        status: "ready",
      },
    ],
  },
};

export default meta;

type TStory = StoryObj<typeof meta>;

export const Default: TStory = {};

export const WithStatuses: TStory = {
  args: {
    documents: [
      {
        id: "id1",
        filename: "CR_Nvidia_Corp_NVDA_Key_Takeaways_from_CES_2025_Keynote__Focus_on_Physical.pdf",
        status: "ready",
      },
      {
        id: "id2",
        filename: "CR_ADOBE_20241212_0705.pdf",
        status: "uploading",
      },
      {
        id: "id3",
        filename: "Q3-NVDA-Company-Overview-FINAL.pdf",
        status: "uploaded",
      },
      {
        id: "id4",
        filename: "NVDA-F3Q25-Quarterly-Presentation-FINAL.pdf",
        status: "processing",
      },
      {
        id: "id5",
        filename: "CR_NVIDIA_Corp_NVDAO_Takeaways_from_Management_Meeting_at_CES_NVIDIA.pdf",
        status: "processing",
        error: "Failed to process",
        errored_at: new Date().toISOString(),
      },
    ],
  },
};
