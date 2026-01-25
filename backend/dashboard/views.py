from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    # Fake data (dokud nemáme DB)
    weeks = [
        {
            "label": "I.",
            "plan": [
                {"date": "1.1.", "day": "Mon", "training": "2R 15-20×400m ANP, P=45s 2V", "notes": ""},
                {"date": "2.1.", "day": "Tue", "training": "10 km klus", "notes": ""},
                {"date": "3.1.", "day": "Wed", "training": "3R 3×4×200m kopec, 200m MK, P=4’ 3V", "notes": ""},
                {"date": "4.1.", "day": "Thu", "training": "volno", "notes": ""},
                {"date": "5.1.", "day": "Fri", "training": "2R 8 km fartlek", "notes": ""},
                {"date": "6.1.", "day": "Sat", "training": "6–8 km regenerační klus + lehce posilka", "notes": ""},
                {"date": "7.1.", "day": "Sun", "training": "16–18 km Z2–Z3", "notes": ""},
            ],
            # vpravo zatím prázdné řádky (jako na wireframu)
            "analysis": [
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
            ],
            "total": "",
        },
        {
            "label": "II.",
            "plan": [
                {"date": "8.1.", "day": "Mon", "training": "2R 4×2km ANP P=2,5’ 2V", "notes": ""},
                {"date": "9.1.", "day": "Tue", "training": "klus + rovinky", "notes": ""},
                {"date": "10.1.", "day": "Wed", "training": "posilka", "notes": ""},
                {"date": "11.1.", "day": "Thu", "training": "volno", "notes": ""},
                {"date": "12.1.", "day": "Fri", "training": "tempový běh", "notes": ""},
                {"date": "13.1.", "day": "Sat", "training": "klus", "notes": ""},
                {"date": "14.1.", "day": "Sun", "training": "dlouhý běh", "notes": ""},
            ],
            "analysis": [
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
                {"splits": "", "time": "", "distance": "", "hr": "", "feel": ""},
            ],
            "total": "",
        },
    ]

    months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6", "Month 7", "Month 8", "Month 9", "Month 10", "Month 11", "Month 12"]

    return render(request, "dashboard/dashboard.html", {"weeks": weeks, "months": months})
