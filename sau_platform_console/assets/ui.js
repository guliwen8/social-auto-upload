export const $ = (id) => document.getElementById(id);

export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, String(v));
  }
  for (const child of children || []) {
    if (child == null) continue;
    node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

export function clear(node) {
  node.innerHTML = "";
}

export function jsonPre(value) {
  const pre = el("pre");
  pre.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return pre;
}

export function toast(message, type = "info") {
  const box = $("toast");
  if (!box) return;
  box.textContent = message;
  box.classList.add("show");
  box.style.borderColor = type === "error" ? "#b91c1c" : "#1f2937";
  window.clearTimeout(box._hideTimer);
  box._hideTimer = window.setTimeout(() => box.classList.remove("show"), 2400);
}

export function setActiveNav(route) {
  const nav = $("nav");
  if (!nav) return;
  const links = nav.querySelectorAll("a[data-route]");
  for (const link of links) {
    link.classList.toggle("active", link.getAttribute("data-route") === route);
  }
}

