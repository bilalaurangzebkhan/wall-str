import {test as base} from "@playwright/experimental-ct-react";

import createTest from "@/../.storybook/createTest";
import stories from "../_stories/SignInForm.stories.portable";

const test = createTest(base);

test("renders the SignInForm", async ({mount}) => {
  const component = await mount(<stories.Default />);
  await component.getByLabel("Email").fill("email@example.com");
  await component.getByLabel("Password").fill("password123");
});
