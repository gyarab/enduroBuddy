import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createRouter, createMemoryHistory } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import TopNav from "@/components/layout/TopNav.vue";

vi.mock("@/components/layout/ProfileDropdown.vue", () => ({ default: { template: "<div />" } }));
vi.mock("@/components/layout/ProfileSettingsModal.vue", () => ({ default: { template: "<div />" } }));

const mockAuthStore = {
  user: {
    initials: "JN",
    first_name: "Jan",
    last_name: "Novák",
    capabilities: { garmin_connect_enabled: true, coached_athlete_count: 0 },
  },
  isAuthenticated: true,
  isCoach: false,
};
const mockTrainingStore = { selectedMonth: { label: "Červen 2026" } };
const mockCoachStore = { selectedMonth: { label: "Červen 2026" } };
const mockLegendStore = { isPanelOpen: false };

vi.mock("@/stores/auth", () => ({ useAuthStore: vi.fn(() => mockAuthStore) }));
vi.mock("@/stores/training", () => ({ useTrainingStore: vi.fn(() => mockTrainingStore) }));
vi.mock("@/stores/coach", () => ({ useCoachStore: vi.fn(() => mockCoachStore) }));
vi.mock("@/stores/legend", () => ({ useLegendStore: vi.fn(() => mockLegendStore) }));
vi.mock("@/components/training/GarminImportModal.vue", () => ({ default: { template: "<div />" } }));

function makeRouter(path = "/app/dashboard") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/app/dashboard", component: { template: "<div/>" } },
      { path: "/coach/plans", component: { template: "<div/>" } },
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
    mockAuthStore.user = {
      initials: "JN",
      first_name: "Jan",
      last_name: "Novák",
      capabilities: { garmin_connect_enabled: true, coached_athlete_count: 0 },
    };
    mockAuthStore.isAuthenticated = true;
    mockAuthStore.isCoach = false;
    mockTrainingStore.selectedMonth = { label: "Červen 2026" };
    mockCoachStore.selectedMonth = { label: "Červen 2026" };
    mockLegendStore.isPanelOpen = false;
  });

  it("renders logo mark", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-brand__mark").exists()).toBe(true);
  });

  it("shows username from auth store", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-brand__username").text()).toBe("Jan Novák");
  });

  it("shows month label", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-month").text()).toContain("Červen 2026");
  });

  it("shows sync button when garmin_connect_enabled=true", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--sync").exists()).toBe(true);
  });

  it("hides sync button when garmin_connect_enabled=false", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    vi.mocked(useAuthStore).mockReturnValueOnce({
      ...mockAuthStore,
      user: { ...mockAuthStore.user, capabilities: { garmin_connect_enabled: false, coached_athlete_count: 0 } },
    } as any);
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--sync").exists()).toBe(false);
  });

  it("shows legend button in athlete variant", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--legend").exists()).toBe(true);
  });

  it("hides legend button in coach variant", async () => {
    const router = makeRouter("/coach/plans");
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "coach" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--legend").exists()).toBe(false);
  });

  it("shows coach badge when isCoach=true and variant=athlete", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    vi.mocked(useAuthStore).mockReturnValueOnce({ ...mockAuthStore, isCoach: true } as any);
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--coach").exists()).toBe(true);
  });

  it("shows myPlan button in coach variant", async () => {
    const router = makeRouter("/coach/plans");
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "coach" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--myplan").exists()).toBe(true);
  });

  it("shows avatar with initials", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-avatar").text()).toBe("JN");
  });

  it("clicking legend button sets legendStore.isPanelOpen = true", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    await wrapper.find(".nav-btn--legend").trigger("click");
    expect(mockLegendStore.isPanelOpen).toBe(true);
  });
});
