import { setActiveNav } from "./ui.js";

export function currentRoute() {
  const hash = window.location.hash || "#/dashboard";
  const route = hash.startsWith("#") ? hash.slice(1) : hash;
  return route.startsWith("/") ? route : "/dashboard";
}

export function createRouter(routes) {
  async function render() {
    const route = currentRoute();
    setActiveNav(route);
    const handler = routes[route] || routes["/dashboard"];
    await handler();
  }

  window.addEventListener("hashchange", () => render());
  return { render };
}

