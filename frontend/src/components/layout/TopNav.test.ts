import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createRouter, createMemoryHistory } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import TopNav from "@/components/layout/TopNav.vue";

vi.mock("@/components/layout/NotificationBell.vue", () => ({ default: { template: "<div />" } }));
vi.mock("@/components/layout/ProfileDropdown.vue", () => ({ default: { template: "<div />" } }));
vi.mock("@/composables/useI18n", () => ({
  useI18n: () => ({ t: (k: string, p?: Record<string, string | number>) => k }),
}));

const mockAuthStore = { user: { initials: "AB", capabilities: { coached_athlete_count: 2 } } };
const mockCoachStore = { selectedAthlete: null, selectedMonth: null };
const mockTrainingStore = { selectedMonth: null };

vi.mock("@/stores/auth", () => ({
  useAuthStore: vi.fn(() => mockAuthStore),
}));
vi.mock("@/stores/coach", () => ({
  useCoachStore: vi.fn(() => mockCoachStore),
}));
vi.mock("@/stores/training", () => ({
  useTrainingStore: vi.fn(() => mockTrainingStore),
}));

function makeRouter(path = "/app/dashboard") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/app/dashboard", component: { template: "<div/>" } },
      { path: "/coach/plans", component: { template: "<div/>" } },
      { path: "/app/profile/complete", component: { template: "<div/>" } },
    ],
  });
  router.push(path);
  return router;
}

describe("TopNav", () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    // Reset shared mock state to safe defaults
    mockAuthStore.user = { initials: "AB", capabilities: { coached_athlete_count: 2 } };
    mockCoachStore.selectedAthlete = null;
    mockCoachStore.selectedMonth = null;
    mockTrainingStore.selectedMonth = null;
  });

  it("renders brand logo", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, {
      props: { variant: "athlete" },
      global: { plugins: [router, pinia] },
    });
    expect(wrapper.find('img[alt="EnduroBuddy"]').exists()).toBe(true);
  });

  it("athlete variant brand link points to /app/dashboard", async () => {
    const router = makeRouter("/app/dashboard");
    await router.isReady();
    const wrapper = mount(TopNav, {
      props: { variant: "athlete" },
      global: { plugins: [router, pinia] },
    });
    expect(wrapper.find("a.top-nav__brand").attributes("href")).toBe("/app/dashboard");
  });

  it("coach variant brand link points to /coach/plans", async () => {
    const router = makeRouter("/coach/plans");
    await router.isReady();
    const wrapper = mount(TopNav, {
      props: { variant: "coach" },
      global: { plugins: [router, pinia] },
    });
    expect(wrapper.find("a.top-nav__brand").attributes("href")).toBe("/coach/plans");
  });

  it("shows initials from auth store", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, {
      props: { variant: "athlete" },
      global: { plugins: [router, pinia] },
    });
    expect(wrapper.find("button.top-nav__avatar").text()).toBe("AB");
  });

  it("shows fallback initials when user is null", async () => {
    // Override auth store to return null user
    const { useAuthStore } = await import("@/stores/auth");
    vi.mocked(useAuthStore).mockReturnValueOnce({ user: null } as any);

    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, {
      props: { variant: "athlete" },
      global: { plugins: [router, pinia] },
    });
    expect(wrapper.find("button.top-nav__avatar").text()).toBe("EB");
  });

  it("toggles ProfileDropdown visibility when avatar button is clicked", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, {
      props: { variant: "athlete" },
      global: { plugins: [router, pinia] },
    });

    // ProfileDropdown should not be visible initially
    expect(wrapper.findComponent({ name: "ProfileDropdown" }).exists()).toBe(false);

    // Click avatar to open
    await wrapper.find("button.top-nav__avatar").trigger("click");
    expect(wrapper.findComponent({ name: "ProfileDropdown" }).exists()).toBe(true);

    // Click avatar again to close
    await wrapper.find("button.top-nav__avatar").trigger("click");
    expect(wrapper.findComponent({ name: "ProfileDropdown" }).exists()).toBe(false);
  });

  it("shows coachWorkspace title on /coach path", async () => {
    const router = makeRouter("/coach/plans");
    await router.isReady();
    const wrapper = mount(TopNav, {
      props: { variant: "coach" },
      global: { plugins: [router, pinia] },
    });
    expect(wrapper.find(".top-nav__title").text()).toBe("topNav.coachWorkspace");
  });

  it("shows completeProfile title on /profile path", async () => {
    const router = makeRouter("/app/profile/complete");
    await router.isReady();
    const wrapper = mount(TopNav, {
      props: { variant: "athlete" },
      global: { plugins: [router, pinia] },
    });
    expect(wrapper.find(".top-nav__title").text()).toBe("topNav.completeProfile");
  });

  it("shows dashboard title on /app/dashboard path", async () => {
    const router = makeRouter("/app/dashboard");
    await router.isReady();
    const wrapper = mount(TopNav, {
      props: { variant: "athlete" },
      global: { plugins: [router, pinia] },
    });
    expect(wrapper.find(".top-nav__title").text()).toBe("topNav.dashboard");
  });
});
