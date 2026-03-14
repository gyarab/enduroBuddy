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
    COACH_CANNOT_EDIT_MANAGED_COMPLETED = "Trenér nemůže upravovat completed trénink svěřence."
    GARMIN_NOT_CONNECTED = "Garmin účet není připojen."
    INVALID_WEEK_START = "Neplatný začátek týdne."
    GARMIN_WEEK_UNAVAILABLE = "Garmin import týdne je dostupný až od začátku týdne."
    GARMIN_SYNC_START_FAILED = "Synchronizaci se nepodařilo spustit."
    GARMIN_SYNC_FAILED = "Garmin sync failed."
    JOB_NOT_FOUND = "Job nenalezen."


class DashboardText:
    ADMIN_ONLY_REMOVE_WEEK = "remove_week_completed je povolený jen pro uživatele admin."
    REMOVE_WEEK_USAGE = "Použij remove_week_completed=3/1 nebo remove_week_completed=2026/3/1."
    ADMIN_USER_NOT_FOUND = "Uživatel admin nebyl nalezen."
    ADMIN_ONLY_TEST_IMPORT = "test_garmin_import je povolený jen pro uživatele admin."

    @staticmethod
    def week_not_found(*, year: int, month: int, week_index: int) -> str:
        return f"Týden {week_index} v {month}/{year} nebyl nalezen."

    @staticmethod
    def removed_admin_week(*, year: int, month: int, week_index: int, completed_count: int, activity_count: int) -> str:
        return (
            f"Vymazáno Splněno pro admin {month}/{year}, týden {week_index}: "
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
            f"Týden znovu vytvořen (index {recreated_week_index}, dnů {recreated_days_count})."
        )

    @staticmethod
    def garmin_week_synced(*, replaced: int, untouched: int) -> str:
        return f"Garmin týden synchronizován. Přepsáno: {replaced}, ponecháno: {untouched}."


class HomeText:
    COACH_CODE_NOT_FOUND = "Kód trenéra nebyl nalezen."
    OWN_COACH_CODE = "Nemůžeš zadat vlastní kód trenéra."
    ALREADY_ASSIGNED_TO_COACH = "Už jsi u tohoto trenéra přiřazený."
    JOIN_REQUEST_ALREADY_PENDING = "Požadavek už čeká na schválení."
    JOIN_REQUEST_SENT = "Požadavek byl odeslán trenérovi ke schválení."
    GARMIN_EMAIL_PASSWORD_REQUIRED = "Enter Garmin email and password."
    GARMIN_ACCOUNT_CONNECTED = "Garmin account connected."
    GARMIN_ACCOUNT_DISCONNECTED = "Garmin account disconnected."
    GARMIN_ACCOUNT_NOT_CONNECTED = "Garmin account is not connected."
    GARMIN_SYNC_QUEUED = "Garmin sync queued."
    GARMIN_SYNC_ALREADY_RUNNING = "Garmin sync už běží."
    GARMIN_SYNC_FAILED = "Garmin sync failed."
    FIT_FILE_REQUIRED = "Please select a FIT file."
    FIT_IMPORT_QUEUED = "FIT import queued."
    FIT_FILE_IMPORTED = "FIT file imported."
    FIT_FILE_ALREADY_IMPORTED = "This FIT file is already imported."
    FIT_IMPORT_FAILED = "FIT import failed."

    @staticmethod
    def month_created(*, weeks_created: int, days_created: int) -> str:
        return f"Přidán nový měsíc: týdny {weeks_created}, dny {days_created}."

    @staticmethod
    def month_extended(*, weeks_created: int, days_created: int) -> str:
        return f"Měsíc už existoval, doplněno: týdny {weeks_created}, dny {days_created}."

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
    DEFAULT_GROUP_NAME = "Moji svěřenci"
    DEFAULT_GROUP_DESCRIPTION = "Výchozí skupina pro pozvánky."
    INVALID_REQUEST = "Neplatný požadavek."
    REQUEST_NOT_FOUND = "Požadavek nebyl nalezen nebo už byl vyřízen."
    REQUEST_APPROVED = "Žádost byla schválena."
    REQUEST_REJECTED = "Žádost byla zamítnuta."
    INVALID_ATHLETE = "Neplatný atlet."
    CANNOT_REMOVE_OWN_PLAN = "Nelze odebrat vlastní plán."
    ATHLETE_NOT_FOUND = "Atlet nebyl nalezen."
    CONFIRM_NAME_MISMATCH = "Potvrzovací jméno nesouhlasí."
    ATHLETE_REMOVED = "Svěřenec byl odebrán."
    SETTINGS_SAVED = "Nastavení bylo uloženo."
    CANNOT_HIDE_OWN_PLAN = "Nelze skrýt vlastní plán."
    INVITE_CREATED = "Pozvánka byla vytvořena."
    INVALID_ATHLETE_SELECTION = "Neplatný výběr atleta."

    @staticmethod
    def month_created(*, weeks_created: int, days_created: int) -> str:
        return f"Přidán nový měsíc: týdny {weeks_created}, dny {days_created}."

    @staticmethod
    def month_extended(*, weeks_created: int, days_created: int) -> str:
        return f"Měsíc už existoval, doplněno: týdny {weeks_created}, dny {days_created}."

    @staticmethod
    def bulk_month_created(*, created_months: int, created_weeks: int, created_days: int) -> str:
        return f"Hromadně vytvořeno: měsíce {created_months}, týdny {created_weeks}, dny {created_days}."

    @staticmethod
    def bulk_specific_month_created(*, label: str, created_months: int, created_weeks: int, created_days: int) -> str:
        return f"Hromadně doplněn {label}: svěřenci {created_months}, týdny {created_weeks}, dny {created_days}."

    @staticmethod
    def bulk_specific_month_already_exists(*, label: str) -> str:
        return f"Všichni svěřenci už mají {label} vytvořený."


class ProfileText:
    PROFILE_SAVED = "Profil byl uložen."
    OLD_PASSWORD_INVALID = "Staré heslo není správně."
    PASSWORD_CONFIRM_MISMATCH = "Nové heslo a potvrzení se neshodují."
    PASSWORD_CHANGED = "Heslo bylo změněno."
    UNKNOWN_ACTION = "Neznámý požadavek."


class InviteText:
    INVITE_NOT_FOUND = "Pozvanka neexistuje."
    INVITE_ALREADY_USED = "Pozvánka už byla použita."
    INVITE_EXPIRED = "Pozvánka už vypršela."
    COACH_CANNOT_ACCEPT_OWN_INVITE = "Trenér nemůže přijmout vlastní pozvánku."
    INVITE_ACCEPTED = "Byl/a jsi přidán/a do tréninkové skupiny."
