from __future__ import annotations


class ApiText:
    METHOD_NOT_ALLOWED = "Method not allowed."
    INVALID_JSON_BODY = "Invalid JSON body."
    INVALID_PLANNED_ID = "Invalid planned_id."
    INVALID_FIELD = "Invalid field."
    INVALID_VALUE = "Invalid value."
    INVALID_SESSION_TYPE = "Invalid session_type value."
    PLANNED_TRAINING_NOT_FOUND = "Planned training not found."
    FORBIDDEN_FOR_ATHLETE = "Forbidden for this athlete."
    COACH_ACCESS_ONLY = "Coach access only."
    INVALID_ATHLETE_ID = "Invalid athlete_id."
    INVALID_FOCUS_VALUE = "Invalid focus value."
    ATHLETE_LINK_NOT_FOUND = "Athlete link not found."
    ATHLETE_IDS_MUST_BE_INT_LIST = "athlete_ids must be a list of integers."
    DUPLICATE_ATHLETE_IDS = "Duplicate athlete ids are not allowed."
    UNLINKED_ATHLETE_IDS = "One or more athletes are not linked to this coach."
    COACH_CANNOT_EDIT_MANAGED_COMPLETED = "Trainer nemuze upravovat completed training sverence."
    GARMIN_NOT_CONNECTED = "Garmin ucet neni pripojen."
    INVALID_WEEK_START = "Neplatny zacatek tydne."
    GARMIN_WEEK_UNAVAILABLE = "Garmin import tydne je dostupny az od zacatku tydne."
    GARMIN_SYNC_START_FAILED = "Synchronizaci se nepodarilo spustit."
    GARMIN_SYNC_FAILED = "Garmin sync failed."
    JOB_NOT_FOUND = "Job nenalezen."


class DashboardText:
    ADMIN_ONLY_REMOVE_WEEK = "remove_week_completed je povoleny jen pro uzivatele admin."
    REMOVE_WEEK_USAGE = "Pouzij remove_week_completed=3/1 nebo remove_week_completed=2026/3/1."
    ADMIN_USER_NOT_FOUND = "Uzivatel admin nebyl nalezen."
    ADMIN_ONLY_TEST_IMPORT = "test_garmin_import je povoleny jen pro uzivatele admin."

    @staticmethod
    def week_not_found(*, year: int, month: int, week_index: int) -> str:
        return f"Tyden {week_index} v {month}/{year} nebyl nalezen."

    @staticmethod
    def removed_admin_week(*, year: int, month: int, week_index: int, completed_count: int, activity_count: int) -> str:
        return (
            f"Vymazano Splneno pro admin {month}/{year}, tyden {week_index}: "
            f"completed {completed_count}, activity {activity_count}."
        )

    @staticmethod
    def test_cleanup_done(
        *,
        from_day,
        to_day,
        deleted_planned_count: int,
        deleted_activity_count: int,
        deleted_ledger_count: int,
        recreated_week_index: int,
        recreated_days_count: int,
    ) -> str:
        return (
            f"Test cleanup hotov ({from_day:%d.%m.%Y} - {to_day:%d.%m.%Y}): "
            f"planned/completed {deleted_planned_count}, activity {deleted_activity_count}, ledger {deleted_ledger_count}. "
            f"Tyden znovu vytvoren (index {recreated_week_index}, dnu {recreated_days_count})."
        )

    @staticmethod
    def garmin_week_synced(*, replaced: int, untouched: int) -> str:
        return f"Garmin tyden synchronizovan. Prepsano: {replaced}, ponechano: {untouched}."


