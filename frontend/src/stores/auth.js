import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { fetchCurrentUser } from "@/api/auth";
export const useAuthStore = defineStore("auth", () => {
    const user = ref(null);
    const isLoading = ref(false);
    const errorMessage = ref("");
    const hasBootstrapped = ref(false);
    const isAuthenticated = computed(() => user.value !== null);
    const isCoach = computed(() => user.value?.role === "COACH");
    async function initialize() {
        isLoading.value = true;
        errorMessage.value = "";
        try {
            user.value = await fetchCurrentUser();
        }
        catch (error) {
            user.value = null;
            errorMessage.value = error instanceof Error ? error.message : "Nepodarilo se nacist uzivatele.";
        }
        finally {
            isLoading.value = false;
            hasBootstrapped.value = true;
        }
    }
    return {
        errorMessage,
        hasBootstrapped,
        initialize,
        isAuthenticated,
        isCoach,
        isLoading,
        user,
    };
});
