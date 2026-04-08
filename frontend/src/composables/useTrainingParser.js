import { computed, ref, watch } from "vue";
import { parseTrainingPreview } from "@/utils/trainingPreview";
export function useTrainingParser(source) {
    const rawText = ref(source.value);
    watch(() => source.value, (value) => {
        rawText.value = value;
    });
    const preview = computed(() => parseTrainingPreview(rawText.value));
    return {
        preview,
    };
}
