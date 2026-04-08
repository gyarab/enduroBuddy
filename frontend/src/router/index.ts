import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/app/",
      redirect: "/app/dashboard",
      meta: { appVariant: "athlete" },
    },
    {
      path: "/app/dashboard",
      name: "athlete-dashboard",
      component: () => import("@/views/dashboard/AthleteView.vue"),
      meta: { appVariant: "athlete" },
    },
    {
      path: "/app/profile/complete",
      name: "complete-profile",
      component: () => import("@/views/profile/CompleteProfileView.vue"),
      meta: { appVariant: "athlete" },
    },
    {
      path: "/coach/",
      redirect: "/coach/plans",
      meta: { appVariant: "coach" },
    },
    {
      path: "/coach/plans",
      name: "coach-dashboard",
      component: () => import("@/views/dashboard/CoachView.vue"),
      meta: { appVariant: "coach" },
    },
  ],
});

export default router;
