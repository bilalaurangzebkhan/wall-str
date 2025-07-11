import { z } from "zod";

const SettingsSchema = z.object({
  API_URL: z.string().url(),
  ENV: z.enum(["development", "production", "test"]),
  DEBUG: z.boolean(),

  GA_TAG: z.string().optional(),

  REDIRECT_NON_AUTH_URL: z.string(),
  jwt: z.object({
    issuer: z.string(),
  }),
});

export const settings = SettingsSchema.parse({
  API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  ENV: process.env.NODE_ENV,
  DEBUG: process.env.NODE_ENV === "development" && process.env.NEXT_PUBLIC_DEBUG === "true",

  GA_TAG: process.env.NEXT_PUBLIC_GA_TAG,

  REDIRECT_NON_AUTH_URL: "/auth/signin",
  jwt: {
    issuer: "https://github.com/limanAI/wallstr",
  },
});
