export function loadState() {
  return {
    apiKey: localStorage.getItem("sau_api_key") || "",
    token: localStorage.getItem("sau_token") || "",
  };
}

export function saveApiKey(value) {
  localStorage.setItem("sau_api_key", value || "");
}

export function saveToken(value) {
  localStorage.setItem("sau_token", value || "");
}

export function authHeaders() {
  const { apiKey, token } = loadState();
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!token && apiKey) headers["X-SAU-API-Key"] = apiKey;
  return headers;
}

export async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers || {}) },
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.msg || JSON.stringify(data));
  }
  return data;
}

