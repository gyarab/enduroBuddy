import { describe, it, expect } from "vitest"
import { mount } from "@vue/test-utils"
import PlannedKmRulesModal from "./PlannedKmRulesModal.vue"

describe("PlannedKmRulesModal", () => {
  it("is hidden when isOpen is false", () => {
    const wrapper = mount(PlannedKmRulesModal, {
      props: { isOpen: false },
    })
    expect(wrapper.find(".eb-modal-overlay").exists()).toBe(false)
  })

  it("shows content when isOpen is true", () => {
    const wrapper = mount(PlannedKmRulesModal, {
      props: { isOpen: true },
      attachTo: document.body,
    })
    expect(wrapper.find(".eb-modal-overlay").exists()).toBe(true)
  })

  it("emits close event on overlay click", async () => {
    const wrapper = mount(PlannedKmRulesModal, {
      props: { isOpen: true },
      attachTo: document.body,
    })
    await wrapper.find(".eb-modal-overlay").trigger("click")
    expect(wrapper.emitted("close")).toBeTruthy()
  })
})
