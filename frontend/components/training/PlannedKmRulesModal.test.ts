import { describe, it, expect } from "vitest"
import { mount } from "@vue/test-utils"
import PlannedKmRulesModal from "./PlannedKmRulesModal.vue"

describe("PlannedKmRulesModal", () => {
  it("is hidden when isOpen is false", () => {
    const wrapper = mount(PlannedKmRulesModal, {
      props: { isOpen: false },
      attachTo: document.body,
    })
    expect(document.querySelector(".eb-modal-overlay")).toBeNull()
    wrapper.unmount()
  })

  it("shows content when isOpen is true", () => {
    const wrapper = mount(PlannedKmRulesModal, {
      props: { isOpen: true },
      attachTo: document.body,
    })
    expect(document.querySelector(".eb-modal-overlay")).not.toBeNull()
    wrapper.unmount()
  })

  it("emits close event on overlay click", async () => {
    const wrapper = mount(PlannedKmRulesModal, {
      props: { isOpen: true },
      attachTo: document.body,
    })
    const overlay = document.querySelector(".eb-modal-overlay") as HTMLElement
    expect(overlay).not.toBeNull()
    overlay.click()
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted("close")).toBeTruthy()
    wrapper.unmount()
  })
})
