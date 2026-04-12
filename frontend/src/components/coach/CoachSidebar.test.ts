import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import type { CoachAthlete } from "@/api/coach";
import CoachSidebar from "@/components/coach/CoachSidebar.vue";

const athletes: CoachAthlete[] = [
  {
    id: 101,
    name: "Alice Runner",
    focus: "10K",
    hidden: false,
    sort_order: 1,
    selected: true,
  },
  {
    id: 202,
    name: "Bob Climber",
    focus: "",
    hidden: false,
    sort_order: 2,
    selected: false,
  },
];

describe("CoachSidebar", () => {
  it("renders athletes and selected state", () => {
    const wrapper = mount(CoachSidebar, {
      props: {
        athletes,
      },
    });

    expect(wrapper.text()).toContain("Athletes");
    expect(wrapper.text()).toContain("Alice Runner");
    expect(wrapper.text()).toContain("Bob Climber");
    expect(wrapper.text()).toContain("10K");
    expect(wrapper.find(".coach-sidebar__item--active").text()).toContain("Alice Runner");
  });

  it("emits selected athlete id on click", async () => {
    const wrapper = mount(CoachSidebar, {
      props: {
        athletes,
      },
    });

    const buttons = wrapper.findAll("button");
    await buttons[1]!.trigger("click");

    expect(wrapper.emitted("select")).toEqual([[202]]);
  });
});