class HomeText:
    COACH_CODE_NOT_FOUND = "Kod trenera nebyl nalezen."
    OWN_COACH_CODE = "Nemuzes zadat vlastni kod trenera."
    ALREADY_ASSIGNED_TO_COACH = "Uz jsi u tohoto trenera prirazeny."
    JOIN_REQUEST_ALREADY_PENDING = "Pozadavek uz ceka na schvaleni."
    JOIN_REQUEST_SENT = "Pozadavek byl odeslan trenerovi ke schvaleni."
    GARMIN_EMAIL_PASSWORD_REQUIRED = "Enter Garmin email and password."
    GARMIN_ACCOUNT_CONNECTED = "Garmin account connected."
    GARMIN_ACCOUNT_DISCONNECTED = "Garmin account disconnected."
    GARMIN_ACCOUNT_NOT_CONNECTED = "Garmin account is not connected."
    GARMIN_SYNC_QUEUED = "Garmin sync queued."
    GARMIN_SYNC_ALREADY_RUNNING = "Garmin sync uz bezi."
    GARMIN_SYNC_FAILED = "Garmin sync failed."
    FIT_FILE_REQUIRED = "Please select a FIT file."
    FIT_IMPORT_QUEUED = "FIT import queued."
    FIT_FILE_IMPORTED = "FIT file imported."
    FIT_FILE_ALREADY_IMPORTED = "This FIT file is already imported."
    FIT_IMPORT_FAILED = "FIT import failed."

    @staticmethod
    def month_created(*, weeks_created: int, days_created: int) -> str:
        return f"Pridan novy mesic: tydny {weeks_created}, dny {days_created}."

    @staticmethod
    def month_extended(*, weeks_created: int, days_created: int) -> str:
        return f"Mesic uz existoval, doplneno: tydny {weeks_created}, dny {days_created}."

    @staticmethod
    def garmin_connect_failed(exc: Exception) -> str:
        return f"Garmin connect failed: {exc}"

    @staticmethod
    def garmin_sync_failed(exc: Exception) -> str:
        return f"Garmin sync failed: {exc}"

    @staticmethod
    def garmin_sync_finished(*, imported: int, skipped: int) -> str:
        return f"Garmin sync finished. Imported: {imported}, skipped duplicates: {skipped}."

    @staticmethod
    def fit_import_failed(exc: Exception) -> str:
        return f"FIT import failed: {exc}"


class CoachText:
    DEFAULT_GROUP_NAME = "Moji sverenci"
    DEFAULT_GROUP_DESCRIPTION = "Vychozi skupina pro pozvanky."
    INVALID_REQUEST = "Neplatny pozadavek."
    REQUEST_NOT_FOUND = "Pozadavek nebyl nalezen nebo uz byl vyrizen."
    REQUEST_APPROVED = "Zadost byla schvalena."
    REQUEST_REJECTED = "Zadost byla zamitnuta."
    INVALID_ATHLETE = "Neplatny atlet."
    CANNOT_REMOVE_OWN_PLAN = "Nelze odebrat vlastni plan."
    ATHLETE_NOT_FOUND = "Atlet nebyl nalezen."
    CONFIRM_NAME_MISMATCH = "Potvrzovaci jmeno nesouhlasi."
    ATHLETE_REMOVED = "Sverenec byl odebran."
    SETTINGS_SAVED = "Nastaveni bylo ulozeno."
    CANNOT_HIDE_OWN_PLAN = "Nelze skryt vlastni plan."
    INVITE_CREATED = "Pozvanka byla vytvorena."
    INVALID_ATHLETE_SELECTION = "Neplatny vyber atleta."

    @staticmethod
    def month_created(*, weeks_created: int, days_created: int) -> str:
        return f"Pridan novy mesic: tydny {weeks_created}, dny {days_created}."

    @staticmethod
    def month_extended(*, weeks_created: int, days_created: int) -> str:
        return f"Mesic uz existoval, doplneno: tydny {weeks_created}, dny {days_created}."

    @staticmethod
    def bulk_month_created(*, created_months: int, created_weeks: int, created_days: int) -> str:
        return f"Hromadne vytvoreno: mesice {created_months}, tydny {created_weeks}, dny {created_days}."


class ProfileText:
    PROFILE_SAVED = "Profil byl ulozen."
    OLD_PASSWORD_INVALID = "Stare heslo neni spravne."
    PASSWORD_CONFIRM_MISMATCH = "Nove heslo a potvrzeni se neshoduji."
    PASSWORD_CHANGED = "Heslo bylo zmeneno."
    UNKNOWN_ACTION = "Neznamy pozadavek."


class InviteText:
    INVITE_NOT_FOUND = "Pozvanka neexistuje."
    INVITE_ALREADY_USED = "Pozvanka uz byla pouzita."
    INVITE_EXPIRED = "Pozvanka uz vyprsela."
    COACH_CANNOT_ACCEPT_OWN_INVITE = "Trener nemuze prijmout vlastni pozvanku."
    INVITE_ACCEPTED = "Byl/a jsi pridan/a do treninkove skupiny."
