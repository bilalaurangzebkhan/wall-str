let cachedToken: string | null = null;

export function getToken(): string | null {
  if (cachedToken) return cachedToken;
  cachedToken = localStorage.getItem("access_token");
  return cachedToken;
}

export function setToken(token: string) {
  if (cachedToken === token) return;
  cachedToken = token;
  localStorage.setItem("access_token", token);
}

export function decodeJwt(token: string) {
  return JSON.parse(atob(token.split(".")[1]));
}

export function needsToRefreshToken(exp: number) {
  const n = Math.ceil(new Date().valueOf() / 1000);
  return exp <= n;
}
