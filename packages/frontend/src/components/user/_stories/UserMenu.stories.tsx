import type {Meta, StoryObj} from "@storybook/react";
import {delay, http, HttpResponse} from "msw";

import UserMenu from "../UserMenu";

const userMock = {
  id: "123",
  email: "alice@example.com",
  username: "alice.storybook",
  fullname: "Alice Storybook",
};

const meta: Meta<typeof UserMenu> = {
  title: "components/user/UserMenu",
  component: UserMenu,
  parameters: {
    msw: {
      handlers: {
        me: http.get(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, () => HttpResponse.json(userMock)),
        signout: http.post(`${process.env.NEXT_PUBLIC_API_URL}/auth.signout`, () =>
          HttpResponse.json(null, {status: 204}),
        ),
      },
    },
  },
  loaders: [() => localStorage.setItem("access_token", "access_token")],
};

export default meta;

type TStory = StoryObj<typeof meta>;

export const Default: TStory = {};

export const Loading: TStory = {
  parameters: {
    msw: {
      handlers: {
        me: http.get(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, async () => {
          await delay(5000);
          return HttpResponse.json(userMock);
        }),
      },
    },
  },
};

export const NotAuthenticated: TStory = {
  parameters: {
    msw: {
      handlers: {
        me: http.get(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, () =>
          HttpResponse.json(
            {
              detail: "Not authenticated",
            },
            {status: 401},
          ),
        ),
      },
    },
  },
};

export const LongEmail: TStory = {
  parameters: {
    msw: {
      handlers: {
        me: http.get(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, () =>
          HttpResponse.json({...userMock, email: "very.long.email.address@really.long.domain.example.com"}),
        ),
      },
    },
  },
};

export const NoUsername: TStory = {
  parameters: {
    msw: {
      handlers: {
        me: http.get(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, () =>
          HttpResponse.json({...userMock, username: ""}),
        ),
      },
    },
  },
};
