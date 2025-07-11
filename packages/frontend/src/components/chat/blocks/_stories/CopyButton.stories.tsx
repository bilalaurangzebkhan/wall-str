import type { Meta, StoryObj } from "@storybook/react";

import CopyButton from "../CopyButton";
import { fn } from "@storybook/test";

const meta: Meta<typeof CopyButton> = {
  title: "components/chat/CopyButton",
  component: CopyButton,
  args: {
    onCopy: fn(),
  },
};

export default meta;

type TStory = StoryObj<typeof meta>;

export const Default: TStory = {};
