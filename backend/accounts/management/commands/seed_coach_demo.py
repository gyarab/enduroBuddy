from __future__ import annotations

from calendar import monthrange
from datetime import date

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import CoachAthlete, Role, TrainingGroup, TrainingGroupAthlete
from training.models import PlannedTraining, TrainingMonth, TrainingWeek


class Command(BaseCommand):
    help = "Create demo coach, athletes, group and richer sample training plans."

    def handle(self, *args, **options):
        User = get_user_model()

        coach, _ = User.objects.get_or_create(
            username="coach_demo",
            defaults={
                "email": "coach_demo@endurobuddy.local",
                "first_name": "Petr",
                "last_name": "Novak",
            },
        )
        coach.set_password("demo12345")
        coach.save(update_fields=["password"])
        self._ensure_verified_email(coach)
        coach.profile.role = Role.COACH
        coach.profile.save(update_fields=["role"])

        athlete_specs = [
            ("athlete_lucie", "Lucie", "Kralova"),
            ("athlete_tomas", "Tomas", "Svoboda"),
            ("athlete_anna", "Anna", "Dvorakova"),
        ]
        athletes = []
        for username, first_name, last_name in athlete_specs:
            athlete, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@endurobuddy.local",
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            athlete.set_password("demo12345")
            athlete.save(update_fields=["password"])
            self._ensure_verified_email(athlete)
            athlete.profile.role = Role.ATHLETE
            athlete.profile.save(update_fields=["role"])
            athletes.append(athlete)

        group, _ = TrainingGroup.objects.get_or_create(
            coach=coach,
            name="A-team",
            defaults={"description": "Vytrvalostni skupina"},
        )

        for athlete in athletes:
            CoachAthlete.objects.get_or_create(coach=coach, athlete=athlete)
            TrainingGroupAthlete.objects.get_or_create(group=group, athlete=athlete)
            self._seed_athlete_plan(athlete)

        self.stdout.write(self.style.SUCCESS("Demo coach dashboard data ready."))
        self.stdout.write("Coach login: coach_demo@endurobuddy.local / demo12345")
        self.stdout.write(
            "Athlete logins: athlete_lucie@endurobuddy.local, athlete_tomas@endurobuddy.local, "
            "athlete_anna@endurobuddy.local / demo12345"
        )

    def _seed_athlete_plan(self, athlete) -> None:
        today = date.today()
        base_year = today.year
        base_month = today.month

        weekly_templates = [
            ("Po", "Lehky vyklus", 8, "Plynule tempo Z2"),
            ("Ut", "Intervaly 6x800m", 11, "Meziklus 2 min"),
            ("Ct", "Tempovy beh", 10, "20 min v prahu"),
            ("So", "Dlouhy beh", 18, "Posledni 3 km svizne"),
        ]

        # 4 months back including current month, each with up to 4 training weeks.
        for month_offset in range(0, 4):
            year, month_num = self._shift_month(base_year, base_month, -month_offset)
            month, _ = TrainingMonth.objects.get_or_create(
                athlete=athlete,
                year=year,
                month=month_num,
            )
            days_in_month = monthrange(year, month_num)[1]

            for week_index in range(1, 5):
                week, _ = TrainingWeek.objects.get_or_create(
                    training_month=month,
                    week_index=week_index,
                )
                week_start_day = 1 + (week_index - 1) * 7

                for day_shift, (day_label, title, km, notes) in zip([0, 1, 3, 5], weekly_templates):
                    day = week_start_day + day_shift
                    if day > days_in_month:
                        continue
                    run_day = date(year, month_num, day)
                    PlannedTraining.objects.get_or_create(
                        week=week,
                        date=run_day,
                        order_in_day=1,
                        defaults={
                            "day_label": day_label,
                            "title": title,
                            "planned_distance_km": km,
                            "notes": notes,
                        },
                    )

    def _shift_month(self, year: int, month: int, delta: int) -> tuple[int, int]:
        total = year * 12 + (month - 1) + delta
        out_year = total // 12
        out_month = (total % 12) + 1
        return out_year, out_month

    def _ensure_verified_email(self, user) -> None:
        EmailAddress.objects.filter(user=user).exclude(email=user.email).delete()
        email_row, _ = EmailAddress.objects.get_or_create(
            user=user,
            email=user.email,
            defaults={"verified": True, "primary": True},
        )
        if not email_row.verified or not email_row.primary:
            email_row.verified = True
            email_row.primary = True
            email_row.save(update_fields=["verified", "primary"])
