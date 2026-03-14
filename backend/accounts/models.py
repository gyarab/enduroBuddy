from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.constraints import UniqueConstraint
from django.dispatch import receiver
from django.db.models.signals import post_save
import secrets
import string

class Role(models.TextChoices):
        COACH = 'COACH', 'Coach'
        ATHLETE = 'ATHLETE', 'Athlete'

class Profile(models.Model):
        user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
        role = models.CharField(max_length=20, choices=Role.choices, default=Role.ATHLETE)
        coach_join_code = models.CharField(max_length=12, unique=True, null=True, blank=True, db_index=True)
        legend_state = models.JSONField(default=dict, blank=True)

        def __str__(self):
            return f"{self.user.username} ({self.role})"

        def ensure_coach_join_code(self) -> str:
            if self.coach_join_code and len(self.coach_join_code) >= 12:
                return self.coach_join_code
            alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
            for _ in range(20):
                code = "".join(secrets.choice(alphabet) for _ in range(12))
                if not Profile.objects.filter(coach_join_code=code).exists():
                    self.coach_join_code = code
                    self.save(update_fields=["coach_join_code"])
                    return code
            code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            self.coach_join_code = code
            self.save(update_fields=["coach_join_code"])
            return code

class CoachAthlete(models.Model):
    coach = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coached_athletes')
    athlete = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='athlete_coaches')
    focus = models.CharField(max_length=30, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    hidden_from_plans = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Coach-Athlete link"
        verbose_name_plural = "Coach-Athlete links"
        constraints = [
            UniqueConstraint(fields=["coach", "athlete"], name="uniq_coach_athlete_pair"), models.CheckConstraint(check=~Q(coach=models.F("athlete")),name="coach_cannot_be_same_as_athlete",),
        ]

    def __str__(self) -> str:
        return f"{self.coach.username} -> {self.athlete.username}"


class TrainingGroup(models.Model):
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="training_groups",
    )
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            UniqueConstraint(fields=["coach", "name"], name="uniq_training_group_name_per_coach"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.coach.username})"


class TrainingGroupAthlete(models.Model):
    group = models.ForeignKey(
        TrainingGroup,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="training_group_memberships",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["group_id", "athlete_id"]
        constraints = [
            UniqueConstraint(fields=["group", "athlete"], name="uniq_training_group_member"),
        ]

    def __str__(self) -> str:
        return f"{self.group.name}: {self.athlete.username}"


class TrainingGroupInvite(models.Model):
    group = models.ForeignKey(
        TrainingGroup,
        on_delete=models.CASCADE,
        related_name="invites",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_training_group_invites",
    )
    token = models.CharField(max_length=128, unique=True, db_index=True)
    invited_email = models.EmailField(blank=True, default="")
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="used_training_group_invites",
    )

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Invite {self.group.name} ({self.token[:8]})"


class CoachJoinRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="incoming_coach_join_requests",
    )
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="outgoing_coach_join_requests",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(check=~Q(coach=models.F("athlete")), name="coach_join_request_no_self"),
            UniqueConstraint(
                fields=["coach", "athlete", "status"],
                condition=Q(status="PENDING"),
                name="uniq_pending_coach_join_request",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.athlete.username} -> {self.coach.username} ({self.status})"


class AppNotification(models.Model):
    class Kind(models.TextChoices):
        COACH_JOIN_REQUEST = "COACH_JOIN_REQUEST", "Coach join request"
        PLAN_UPDATED = "PLAN_UPDATED", "Plan updated"
        COACH_NOTE = "COACH_NOTE", "Coach note"

    class Tone(models.TextChoices):
        SUCCESS = "success", "Success"
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        DANGER = "danger", "Danger"
        SECONDARY = "secondary", "Secondary"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="app_notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_app_notifications",
    )
    kind = models.CharField(max_length=40, choices=Kind.choices, db_index=True)
    tone = models.CharField(max_length=16, choices=Tone.choices, default=Tone.INFO)
    text = models.CharField(max_length=255)
    dedupe_key = models.CharField(max_length=120, blank=True, default="", db_index=True)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["recipient", "read_at", "-created_at"], name="appnotif_rec_read_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.recipient} | {self.kind} | {self.text[:40]}"


class GarminConnection(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="garmin_connection",
    )
    garmin_email = models.EmailField(blank=True, default="")
    garmin_display_name = models.CharField(max_length=128, blank=True, default="")
    encrypted_tokenstore = models.TextField(blank=True, default="")
    kms_key_id = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} | Garmin active={self.is_active}"


class GarminSyncAudit(models.Model):
    class Action(models.TextChoices):
        CONNECT = "CONNECT", "Connect"
        SYNC = "SYNC", "Sync"
        REVOKE = "REVOKE", "Revoke"

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        ERROR = "ERROR", "Error"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="garmin_sync_audits",
    )
    connection = models.ForeignKey(
        GarminConnection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audits",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    window = models.CharField(max_length=20, blank=True, default="")
    imported_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    message = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.user} | {self.action} | {self.status}"


class ImportJob(models.Model):
    class Kind(models.TextChoices):
        GARMIN_SYNC = "GARMIN_SYNC", "Garmin sync"

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        ERROR = "ERROR", "Error"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="import_jobs",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True)
    window = models.CharField(max_length=20, blank=True, default="")
    total_count = models.PositiveIntegerField(default=0)
    processed_count = models.PositiveIntegerField(default=0)
    imported_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    message = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            UniqueConstraint(
                fields=["user", "kind"],
                condition=Q(status__in=["QUEUED", "RUNNING"]),
                name="uniq_active_import_job_per_user_kind",
            ),
        ]

    def __str__(self):
        return f"{self.user} | {self.kind} | {self.status}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
