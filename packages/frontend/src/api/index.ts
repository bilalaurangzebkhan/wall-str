import { Options } from "@hey-api/client-fetch";
import { z } from "zod";

import { settings } from "@/conf";
import { decodeJwt, getToken, needsToRefreshToken, setToken } from "@/utils/auth";
import { UnauthenticatedError } from "@/utils/errors";

import { AuthService, ChatService, client, DefaultService, DocumentsService } from "./wallstr-sdk";

const tokenResponseSchema = z.object({
  token: z.string(),
  token_type: z.literal("bearer"),
});

class TokenService {
  private refreshPromise: Promise<string> | null = null;

  validateToken(token: string): boolean {
    const payload = decodeJwt(token);
    return payload["iss"] === settings.jwt.issuer;
  }

  async refreshToken(token: string): Promise<string> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.doRefreshToken(token).finally(() => {
      this.refreshPromise = null;
    });

    return this.refreshPromise;
  }

  private async doRefreshToken(token: string): Promise<string> {
    const response = await fetch(`${settings.API_URL}/auth/refresh-token`, {
      method: "POST",
      credentials: "include",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new UnauthenticatedError();
    }

    const data = tokenResponseSchema.parse(await response.json());
    setToken(data.token);
    return data.token;
  }
}

const tokenService = new TokenService();

client.setConfig({
  baseUrl: settings.API_URL,
});

// Authorization token
export const requestAuthInterceptor = async (request: Request, options: Options) => {
  if (!options.security) {
    return request;
  }

  let token = getToken();
  if (!token) {
    throw new UnauthenticatedError();
  }

  if (!tokenService.validateToken(token)) {
    throw new UnauthenticatedError();
  }

  const payload = decodeJwt(token);
  if (needsToRefreshToken(payload["exp"] as number)) {
    token = await tokenService.refreshToken(token);
  }

  request.headers.set("Authorization", `Bearer ${token}`);
  return request;
};

client.interceptors.request.use(requestAuthInterceptor);

class API {
  public readonly client = client;
  public readonly auth = AuthService;
  public readonly chat = ChatService;
  public readonly default = DefaultService;
  public readonly documents = DocumentsService;
}

export const api = new API();
