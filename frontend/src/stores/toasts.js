import { ref } from "vue";
import { defineStore } from "pinia";
export const useToastStore = defineStore("toasts", () => {
    const items = ref([]);
    let nextId = 1;
    function push(message, tone = "info") {
        const id = nextId++;
        items.value.push({ id, message, tone });
        setTimeout(() => remove(id), 3200);
    }
    function remove(id) {
        items.value = items.value.filter((item) => item.id !== id);
    }
    return {
        items,
        push,
        remove,
    };
});
