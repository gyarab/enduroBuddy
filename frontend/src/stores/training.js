import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { addSecondPhaseTraining, fetchDashboard, removeSecondPhaseTraining, updateCompletedTraining, updatePlannedTraining, } from "@/api/training";
import { useToastStore } from "@/stores/toasts";
import { parseTrainingPreview } from "@/utils/trainingPreview";
export const useTrainingStore = defineStore("training", () => {
    const dashboard = ref(null);
    const isLoading = ref(false);
    const errorMessage = ref("");
    const isRefreshing = ref(false);
    const toastStore = useToastStore();
    const selectedMonth = computed(() => dashboard.value?.selected_month ?? null);
    const weeks = computed(() => dashboard.value?.weeks ?? []);
    const summary = computed(() => dashboard.value?.summary ?? null);
    const navigation = computed(() => dashboard.value?.navigation ?? null);
    const hasData = computed(() => weeks.value.length > 0);
    const selectedMonthValue = computed(() => selectedMonth.value?.value || undefined);
    function formatFixed(value, decimals, useCommaDecimal) {
        const formatted = value.toFixed(decimals);
        return useCommaDecimal ? formatted.replace(".", ",") : formatted;
    }
    function formatPlannedWeekLabel(totalKm, previousLabel) {
        const useCommaDecimal = previousLabel.includes(",");
        const suffix = previousLabel.includes("km/t") ? "km/t\u00fdden" : "km/week";
        return `${formatFixed(totalKm, 1, useCommaDecimal)} ${suffix}`;
    }
    function formatCompletedKm(totalKm, previousValue) {
        const useCommaDecimal = previousValue.includes(",");
        return totalKm > 0 ? formatFixed(totalKm, 2, useCommaDecimal) : "-";
    }
    function isSubstantivePlannedRow(row) {
        return Boolean((row.title && row.title !== "-")
            || row.notes.trim()
            || (row.planned_metrics?.planned_km_value || 0) > 0);
    }
    function isSubstantiveCompletedRow(row) {
        return Boolean(row.completed_metrics?.km?.trim()
            || row.completed_metrics?.minutes?.trim()
            || row.completed_metrics?.details?.trim()
            || row.completed_metrics?.avg_hr !== null
            || row.completed_metrics?.max_hr !== null
            || row.has_linked_activity);
    }
    function recomputeCompletedTotals(week) {
        let totalKm = 0;
        let totalMinutes = 0;
        let hrNum = 0;
        let hrDen = 0;
        let maxHr = null;
        for (const row of week.completed_rows) {
            const metrics = row.completed_metrics;
            if (!metrics) {
                continue;
            }
            const km = Number.parseFloat((metrics.km || "").replace(",", "."));
            const minutes = Number.parseInt(metrics.minutes || "", 10);
            if (Number.isFinite(km)) {
                totalKm += km;
            }
            if (Number.isFinite(minutes)) {
                totalMinutes += minutes;
            }
            if (metrics.avg_hr !== null && Number.isFinite(minutes) && minutes > 0) {
                hrNum += metrics.avg_hr * minutes;
                hrDen += minutes;
            }
            if (metrics.max_hr !== null) {
                maxHr = maxHr === null ? metrics.max_hr : Math.max(maxHr, metrics.max_hr);
            }
        }
        week.completed_total = {
            km: formatCompletedKm(totalKm, week.completed_total.km),
            time: totalMinutes > 0 ? String(totalMinutes) : "-",
            avg_hr: hrDen > 0 ? Math.round(hrNum / hrDen) : null,
            max_hr: maxHr,
        };
    }
    function recomputePlannedWeekTotals(week) {
        const totalKm = week.planned_rows.reduce((sum, row) => sum + (row.planned_metrics?.planned_km_value || 0), 0);
        week.planned_total_km_text = formatPlannedWeekLabel(totalKm, week.planned_total_km_text);
    }
    function recomputeSummary() {
        if (!dashboard.value) {
            return;
        }
        let plannedSessions = 0;
        let completedSessions = 0;
        let plannedKm = 0;
        let completedKm = 0;
        let completedMinutes = 0;
        for (const week of dashboard.value.weeks) {
            for (const row of week.planned_rows) {
                if (isSubstantivePlannedRow(row)) {
                    plannedSessions += 1;
                    plannedKm += row.planned_metrics?.planned_km_value || 0;
                }
            }
            for (const row of week.completed_rows) {
                if (isSubstantiveCompletedRow(row)) {
                    completedSessions += 1;
                }
            }
            const weekKm = Number.parseFloat((week.completed_total.km || "").replace(",", "."));
            const weekMinutes = Number.parseInt(week.completed_total.time || "", 10);
            if (Number.isFinite(weekKm)) {
                completedKm += weekKm;
            }
            if (Number.isFinite(weekMinutes)) {
                completedMinutes += weekMinutes;
            }
        }
        dashboard.value.summary = {
            planned_sessions: plannedSessions,
            completed_sessions: completedSessions,
            planned_km: Math.round(plannedKm * 10) / 10,
            completed_km: Math.round(completedKm * 10) / 10,
            completed_minutes: completedMinutes,
            completion_rate: plannedSessions > 0 ? Math.round((completedSessions / plannedSessions) * 100) : 0,
        };
    }
    function patchPlannedRow(plannedId, payload) {
        if (!dashboard.value) {
            return;
        }
        for (const week of dashboard.value.weeks) {
            const row = week.planned_rows.find((candidate) => candidate.id === plannedId);
            if (!row) {
                continue;
            }
            if (payload.field === "title") {
                row.title = payload.value.trim() || "-";
                const preview = parseTrainingPreview(payload.value);
                row.planned_metrics = {
                    planned_km_value: preview.totalKm,
                    planned_km_text: preview.kmText,
                    planned_km_confidence: preview.confidence,
                };
            }
            if (payload.field === "notes") {
                row.notes = payload.value.trim();
            }
            if (payload.field === "session_type") {
                row.session_type = payload.value === "WORKOUT" ? "WORKOUT" : "RUN";
            }
            row.status = isSubstantivePlannedRow(row) ? "planned" : "rest";
            recomputePlannedWeekTotals(week);
            break;
        }
        recomputeSummary();
    }
    function patchCompletedRow(plannedId, payload) {
        if (!dashboard.value) {
            return;
        }
        for (const week of dashboard.value.weeks) {
            const row = week.completed_rows.find((candidate) => candidate.id === plannedId);
            if (!row || !row.completed_metrics) {
                continue;
            }
            if (payload.field === "km") {
                row.completed_metrics.km = payload.value;
            }
            if (payload.field === "min") {
                row.completed_metrics.minutes = payload.value;
            }
            if (payload.field === "third") {
                row.completed_metrics.details = payload.value;
                row.notes = payload.value;
            }
            if (payload.field === "avg_hr") {
                row.completed_metrics.avg_hr = payload.value ? Number.parseInt(payload.value, 10) : null;
            }
            if (payload.field === "max_hr") {
                row.completed_metrics.max_hr = payload.value ? Number.parseInt(payload.value, 10) : null;
            }
            row.status = isSubstantiveCompletedRow(row) ? "done" : "missed";
            recomputeCompletedTotals(week);
            break;
        }
        recomputeSummary();
    }
    async function loadDashboard(month, options) {
        const silent = options?.silent === true;
        if (silent) {
            isRefreshing.value = true;
        }
        else {
            isLoading.value = true;
        }
        errorMessage.value = "";
        try {
            dashboard.value = await fetchDashboard(month);
        }
        catch (error) {
            errorMessage.value = error instanceof Error ? error.message : "Nepodarilo se nacist dashboard.";
        }
        finally {
            if (silent) {
                isRefreshing.value = false;
            }
            else {
                isLoading.value = false;
            }
        }
    }
    async function goToPreviousMonth() {
        const target = navigation.value?.previous?.value;
        if (!target) {
            return;
        }
        await loadDashboard(target);
    }
    async function goToNextMonth() {
        const target = navigation.value?.next?.value;
        if (!target) {
            return;
        }
        await loadDashboard(target);
    }
    async function savePlannedField(plannedId, payload) {
        await updatePlannedTraining(plannedId, payload);
        patchPlannedRow(plannedId, payload);
        toastStore.push("Plan saved.", "success");
    }
    async function savePlannedDraft(plannedId, updates) {
        for (const update of updates) {
            await updatePlannedTraining(plannedId, update);
            patchPlannedRow(plannedId, update);
        }
        toastStore.push("Planned training updated.", "success");
    }
    async function saveCompletedDraft(plannedId, updates) {
        for (const update of updates) {
            await updateCompletedTraining(plannedId, update);
            patchCompletedRow(plannedId, update);
        }
        toastStore.push("Completed training updated.", "success");
    }
    async function addSecondPhase(plannedId) {
        await addSecondPhaseTraining(plannedId);
        await loadDashboard(selectedMonthValue.value, { silent: true });
        toastStore.push("Second phase added.", "success");
    }
    async function removeSecondPhase(plannedId) {
        await removeSecondPhaseTraining(plannedId);
        await loadDashboard(selectedMonthValue.value, { silent: true });
        toastStore.push("Second phase removed.", "success");
    }
    return {
        addSecondPhase,
        dashboard,
        errorMessage,
        goToNextMonth,
        goToPreviousMonth,
        hasData,
        isLoading,
        isRefreshing,
        loadDashboard,
        navigation,
        removeSecondPhase,
        saveCompletedDraft,
        savePlannedDraft,
        savePlannedField,
        selectedMonth,
        selectedMonthValue,
        summary,
        weeks,
    };
});
