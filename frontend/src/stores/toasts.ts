import { ref } from "vue";
import { defineStore } from "pinia";

type ToastTone = "success" | "info" | "warning" | "danger";

export type ToastItem = {
  id: number;
  message: string;
  tone: ToastTone;
};

export const useToastStore = defineStore("toasts", () => {
  const items = ref<ToastItem[]>([]);
  let nextId = 1;

  function push(message: string, tone: ToastTone = "info") {
    const id = nextId++;
    items.value.push({ id, message, tone });
    setTimeout(() => remove(id), 3200);
  }

  function remove(id: number) {
    items.value = items.value.filter((item) => item.id !== id);
  }

  return {
    items,
    push,
    remove,
  };
});
