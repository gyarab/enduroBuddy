from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from training.models import TrainingMonth

MONTH_NAMES_CS = ["", "Leden","Únor","Březen","Duben","Květen","Červen","Červenec","Srpen","Září","Říjen","Listopad","Prosinec"]

def month_label_cs(year: int, month: int) -> str:
    return f"{MONTH_NAMES_CS[month]} {year}"

@login_required
def home(request):
    months = (
    TrainingMonth.objects
    .filter(athlete=request.user)
    .prefetch_related(
        "weeks",
        "weeks__planned_trainings",
        "weeks__planned_trainings__activity",
        "weeks__planned_trainings__activity__intervals",
    )
    .order_by("-year", "-month")[:6]
)


    month_cards = []
    for m in months:
        month_cards.append({
            "id": m.id,
            "year": m.year,
            "month": m.month,
            "label": month_label_cs(m.year, m.month),
            "weeks": list(m.weeks.all()),
        })

    return render(request, "dashboard/dashboard.html", {"month_cards": month_cards})
