import { el, jsonPre, toast } from "./ui.js";

export async function renderPlans(container, ctx) {
  const header = el("div", { class: "page-header" }, [
    el("h1", { text: "发布计划" }),
    el("div", { class: "muted", text: "创建发布计划、查看列表、提交审批" }),
  ]);

  const createCard = el("div", { class: "card" }, [
    el("h2", { text: "创建计划" }),
    el("div", { class: "row" }, [
      el("select", { id: "planPlatform" }, ["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent", "youtube"].map((p) => el("option", { value: p, text: p }))),
      el("select", { id: "planType" }, ["video", "note"].map((p) => el("option", { value: p, text: p }))),
    ]),
    el("div", { class: "row" }, [
      el("input", { id: "planAccountName", placeholder: "account_name" }),
      el("label", { class: "muted", style: "display:flex;align-items:center;gap:8px;" }, [
        el("input", { id: "planRequireApproval", type: "checkbox", style: "width:auto;" }),
        "需要审批",
      ]),
    ]),
    el("div", { class: "row" }, [
      el("input", { id: "planDraftId", placeholder: "draft_id（可选）" }),
      el("input", { id: "planAssetIds", placeholder: "asset_ids（可选，逗号分隔）" }),
    ]),
    el("textarea", { id: "planPayload", placeholder: 'payload JSON（可选）例如 {"title":"标题","video_file":"demo.mp4"}' }),
    el("div", { class: "toolbar" }, [
      el("button", { text: "创建", onclick: () => createPlan() }),
      el("button", { class: "secondary", text: "刷新列表", onclick: () => loadPlans() }),
    ]),
    el("div", { id: "planCreateOut" }, [jsonPre({})]),
  ]);

  const listCard = el("div", { class: "card" }, [
    el("h2", { text: "计划列表" }),
    el("div", { id: "planList" }, [jsonPre({})]),
  ]);

  const detailCard = el("div", { class: "card" }, [
    el("h2", { text: "计划详情" }),
    el("div", { id: "planDetail" }, [jsonPre({ hint: "点击列表中的 plan 查看详情" })]),
  ]);

  async function createPlan() {
    try {
      let payload = {};
      const raw = document.getElementById("planPayload").value.trim();
      if (raw) payload = JSON.parse(raw);
      const asset_ids = (document.getElementById("planAssetIds").value || "")
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const res = await ctx.api("/api/v1/publish-plans", {
        method: "POST",
        body: JSON.stringify({
          platform: document.getElementById("planPlatform").value,
          content_type: document.getElementById("planType").value,
          account_name: document.getElementById("planAccountName").value.trim(),
          draft_id: document.getElementById("planDraftId").value.trim() || undefined,
          asset_ids,
          require_approval: document.getElementById("planRequireApproval").checked,
          payload,
        }),
      });
      toast("创建成功");
      createCard.querySelector("#planCreateOut").replaceChildren(jsonPre(res.data));
      await loadPlans();
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  async function submitPlan(planId) {
    try {
      const res = await ctx.api(`/api/v1/publish-plans/${planId}/submit`, { method: "POST", body: "{}" });
      toast("已提交审批");
      detailCard.querySelector("#planDetail").replaceChildren(jsonPre(res.data));
      await loadPlans();
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  async function loadPlans() {
    try {
      const res = await ctx.api("/api/v1/publish-plans");
      const plans = res.data || [];
      const table = el("table", { class: "table" }, [
        el("thead", {}, [
          el("tr", {}, [
            el("th", { text: "plan_id" }),
            el("th", { text: "platform" }),
            el("th", { text: "account" }),
            el("th", { text: "type" }),
            el("th", { text: "status" }),
          ]),
        ]),
        el(
          "tbody",
          {},
          plans.map((p) =>
            el("tr", { onclick: () => showPlan(p), style: "cursor:pointer" }, [
              el("td", { text: p.id }),
              el("td", { text: p.platform }),
              el("td", { text: p.account_name }),
              el("td", { text: p.content_type }),
              el("td", { text: p.status }),
            ])
          )
        ),
      ]);
      listCard.querySelector("#planList").replaceChildren(table);
      if (plans.length === 0) listCard.querySelector("#planList").appendChild(el("div", { class: "muted", text: "暂无计划" }));
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  function showPlan(plan) {
    const actions = el("div", { class: "toolbar" }, [
      el("button", { class: "secondary", text: "查看审批记录", onclick: async () => {
        const res = await ctx.api(`/api/v1/approvals?plan_id=${encodeURIComponent(plan.id)}`);
        detailCard.querySelector("#planDetail").replaceChildren(jsonPre({ plan, approvals: res.data }));
      }}),
    ]);
    if (plan.status === "draft") {
      actions.appendChild(el("button", { text: "提交审批", onclick: () => submitPlan(plan.id) }));
    }
    detailCard.querySelector("#planDetail").replaceChildren(el("div", { class: "stack" }, [actions, jsonPre(plan)]));
  }

  container.replaceChildren(el("div", { class: "page" }, [header, createCard, el("div", { class: "row" }, [listCard, detailCard])]));
  await loadPlans();
}

