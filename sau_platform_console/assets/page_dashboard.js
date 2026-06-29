import { el, jsonPre } from "./ui.js";

export async function renderDashboard(container, ctx) {
  const me = ctx.me || null;
  const workspaces = ctx.workspaces || [];

  const card = el("div", { class: "card" }, [
    el("div", { class: "page-header" }, [
      el("h1", { text: "仪表盘" }),
      el("div", { class: "muted", text: "当前工作区概览与快捷入口" }),
    ]),
    el("div", { class: "row", style: "margin-top:12px;" }, [
      el("div", { class: "stack" }, [
        el("h2", { text: "当前身份" }),
        jsonPre(me || { hint: "未登录" }),
      ]),
      el("div", { class: "stack" }, [
        el("h2", { text: "可访问工作区" }),
        jsonPre(workspaces.map((w) => ({ id: w.id, name: w.name })) ),
      ]),
    ]),
  ]);

  const quick = el("div", { class: "card" }, [
    el("h2", { text: "快捷入口" }),
    el("div", { class: "toolbar" }, [
      el("button", { class: "secondary", text: "去审批中心", onclick: () => (window.location.hash = "#/approvals") }),
      el("button", { class: "secondary", text: "去任务中心", onclick: () => (window.location.hash = "#/tasks") }),
      el("button", { class: "secondary", text: "去发布计划", onclick: () => (window.location.hash = "#/plans") }),
      el("button", { class: "secondary", text: "去 AI 设置", onclick: () => (window.location.hash = "#/settings") }),
    ]),
  ]);

  container.replaceChildren(el("div", { class: "page" }, [card, quick]));
}

