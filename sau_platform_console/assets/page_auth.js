import { el, jsonPre, toast } from "./ui.js";

export function renderAuthPage(container, ctx) {
  const card = el("div", { class: "card" }, [
    el("div", { class: "page-header" }, [
      el("h1", { text: "登录" }),
      el("div", { class: "muted", text: "登录后可使用工作区切换、审批、AI 配置等能力。" }),
    ]),
    el("div", { class: "row", style: "margin-top:12px;" }, [
      el("div", { class: "stack" }, [
        el("input", { id: "authEmail", placeholder: "邮箱" }),
        el("input", { id: "authPassword", placeholder: "密码（>=8）", type: "password" }),
        el("div", { class: "toolbar" }, [
          el("button", {
            text: "登录",
            onclick: async () => {
              try {
                const email = document.getElementById("authEmail").value.trim();
                const password = document.getElementById("authPassword").value.trim();
                const res = await ctx.fetchJson("/api/v1/auth/login", { email, password });
                ctx.saveToken(res.data.token);
                toast("登录成功");
                await ctx.refreshContext();
                window.location.hash = "#/dashboard";
              } catch (e) {
                toast(String(e.message || e), "error");
              }
            },
          }),
          el("button", {
            class: "secondary",
            text: "注册",
            onclick: async () => {
              try {
                const email = document.getElementById("authEmail").value.trim();
                const password = document.getElementById("authPassword").value.trim();
                const res = await ctx.fetchJson("/api/v1/auth/register", {
                  email,
                  password,
                  display_name: email,
                });
                toast("注册成功，请登录");
                container.querySelector("#authResult").replaceChildren(jsonPre(res.data));
              } catch (e) {
                toast(String(e.message || e), "error");
              }
            },
          }),
        ]),
      ]),
      el("div", { class: "stack" }, [
        el("div", { class: "muted", text: "提示：如果你只是临时调试，也可以用 API Key 模式，但产品化建议都走登录态。" }),
        el("div", { id: "authResult" }, [jsonPre({})]),
      ]),
    ]),
  ]);

  container.replaceChildren(el("div", { class: "page" }, [card]));
}

