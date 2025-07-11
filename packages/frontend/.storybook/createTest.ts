import { createTest as storybookCreateTest } from "@storybook/react/experimental-playwright";

const createTest = <TFixture extends { extend: any }>(test: TFixture): TFixture => {
  // serviceWorkers: allow for making MSW work
  // https://github.com/microsoft/playwright/issues/30981
  return storybookCreateTest(test).extend({ serviceWorkers: "allow" });
};

export default createTest;
