import type { Meta, StoryObj } from "@storybook/react";

import SignUpForm from "../SignUpForm";

const meta: Meta<typeof SignUpForm> = {
  title: "components/auth/SignUpForm",
  component: SignUpForm,
  args: {
    urls: {
      signIn: "#",
    },
  },
};

export default meta;

type TStory = StoryObj<typeof meta>;

export const Default: TStory = {};
