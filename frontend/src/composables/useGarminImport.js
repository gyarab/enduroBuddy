import { computed, onBeforeUnmount, ref } from "vue";
import { connectGarmin, fetchImportJobStatus, revokeGarmin, startGarminSync, uploadFitFile, } from "@/api/imports";
export function useGarminImport(source) {
    const isOpen = ref(false);
    const isBusy = ref(false);
    const errorMessage = ref("");
    const statusMessage = ref("");
    const job = ref(null);
    const selectedRange = ref("last_30_days");
    const garminEmail = ref("");
    const garminPassword = ref("");
    const connected = ref(Boolean(source.value?.has_garmin_connection));
    const connectionLabel = ref("");
    let pollTimer = null;
    const canConnect = computed(() => Boolean(source.value?.garmin_connect_enabled));
    const canSync = computed(() => Boolean(source.value?.garmin_sync_enabled));
    function open() {
        isOpen.value = true;
        connected.value = Boolean(source.value?.has_garmin_connection);
        errorMessage.value = "";
    }
    function close() {
        isOpen.value = false;
    }
    function stopPolling() {
        if (pollTimer !== null) {
            window.clearInterval(pollTimer);
            pollTimer = null;
        }
    }
    async function pollJob(jobId) {
        const payload = await fetchImportJobStatus(jobId);
        job.value = payload.job;
        statusMessage.value = payload.job.message;
        if (payload.job.done) {
            stopPolling();
        }
        return payload.job;
    }
    function startPolling(jobId) {
        stopPolling();
        pollTimer = window.setInterval(() => {
            void pollJob(jobId);
        }, 2000);
    }
    async function connect() {
        isBusy.value = true;
        errorMessage.value = "";
        try {
            const payload = await connectGarmin(garminEmail.value.trim(), garminPassword.value);
            connected.value = payload.connection.connected;
            connectionLabel.value = payload.connection.display_name;
            statusMessage.value = payload.message;
            garminPassword.value = "";
            return payload.connection;
        }
        catch (error) {
            errorMessage.value = error instanceof Error ? error.message : "Garmin connect failed.";
            throw error;
        }
        finally {
            isBusy.value = false;
        }
    }
    async function disconnect() {
        isBusy.value = true;
        errorMessage.value = "";
        try {
            const payload = await revokeGarmin();
            connected.value = payload.connection.connected;
            connectionLabel.value = payload.connection.display_name;
            statusMessage.value = payload.message;
            return payload.connection;
        }
        catch (error) {
            errorMessage.value = error instanceof Error ? error.message : "Garmin disconnect failed.";
            throw error;
        }
        finally {
            isBusy.value = false;
        }
    }
    async function sync() {
        isBusy.value = true;
        errorMessage.value = "";
        try {
            const payload = await startGarminSync(selectedRange.value);
            job.value = payload.job;
            statusMessage.value = payload.message;
            startPolling(payload.job.id);
            await pollJob(payload.job.id);
            return payload.job;
        }
        catch (error) {
            errorMessage.value = error instanceof Error ? error.message : "Garmin sync failed.";
            throw error;
        }
        finally {
            isBusy.value = false;
        }
    }
    async function upload(file) {
        isBusy.value = true;
        errorMessage.value = "";
        try {
            const payload = await uploadFitFile(file);
            statusMessage.value = payload.message;
            return payload;
        }
        catch (error) {
            errorMessage.value = error instanceof Error ? error.message : "FIT import failed.";
            throw error;
        }
        finally {
            isBusy.value = false;
        }
    }
    onBeforeUnmount(() => {
        stopPolling();
    });
    return {
        canConnect,
        canSync,
        close,
        connect,
        connected,
        connectionLabel,
        disconnect,
        errorMessage,
        garminEmail,
        garminPassword,
        isBusy,
        isOpen,
        job,
        open,
        pollJob,
        selectedRange,
        statusMessage,
        stopPolling,
        sync,
        upload,
    };
}
