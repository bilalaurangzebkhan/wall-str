import type {AppError} from "@/utils/errors";

declare module "@tanstack/react-query" {
  interface Register {
    defaultError: HTTPError | AppError;
  }
}
