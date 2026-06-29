import { el, jsonPre, toast } from "./ui.js";

export async function renderTasks(container, ctx) {
  const header = el("div", { class: "page-header" }, [
    el("h1", { text: "任务中心" }),
    el("div", { class: "muted", text: "查看任务、执行任务、查看执行记录" }),
  ]);

  const listCard = el("div", { class: "card" }, [
    el("div", { class: "toolbar" }, [
      el("button", { class: "secondary", text: "刷新列表", onclick: () => loadTasks() }),
      el("button", { class: "secondary", text: "执行到期任务", onclick: () => runDue() }),
    ]),
    el("div", { id: "tasksList" }, [jsonPre({})]),
  ]);

  const detailCard = el("div", { class: "card" }, [
    el("h2", { text: "任务详情" }),
    el("div", { id: "taskDetail" }, [jsonPre({ hint: "选择任务查看详情" })]),
  ]);

  async function loadTasks() {
    try {
      const res = await ctx.api("/api/v1/tasks");
      const tasks = res.data || [];
      const table = el("table", { class: "table" }, [
        el("thead", {}, [
          el("tr", {}, [
            el("th", { text: "task_id" }),
            el("th", { text: "status" }),
            el("th", { text: "attempts" }),
            el("th", { text: "scheduled_at" }),
            el("th", { text: "last_error_type" }),
          ]),
        ]),
        el(
          "tbody",
          {},
          tasks.map((t) =>
            el("tr", { onclick: () => loadTask(t.id), style: "cursor:pointer" }, [
              el("td", { text: t.id }),
              el("td", { text: t.status }),
              el("td", { text: String(t.attempts) }),
              el("td", { text: t.scheduled_at || "" }),
              el("td", { text: t.last_error_type || "" }),
            ])
          )
        ),
      ]);
      listCard.querySelector("#tasksList").replaceChildren(table);
      if (tasks.length === 0) listCard.querySelector("#tasksList").appendChild(el("div", { class: "muted", text: "暂无任务" }));
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  async function loadTask(taskId) {
    try {
      const res = await ctx.api(`/api/v1/tasks/${taskId}`);
      const data = res.data;
      const actions = el("div", { class: "toolbar" }, [
        el("button", { text: "执行任务", onclick: () => runTask(taskId) }),
      ]);
      detailCard.querySelector("#taskDetail").replaceChildren(
        el("div", { class: "stack" }, [actions, jsonPre(data)])
      );
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  async function runTask(taskId) {
    try {
      const res = await ctx.api(`/api/v1/tasks/${taskId}/run`, { method: "POST", body: "{}" });
      toast("已触发执行");
      detailCard.querySelector("#taskDetail").replaceChildren(jsonPre(res.data));
      await loadTasks();
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  async function runDue() {
    try {
      const res = await ctx.api("/api/v1/tasks/run-due", { method: "POST", body: JSON.stringify({ limit: 10 }) });
      toast("已触发到期任务执行");
      detailCard.querySelector("#taskDetail").replaceChildren(jsonPre(res.data));
      await loadTasks();
    } catch (e) {
      toast(String(e.message || e), "error");
    }
  }

  container.replaceChildren(el("div", { class: "page" }, [header, el("div", { class: "row" }, [listCard, detailCard])]));
  await loadTasks();
}

