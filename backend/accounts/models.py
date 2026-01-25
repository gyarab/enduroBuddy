from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.constraints import UniqueConstraint
from django.dispatch import receiver
from django.db.models.signals import post_save

class Role(models.TextChoices):
        COACH = 'COACH', 'Coach'
        ATHLETE = 'ATHLETE', 'Athlete'

class Profile(models.Model):
        user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
        role = models.CharField(max_length=20, choices=Role.choices, default=Role.ATHLETE)

        def __str__(self):
            return f"{self.user.username} ({self.role})"

class CoachAthlete(models.Model):
    coach = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coachded_athletes')
    athlete = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='athlete_coaches')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Coach-Athlete link"
        verbose_name_plural = "Coach-Athlete links"
        constraints = [
            UniqueConstraint(fields=["coach", "athlete"], name="uniq_coach_athlete_pair"), models.CheckConstraint(check=~Q(coach=models.F("athlete")),name="coach_cannot_be_same_as_athlete",),
        ]

        def __str__(self) -> str:
            return f"{self.coach.username} -> {self.athlete.username}"
        
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)