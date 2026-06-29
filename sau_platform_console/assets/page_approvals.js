import { el, jsonPre, toast } from "./ui.js";

function planRow(plan, onSelect) {
  return el("tr", {}, [
    el("td", {}, [el("a", { href: "javascript:void(0)", onclick: () => onSelect(plan) }, [plan.id])]),
    el("td", { text: plan.platform }),
    el("td", { text: plan.account_name }),
    el("td", { text: plan.content_type }),
    el("td", { text: plan.status }),
    el("td", { text: plan.created_by || "" }),
  ]);
}

export async function renderApprovals(container, ctx) {
  const state = { selectedPlan: null, approvals: [] };

  async function loadPendingForMe() {
    const res = await ctx.api("/api/v1/publish-plans/pending-for-me");
    return res.data || [];
  }

  async function loadMine() {
    const res = await ctx.api("/api/v1/publish-plans/mine");
    return res.data || [];
  }

  async function loadApprovals(planId) {
    if (!planId) return [];
    const res = await ctx.api(`/api/v1/approvals?plan_id=${encodeURIComponent(planId)}`);
    return res.data || [];
  }

  async function approve(planId) {
    const comment = prompt("通过意见（可选）", "") || "";
    await ctx.api(`/api/v1/publish-plans/${planId}/approve`, { method: "POST", body: JSON.stringify({ comment }) });
    toast("已通过");
  }

  async function reject(planId) {
    const reason = prompt("驳回原因（必填）", "") || "";
    if (!reason.trim()) return toast("驳回原因不能为空", "error");
    await ctx.api(`/api/v1/publish-plans/${planId}/reject`, { method: "POST", body: JSON.stringify({ reason }) });
    toast("已驳回");
  }

  const header = el("div", { class: "page-header" }, [
    el("h1", { text: "审批中心" }),
    el("div", { class: "muted", text: "待我审批 / 我提交的 / 审批记录" }),
  ]);

  const tabs = el("div", { class: "toolbar" }, [
    el("button", { class: "secondary", text: "待我审批", onclick: async () => renderList(await loadPendingForMe(), true) }),
    el("button", { class: "secondary", text: "我提交的", onclick: async () => renderList(await loadMine(), false) }),
    el("button", { class: "secondary", text: "查看记录", onclick: () => renderRecordOnly() }),
  ]);

  const left = el("div", { class: "card" }, [
    el("h2", { text: "列表" }),
    el("div", { id: "approvalList" }, [jsonPre({})]),
  ]);

  const right = el("div", { class: "card" }, [
    el("h2", { text: "详情与记录" }),
    el("div", { id: "approvalDetail" }, [jsonPre({ hint: "选择一条计划查看" })]),
  ]);

  function renderList(plans, actionable) {
    const table = el("table", { class: "table" }, [
      el("thead", {}, [
        el("tr", {}, [
          el("th", { text: "plan_id" }),
          el("th", { text: "platform" }),
          el("th", { text: "account" }),
          el("th", { text: "type" }),
          el("th", { text: "status" }),
          el("th", { text: "created_by" }),
        ]),
      ]),
      el("tbody", {}, plans.map((p) => planRow(p, async (plan) => {
        state.selectedPlan = plan;
        state.approvals = await loadApprovals(plan.id);
        renderDetail(actionable);
      }))),
    ]);
    left.querySelector("#approvalList").replaceChildren(table);
    if (plans.length === 0) left.querySelector("#approvalList").appendChild(el("div", { class: "muted", text: "暂无数据" }));
    right.querySelector("#approvalDetail").replaceChildren(jsonPre({ hint: "选择一条计划查看" }));
  }

  function renderRecordOnly() {
    const planId = prompt("输入 plan_id（为空则取消）", "") || "";
    if (!planId.trim()) return;
    loadApprovals(planId.trim())
      .then((records) => {
        left.querySelector("#approvalList").replaceChildren(jsonPre({ plan_id: planId.trim(), records }));
        right.querySelector("#approvalDetail").replaceChildren(jsonPre({}));
      })
      .catch((e) => toast(String(e.message || e), "error"));
  }

  function renderDetail(actionable) {
    const plan = state.selectedPlan;
    const actions = actionable
      ? el("div", { class: "toolbar" }, [
          el("button", { text: "通过", onclick: async () => { await approve(plan.id); renderList(await loadPendingForMe(), true); } }),
          el("button", { class: "danger", text: "驳回", onclick: async () => { await reject(plan.id); renderList(await loadPendingForMe(), true); } }),
        ])
      : el("div", { class: "muted", text: "该列表为“我提交的”，不提供审批操作。" });

    right.querySelector("#approvalDetail").replaceChildren(
      el("div", { class: "stack" }, [
        el("div", { class: "muted", text: "发布计划" }),
        jsonPre(plan),
        el("div", { class: "muted", text: "审批记录" }),
        jsonPre(state.approvals),
        actions,
      ])
    );
  }

  container.replaceChildren(el("div", { class: "page" }, [header, el("div", { class: "card" }, [tabs]), el("div", { class: "row" }, [left, right])]));

  // 默认：待我审批
  try {
    renderList(await loadPendingForMe(), true);
  } catch (e) {
    toast(String(e.message || e), "error");
  }
}

