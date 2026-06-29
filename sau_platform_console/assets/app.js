import { api as apiCall, loadState, saveApiKey, saveToken } from "./api.js";
import { $, toast } from "./ui.js";
import { createRouter } from "./router.js";
import { renderAuthPage } from "./page_auth.js";
import { renderDashboard } from "./page_dashboard.js";
import { renderApprovals } from "./page_approvals.js";
import { renderTasks } from "./page_tasks.js";
import { renderPlans } from "./page_plans.js";
import { renderSettings } from "./page_settings.js";
import { renderContent } from "./page_content.js";

const appRoot = $("app");

function renderWorkspaceOptions(workspaces, selectedId, searchText = "") {
  const select = $("workspaceSelectTop");
  select.innerHTML = "";
  const query = (searchText || "").trim().toLowerCase();
  const filtered = (workspaces || [])
    .filter((ws) => {
      if (!query) return true;
      return String(ws.name || "").toLowerCase().includes(query) || String(ws.id || "").toLowerCase().includes(query);
    })
    .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));
  for (const ws of filtered) {
    const opt = document.createElement("option");
    opt.value = ws.id;
    opt.textContent = `${ws.name} · ${ws.id}`;
    if (selectedId && ws.id === selectedId) opt.selected = true;
    select.appendChild(opt);
  }
}

async function fetchJson(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json();
  if (!res.ok || data.code !== 200) throw new Error(data.msg || "request failed");
  return data;
}

const ctx = {
  me: null,
  workspaces: [],
  api: apiCall,
  fetchJson,
  saveToken: (value) => saveToken(value),
  async refreshContext() {
    try {
      const me = await apiCall("/api/v1/me");
      ctx.me = me.data || null;
      $("actorBadge").textContent = ctx.me
        ? `${ctx.me.display_name || ctx.me.email || ctx.me.user_id} (${ctx.me.role})`
        : "未登录";
      const ws = await apiCall("/api/v1/workspaces");
      ctx.workspaces = ws.data || [];
      renderWorkspaceOptions(ctx.workspaces, ctx.me?.workspace_id, $("workspaceSearchTop").value);
    } catch {
      ctx.me = null;
      ctx.workspaces = [];
      $("actorBadge").textContent = "未登录";
      renderWorkspaceOptions([], "", "");
    }
  },
};

async function requireLogin() {
  await ctx.refreshContext();
  if (!ctx.me) {
    renderAuthPage(appRoot, ctx);
    return false;
  }
  return true;
}

const router = createRouter({
  "/dashboard": async () => {
    if (!(await requireLogin())) return;
    await renderDashboard(appRoot, ctx);
  },
  "/approvals": async () => {
    if (!(await requireLogin())) return;
    await renderApprovals(appRoot, ctx);
  },
  "/plans": async () => {
    if (!(await requireLogin())) return;
    await renderPlans(appRoot, ctx);
  },
  "/tasks": async () => {
    if (!(await requireLogin())) return;
    await renderTasks(appRoot, ctx);
  },
  "/accounts": async () => {
    if (!(await requireLogin())) return;
    appRoot.replaceChildren(document.createElement("div"));
    toast("账号中心页面稍后补齐，先用 CLI 或旧控制台接口调试。", "info");
  },
  "/content": async () => {
    if (!(await requireLogin())) return;
    await renderContent(appRoot, ctx);
  },
  "/settings": async () => {
    if (!(await requireLogin())) return;
    await renderSettings(appRoot, ctx);
  },
});

function bindTopbar() {
  const { apiKey, token } = loadState();
  // 仍保留 apiKey 作为兜底
  if (apiKey && !token) saveApiKey(apiKey);

  $("workspaceSearchTop").addEventListener("input", (e) => {
    renderWorkspaceOptions(ctx.workspaces, $("workspaceSelectTop").value, e.target.value || "");
  });

  $("switchWorkspaceTop").onclick = async () => {
    try {
      const workspace_id = $("workspaceSelectTop").value;
      const res = await apiCall("/api/v1/auth/switch-workspace", {
        method: "POST",
        body: JSON.stringify({ workspace_id }),
      });
      saveToken(res.data.token);
      toast("已切换工作区");
      await ctx.refreshContext();
      await router.render();
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  };

  $("logoutTop").onclick = async () => {
    try {
      await apiCall("/api/v1/auth/logout", { method: "POST", body: "{}" });
    } catch {}
    saveToken("");
    toast("已退出");
    await ctx.refreshContext();
    await router.render();
  };
}

window.addEventListener("error", (e) => toast(String(e.error || e.message), "error"));

// Init
(() => {
  bindTopbar();
  ctx.refreshContext().then(() => router.render());
})();
