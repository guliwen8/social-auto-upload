import { el, jsonPre, toast } from "./ui.js";

function parseIds(raw) {
  return String(raw || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export async function renderContent(container, ctx) {
  const header = el("div", { class: "page-header" }, [
    el("h1", { text: "素材与草稿" }),
    el("div", { class: "muted", text: "素材库、草稿库，以及草稿与素材的关联" }),
  ]);

  const state = { assets: [], drafts: [], selected: null, mode: "assets" };

  const switcher = el("div", { class: "toolbar" }, [
    el("button", { class: "secondary", text: "素材", onclick: async () => { state.mode = "assets"; await refresh(); } }),
    el("button", { class: "secondary", text: "草稿", onclick: async () => { state.mode = "drafts"; await refresh(); } }),
    el("button", { class: "secondary", text: "刷新", onclick: async () => refresh() }),
  ]);

  const createAssetCard = el("div", { class: "card" }, [
    el("h2", { text: "创建素材" }),
    el("div", { class: "row" }, [
      el(
        "select",
        { id: "assetType" },
        ["video", "image"].map((t) => el("option", { value: t, text: t }))
      ),
      el("input", { id: "assetPath", placeholder: "素材路径（例如 videos/demo.mp4）" }),
    ]),
    el("div", { class: "toolbar" }, [
      el("button", { text: "创建", onclick: async () => createAsset() }),
    ]),
    el("div", { id: "assetCreateOut" }, [jsonPre({})]),
  ]);

  const createDraftCard = el("div", { class: "card" }, [
    el("h2", { text: "创建草稿" }),
    el("input", { id: "draftTitle", placeholder: "标题" }),
    el("textarea", { id: "draftDesc", placeholder: "描述" }),
    el("input", { id: "draftTags", placeholder: "tags（逗号分隔）" }),
    el("input", { id: "draftAssetIds", placeholder: "asset_ids（逗号分隔，可从素材列表复制）" }),
    el("div", { class: "toolbar" }, [
      el("button", { text: "创建", onclick: async () => createDraft() }),
    ]),
    el("div", { id: "draftCreateOut" }, [jsonPre({})]),
  ]);

  const listCard = el("div", { class: "card" }, [
    el("h2", { text: "列表" }),
    el("div", { id: "listOut" }, [jsonPre({})]),
  ]);

  const detailCard = el("div", { class: "card" }, [
    el("h2", { text: "详情" }),
    el("div", { id: "detailOut" }, [jsonPre({ hint: "点击列表行查看详情" })]),
  ]);

  function renderList() {
    const rows = state.mode === "assets" ? state.assets : state.drafts;
    const table = el("table", { class: "table" }, [
      el("thead", {}, [
        el("tr", {}, state.mode === "assets"
          ? [el("th", { text: "asset_id" }), el("th", { text: "type" }), el("th", { text: "path" }), el("th", { text: "created_at" })]
          : [el("th", { text: "draft_id" }), el("th", { text: "title" }), el("th", { text: "status" }), el("th", { text: "updated_at" })]
        ),
      ]),
      el(
        "tbody",
        {},
        rows.map((item) => {
          const cells = state.mode === "assets"
            ? [item.id, item.asset_type, item.path, item.created_at]
            : [item.id, item.title, item.status, item.updated_at];
          return el("tr", { onclick: () => { state.selected = item; renderDetail(); }, style: "cursor:pointer" }, cells.map((c) => el("td", { text: c || "" })));
        })
      ),
    ]);
    listCard.querySelector("#listOut").replaceChildren(table);
    if (rows.length === 0) listCard.querySelector("#listOut").appendChild(el("div", { class: "muted", text: "暂无数据" }));
  }

  function renderDetail() {
    detailCard.querySelector("#detailOut").replaceChildren(jsonPre(state.selected || { hint: "点击列表行查看详情" }));
  }

  async function refresh() {
    try {
      const [assetsRes, draftsRes] = await Promise.all([
        ctx.api("/api/v1/assets"),
        ctx.api("/api/v1/drafts"),
      ]);
      state.assets = assetsRes.data || [];
      state.drafts = draftsRes.data || [];
      renderList();
      renderDetail();
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  async function createAsset() {
    try {
      const asset_type = document.getElementById("assetType").value;
      const path = document.getElementById("assetPath").value.trim();
      const res = await ctx.api("/api/v1/assets", { method: "POST", body: JSON.stringify({ asset_type, path }) });
      createAssetCard.querySelector("#assetCreateOut").replaceChildren(jsonPre(res.data));
      toast("素材已创建");
      await refresh();
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  async function createDraft() {
    try {
      const title = document.getElementById("draftTitle").value.trim();
      const description = document.getElementById("draftDesc").value.trim();
      const tags = parseIds(document.getElementById("draftTags").value);
      const asset_ids = parseIds(document.getElementById("draftAssetIds").value);
      const res = await ctx.api("/api/v1/drafts", {
        method: "POST",
        body: JSON.stringify({ title, description, tags, asset_ids }),
      });
      createDraftCard.querySelector("#draftCreateOut").replaceChildren(jsonPre(res.data));
      toast("草稿已创建");
      await refresh();
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  const layout = el("div", { class: "page" }, [
    header,
    el("div", { class: "card" }, [switcher]),
    el("div", { class: "row" }, [createAssetCard, createDraftCard]),
    el("div", { class: "row" }, [listCard, detailCard]),
  ]);

  container.replaceChildren(layout);
  await refresh();
}

