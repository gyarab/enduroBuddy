import { useInlineEditor } from "./useInlineEditor";

describe("useInlineEditor", () => {
  const factory = () => ({ name: "default", pace: "5:00" });

  it("open() sets isOpen to true and initializes draft from factory", () => {
    const { isOpen, draft, open } = useInlineEditor(factory);
    expect(isOpen.value).toBe(false);
    open();
    expect(isOpen.value).toBe(true);
    expect(draft.value).toEqual({ name: "default", pace: "5:00" });
  });

  it("open(draft) uses provided draft instead of factory", () => {
    const { draft, open } = useInlineEditor(factory);
    open({ name: "custom", pace: "4:30" });
    expect(draft.value).toEqual({ name: "custom", pace: "4:30" });
  });

  it("open() clears errorMessage", () => {
    const { errorMessage, open } = useInlineEditor(factory);
    errorMessage.value = "something went wrong";
    open();
    expect(errorMessage.value).toBe("");
  });

  it("close() sets isOpen to false", () => {
    const { isOpen, open, close } = useInlineEditor(factory);
    open();
    expect(isOpen.value).toBe(true);
    close();
    expect(isOpen.value).toBe(false);
  });

  it("close() clears errorMessage", () => {
    const { errorMessage, open, close } = useInlineEditor(factory);
    open();
    errorMessage.value = "save failed";
    close();
    expect(errorMessage.value).toBe("");
  });

  it("canInteract is true when not saving", () => {
    const { canInteract } = useInlineEditor(factory);
    expect(canInteract.value).toBe(true);
  });

  it("canInteract is false when isSaving is true", () => {
    const { canInteract, isSaving } = useInlineEditor(factory);
    isSaving.value = true;
    expect(canInteract.value).toBe(false);
  });

  it("canInteract restores to true after isSaving is set back to false", () => {
    const { canInteract, isSaving } = useInlineEditor(factory);
    isSaving.value = true;
    expect(canInteract.value).toBe(false);
    isSaving.value = false;
    expect(canInteract.value).toBe(true);
  });

  it("errorMessage can be set externally", () => {
    const { errorMessage } = useInlineEditor(factory);
    errorMessage.value = "network error";
    expect(errorMessage.value).toBe("network error");
  });

  it("open() without args re-calls factory for a fresh draft each time", () => {
    let callCount = 0;
    const trackingFactory = () => {
      callCount++;
      return { name: `draft-${callCount}`, pace: "5:00" };
    };
    const { draft, open } = useInlineEditor(trackingFactory);

    open();
    expect(draft.value.name).toBe("draft-2"); // factory() called once in setup, once in open()
    open();
    expect(draft.value.name).toBe("draft-3");
    expect(callCount).toBe(3);
  });
});
