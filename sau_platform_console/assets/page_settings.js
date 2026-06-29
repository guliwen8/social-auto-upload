import { el, jsonPre, toast } from "./ui.js";

export async function renderSettings(container, ctx) {
  const header = el("div", { class: "page-header" }, [
    el("h1", { text: "设置" }),
    el("div", { class: "muted", text: "AI 配置、调试信息" }),
  ]);

  const aiCard = el("div", { class: "card" }, [
    el("h2", { text: "AI 配置（当前用户）" }),
    el("div", { class: "row" }, [
      el("input", { id: "aiBaseUrl", placeholder: "Base URL（OpenAI 兼容）" }),
      el("input", { id: "aiModel", placeholder: "Model（例如 gpt-4.1-mini）" }),
    ]),
    el("input", { id: "aiApiKey", placeholder: "API Key（保存后自动清空输入框）" }),
    el("div", { class: "toolbar" }, [
      el("button", { class: "secondary", text: "读取", onclick: () => load() }),
      el("button", { text: "保存", onclick: () => save() }),
    ]),
    el("div", { id: "aiOut" }, [jsonPre({})]),
  ]);

  async function load() {
    try {
      const res = await ctx.api("/api/v1/ai/settings");
      const data = res.data || {};
      aiCard.querySelector("#aiBaseUrl").value = data.base_url || "";
      aiCard.querySelector("#aiModel").value = data.model || "";
      aiCard.querySelector("#aiOut").replaceChildren(jsonPre(data));
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  async function save() {
    try {
      const payload = {
        provider: "openai_compat",
        base_url: aiCard.querySelector("#aiBaseUrl").value.trim(),
        api_key: aiCard.querySelector("#aiApiKey").value.trim(),
        model: aiCard.querySelector("#aiModel").value.trim() || "gpt-4.1-mini",
      };
      const res = await ctx.api("/api/v1/ai/settings", { method: "POST", body: JSON.stringify(payload) });
      aiCard.querySelector("#aiApiKey").value = "";
      aiCard.querySelector("#aiOut").replaceChildren(jsonPre(res.data));
      toast("已保存");
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  const debugCard = el("div", { class: "card" }, [
    el("h2", { text: "调试信息" }),
    jsonPre({ me: ctx.me, workspace_id: ctx.me?.workspace_id, workspaces: (ctx.workspaces || []).length }),
  ]);

  container.replaceChildren(el("div", { class: "page" }, [header, aiCard, debugCard]));
  await load();
}

