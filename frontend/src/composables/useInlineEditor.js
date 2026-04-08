import { computed, ref } from "vue";
export function useInlineEditor(factory) {
    const isOpen = ref(false);
    const isSaving = ref(false);
    const errorMessage = ref("");
    const draft = ref(factory());
    function open(nextDraft) {
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
