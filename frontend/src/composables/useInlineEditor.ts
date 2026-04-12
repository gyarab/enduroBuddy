import { computed, ref } from "vue";

type DraftShape = Record<string, string>;

export function useInlineEditor<TDraft extends DraftShape>(factory: () => TDraft) {
  const isOpen = ref(false);
  const isSaving = ref(false);
  const errorMessage = ref("");
  const draft = ref<TDraft>(factory());

  function open(nextDraft?: TDraft) {
    draft.value = nextDraft ?? factory();
    errorMessage.value = "";
    isOpen.value = true;
  }

  function close() {
    isOpen.value = false;
    errorMessage.value = "";
  }

  const canInteract = computed(() => !isSaving.value);

  return {
    canInteract,
    close,
    draft,
    errorMessage,
    isOpen,
    isSaving,
    open,
  };
}
