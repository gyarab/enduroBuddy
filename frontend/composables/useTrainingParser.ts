import { computed, ref, watch } from "vue";

import { parseTrainingPreview, type ParsedTrainingPreview } from "@/utils/trainingPreview";

export function useTrainingParser(source: { value: string }) {
  const rawText = ref(source.value);

  watch(
    () => source.value,
    (value) => {
      rawText.value = value;
    },
  );

  const preview = computed<ParsedTrainingPreview>(() => parseTrainingPreview(rawText.value));

  return {
    preview,
  };
}
