import type { Meta, StoryObj } from "@storybook/react";

import SignInForm from "../SignInForm";

const meta: Meta<typeof SignInForm> = {
  title: "components/auth/SignInForm",
  component: SignInForm,
  args: {
    urls: {
      forgotPassword: "#",
      signUp: "#",
    },
  },
};

export default meta;

type TStory = StoryObj<typeof meta>;

export const Default: TStory = {};
