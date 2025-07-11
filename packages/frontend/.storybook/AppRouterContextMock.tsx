import {AppRouterContext, AppRouterInstance} from "next/dist/shared/lib/app-router-context.shared-runtime";
import React from "react";

import type {Decorator} from "@storybook/react";
import {fn} from "@storybook/test";

/*
Requires mocking AppRouterContext to make stories work in Pywright

https://github.com/vercel/next.js/discussions/48937#discussioncomment-6395245
https://github.com/vercel/next.js/discussions/48937
https://github.com/vercel/next.js/discussions/63100#discussioncomment-8737391
https://github.com/storybookjs/storybook/blob/377e0babb3c82d50a03906c6a2a1775ad454537c/code/frameworks/nextjs/src/export-mocks/navigation/index.ts#L25
*/
export const withAppRouterContext: Decorator = (Story, context) => {
  return (
    <AppRouterContextProviderMock>
      <Story {...context} />
    </AppRouterContextProviderMock>
  );
};

export const AppRouterContextProviderMock = ({children}: {children: React.ReactNode}): React.ReactNode => {
  const mockedRouter: AppRouterInstance = {
    back: fn(),
    forward: fn(),
    push: fn(),
    replace: fn(),
    refresh: fn(),
    prefetch: fn(),
  };
  return <AppRouterContext.Provider value={mockedRouter}>{children}</AppRouterContext.Provider>;
};
