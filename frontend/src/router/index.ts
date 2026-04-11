import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/auth-preview/:screen?",
      name: "auth-preview",
      component: () => import("@/views/auth/AuthPreviewView.vue"),
      meta: { layout: "auth-preview" },
    },
    {
      path: "/accounts/login/",
      name: "account-login",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "login" },
    },
    {
      path: "/accounts/signup/",
      name: "account-signup",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "signup" },
    },
    {
      path: "/accounts/password/reset/",
      name: "account-password-reset",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "password-reset" },
    },
    {
      path: "/accounts/password/reset/done/",
      name: "account-password-reset-done",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "password-reset-done" },
    },
    {
      path: "/accounts/confirm-email/",
      name: "account-confirm-email-sent",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "verification-sent" },
    },
    {
      path: "/accounts/confirm-email/:key/",
      name: "account-confirm-email-key",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "email-confirm-key" },
    },
    {
      path: "/accounts/logout/",
      name: "account-logout",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "logout" },
    },
    {
      path: "/accounts/inactive/",
      name: "account-inactive",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "inactive" },
    },
    {
      path: "/accounts/email/",
      name: "account-email",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "email-management" },
    },
    {
      path: "/accounts/password/change/",
      name: "account-password-change",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "password-change" },
    },
    {
      path: "/accounts/password/set/",
      name: "account-password-set",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "password-set" },
    },
    {
      path: "/accounts/password/reset/key/:uidb36-:key/",
      name: "account-password-reset-key",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "password-reset-key" },
    },
    {
      path: "/accounts/password/reset/key/done/",
      name: "account-password-reset-key-done",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "password-reset-key-done" },
    },
    {
      path: "/accounts/social/login/error/",
      name: "account-social-error",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "social-error" },
    },
    {
      path: "/accounts/social/login/cancelled/",
      name: "account-social-cancelled",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "social-cancelled" },
    },
    {
      path: "/accounts/social/connections/",
      name: "account-social-connections",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "connections" },
    },
    {
      path: "/accounts/reauthenticate/",
      name: "account-reauthenticate",
      component: () => import("@/views/auth/AuthFlowView.vue"),
      meta: { layout: "auth", authScreen: "reauthenticate" },
    },
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
    {
      path: "/coach/invite/:token",
      name: "invite-accept",
      component: () => import("@/views/invite/InviteView.vue"),
      meta: { appVariant: "athlete" },
    },
  ],
});

export default router;
