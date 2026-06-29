export type ApiResponse<T> = { code: number; data: T; msg?: string };

export function getToken(): string {
  return localStorage.getItem("sau_token") || "";
}

export function setToken(token: string) {
  localStorage.setItem("sau_token", token || "");
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, { ...init, headers });
  const data = (await res.json()) as ApiResponse<T>;
  if (!res.ok || data.code !== 200) {
    throw new Error(data.msg || `请求失败: ${res.status}`);
  }
  return data;
}

