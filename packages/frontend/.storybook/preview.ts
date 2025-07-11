import type { Preview } from "@storybook/react";

import { MINIMAL_VIEWPORTS } from "@storybook/addon-viewport";
import { initialize, mswLoader, getWorker } from "msw-storybook-addon";

import { withAppRouterContext } from "./AppRouterContextMock";
import { withQueryClientContext } from "./QueryClientContextMock";
import "../app/globals.css";

initialize();

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    viewport: {
      viewports: MINIMAL_VIEWPORTS,
    },
    layout: "centered",
    nextjs: {
      appDirectory: true,
    },
  },
  decorators: [withQueryClientContext, withAppRouterContext],
  // https://github.com/mswjs/msw-storybook-addon/issues/89#issuecomment-2051972538
  loaders: [mswLoader, () => getWorker().start()],
};

export default preview;
