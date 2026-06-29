import { reactive } from "vue";
import { api, setToken, getToken } from "../api/client";

export type Actor = {
  tenant_id?: string;
  workspace_id?: string;
  user_id: string;
  role: string;
  email: string;
  display_name: string;
};

export type Workspace = { id: string; tenant_id: string; name: string; created_at: string };

export const session = reactive({
  loading: false,
  actor: null as Actor | null,
  workspaces: [] as Workspace[],
});

export async function refreshSession() {
  if (!getToken()) {
    session.actor = null;
    session.workspaces = [];
    return;
  }
  session.loading = true;
  try {
    const me = await api<Actor | null>("/api/v1/me");
    session.actor = me.data;
    const ws = await api<Workspace[]>("/api/v1/workspaces");
    session.workspaces = ws.data || [];
  } finally {
    session.loading = false;
  }
}

export async function logout() {
  try {
    await api<{ ok: boolean }>("/api/v1/auth/logout", { method: "POST", body: "{}" });
  } catch {
    // ignore
  }
  setToken("");
  await refreshSession();
}

export async function switchWorkspace(workspace_id: string) {
  const res = await api<{ token: string; expires_at: string; workspace_id: string }>(
    "/api/v1/auth/switch-workspace",
    { method: "POST", body: JSON.stringify({ workspace_id }) }
  );
  setToken(res.data.token);
  await refreshSession();
}

export function canManageSystem(role?: string | null) {
  return role === "owner" || role === "admin";
}

export function canEditContent(role?: string | null) {
  return role === "owner" || role === "admin" || role === "editor";
}
