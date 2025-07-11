import type { Meta, StoryObj } from "@storybook/react";

import { STORAGE_KEYS } from "@/hooks/useLocalStorage";
import ChatInput from "../ChatInput";
import { fn } from "@storybook/test";

const meta: Meta<typeof ChatInput> = {
  title: "components/chat/ChatInput",
  component: ChatInput,
  loaders: [() => localStorage.removeItem(STORAGE_KEYS.DRAFT_MESSAGE)],
  parameters: {
    args: {
      onSubmit: fn(),
    },
  },
};

export default meta;

type TStory = StoryObj<typeof meta>;

export const Default: TStory = {};

export const WithDraftMessage: TStory = {
  loaders: [() => localStorage.setItem(STORAGE_KEYS.DRAFT_MESSAGE, "This is a draft message")],
};

export const LongMessage: TStory = {
  loaders: [
    () =>
      localStorage.setItem(
        STORAGE_KEYS.DRAFT_MESSAGE,
        "This is a very long message that should trigger the auto-resize functionality of the textarea. It contains multiple lines of text to demonstrate how the component handles longer content and adjusts its height accordingly while respecting the maximum height constraint.",
      ),
  ],
};
