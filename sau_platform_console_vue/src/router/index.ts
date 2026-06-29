import { createRouter, createWebHashHistory } from "vue-router";
import LoginPage from "../views/LoginPage.vue";
import DashboardPage from "../views/DashboardPage.vue";
import ApprovalsPage from "../views/ApprovalsPage.vue";
import PlansPage from "../views/PlansPage.vue";
import TasksPage from "../views/TasksPage.vue";
import AccountsPage from "../views/AccountsPage.vue";
import ContentPage from "../views/ContentPage.vue";
import SettingsPage from "../views/SettingsPage.vue";
import AdminPage from "../views/AdminPage.vue";
import RiskPoliciesPage from "../views/RiskPoliciesPage.vue";
import { getToken } from "../api/client";
import { canManageSystem, session } from "../state/session";

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/login", component: LoginPage },
    { path: "/", component: DashboardPage },
    { path: "/approvals", component: ApprovalsPage },
    { path: "/plans", component: PlansPage },
    { path: "/tasks", component: TasksPage },
    { path: "/accounts", component: AccountsPage },
    { path: "/content", component: ContentPage },
    { path: "/admin", component: AdminPage, meta: { manageOnly: true } },
    { path: "/risk-policies", component: RiskPoliciesPage, meta: { manageOnly: true } },
    { path: "/settings", component: SettingsPage }
  ]
});

router.beforeEach((to) => {
  const authed = Boolean(getToken());
  if (!authed && to.path !== "/login") return "/login";
  if (authed && to.path === "/login") return "/";
  if (to.meta.manageOnly && session.actor && !canManageSystem(session.actor.role)) return "/";
  return true;
});
