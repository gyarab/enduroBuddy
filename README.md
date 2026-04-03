# EnduroBuddy

EnduroBuddy je webová aplikace postavená na Django pro plánování tréninku a správu vytrvalostních aktivit. Projekt propojuje práci trenéra a sportovce v jednom rozhraní: trenér připravuje měsíční plán, sportovec zapisuje plnění a k jednotlivým tréninkům může párovat reálně absolvované aktivity importované z FIT souborů nebo ze služby Garmin Connect.

Repozitář obsahuje funkční backend i server-rendered frontend, autentizaci přes email a Google, workflow pro role `Coach` a `Athlete`, plánovací dashboard, správu skupin a testy pro klíčové scénáře importu i editace tréninků.

## Hlavní funkce

- registrace, přihlášení, potvrzení emailu a reset hesla přes `django-allauth`
- volitelný Google login
- role `Coach` a `Athlete`
- propojení trenéra a sportovce přes coach join code a join requesty
- tréninkové skupiny a pozvánky přes token
- měsíční plánovací dashboard s týdenní strukturou
- editace plánovaných tréninků včetně dvoufázových dní
- evidence dokončených tréninků
- import aktivit z FIT souborů
- synchronizace aktivit z Garmin Connect
- deduplikace importu podle kontrolního součtu
- ukládání intervalů a časové řady pro další analýzu
- Django admin pro správu dat

## Pro koho je projekt určený

Projekt řeší dvě hlavní role:

- `Athlete`: spravuje svůj plán, doplňuje splněné tréninky a importuje aktivity
- `Coach`: připravuje plán pro sebe i svěřence, organizuje skupiny a sleduje jejich tréninkový přehled

## Architektura

Projekt je rozdělený do několika Django aplikací:

- `backend/accounts`
  správa profilů, rolí, vazeb mezi trenéry a sportovci, skupin, pozvánek a Garmin připojení
- `backend/training`
  modely pro měsíce, týdny, plánované tréninky a dokončené tréninky
- `backend/activities`
  import a ukládání aktivit, souborů, intervalů, vzorků a import ledgeru
- `backend/dashboard`
  hlavní dashboard, coach rozhraní, servisní logika a endpointy pro interaktivní úpravy
- `backend/templates` a `backend/static`
  UI postavené nad Django templates s vlastním JavaScriptem a CSS

### Důležité URL

- `/` dashboard sportovce
- `/coach/plans/` dashboard trenéra
- `/accounts/` autentizace
- `/admin/` administrační rozhraní

## Doménový model

Nejdůležitější entity v projektu:

- `Profile`
  role uživatele, stav legendy a coach join code
- `CoachAthlete`
  vazba trenér -> sportovec, fokus a pořadí v přehledu
- `TrainingGroup` a `TrainingGroupInvite`
  skupiny a pozvánky do skupiny
- `TrainingMonth`, `TrainingWeek`, `PlannedTraining`, `CompletedTraining`
  plánovací vrstva a evidence splnění
- `Activity`, `ActivityFile`, `ActivityInterval`, `ActivitySample`
  importované aktivity a jejich analytická reprezentace
- `GarminConnection`, `GarminSyncAudit`, `ImportJob`
  napojení na Garmin, audit synchronizací a stav importních úloh

## Technologie

- Python 3.12
- Django 5.2
- PostgreSQL
- `django-allauth`
- `fitparse`
- `garminconnect`
- server-rendered frontend s vlastním JS/CSS
- Docker a Docker Compose

## Struktura repozitáře

```text
.
├── backend/
│   ├── accounts/
│   ├── activities/
│   ├── config/
│   ├── dashboard/
│   ├── templates/
│   ├── training/
│   └── manage.py
├── docs/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Požadavky

Pro lokální vývoj budeš potřebovat:

- Python 3.12 nebo novější
- PostgreSQL
- `pip`

Alternativně můžeš použít Docker Compose, což je v tomto projektu nejjednodušší cesta.

## Rychlý start přes Docker

### 1. Připrav konfiguraci

Zkopíruj vzorový konfigurační soubor:

```bash
copy .env.example .env
```

Pro local Docker/Compose obvykle nech `POSTGRES_HOST=db`.

Do `.env` doplň minimálně tyto hodnoty:

```env
DJANGO_SECRET_KEY=replace-with-long-random-secret-key
POSTGRES_DB=endurobuddy
POSTGRES_USER=endurobuddy
POSTGRES_PASSWORD=endurobuddy_password
DJANGO_DEBUG=true
```

### 2. Spusť aplikaci

```bash
docker compose up --build
```

### 3. Otevři projekt v prohlížeči

```text
http://127.0.0.1:8000
```

Kontejner `web` při startu automaticky spouští migrace a následně Django development server.

## Lokální vývoj

Doporučený postup pro běžný vývoj je spustit PostgreSQL přes Docker Compose a Django lokálně ve vlastním virtuálním prostředí.

### 1. Naklonuj repozitář

```bash
git clone <repo-url>
cd endurobuddy-private
```

### 2. Vytvoř a aktivuj virtuální prostředí

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
```

### 3. Nainstaluj závislosti

```bash
pip install -r requirements.txt
```

### 4. Připrav `.env`

Zkopíruj vzorový soubor:

```bash
cp .env.example .env
```

Ve Windows PowerShell můžeš použít i:

```powershell
Copy-Item .env.example .env
```

Pak v `.env` nastav alespoň:

```env
DJANGO_SECRET_KEY=replace-with-long-random-secret-key
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
POSTGRES_DB=endurobuddy
POSTGRES_USER=endurobuddy
POSTGRES_PASSWORD=endurobuddy_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Poznámky:

- `DJANGO_SECRET_KEY` je povinný, bez něj aplikace nenaběhne
- `DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost` stačí pro lokální vývoj
- hodnoty `POSTGRES_DB`, `POSTGRES_USER` a `POSTGRES_PASSWORD` musí odpovídat databázi, kterou spustíš níže přes Docker Compose

Pokud chceš používat Google login nebo odesílání emailů přes SMTP, doplň také příslušné proměnné z `.env.example`.

### 5. Spusť databázi

```bash
docker compose up db -d
```

`docker-compose.yml` ve výchozím stavu vytvoří PostgreSQL s těmito údaji:

```env
POSTGRES_DB=endurobuddy
POSTGRES_USER=endurobuddy
POSTGRES_PASSWORD=endurobuddy_password
```

### 6. Proveď migrace

```bash
cd backend
python manage.py migrate
```

### 7. Volitelně vytvoř administrátora

```bash
python manage.py createsuperuser
```

### 8. Spusť vývojový server

```bash
python manage.py runserver
```

## Konfigurace prostředí

Projekt používá zejména tyto proměnné prostředí:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `DJANGO_EMAIL_BACKEND`
- `DJANGO_EMAIL_HOST`
- `DJANGO_EMAIL_PORT`
- `DJANGO_EMAIL_HOST_USER`
- `DJANGO_EMAIL_HOST_PASSWORD`
- `DJANGO_DEFAULT_FROM_EMAIL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GARMIN_SYNC_LIMIT`
- `GARMIN_KMS_KEY_ID`
- `GARMIN_KMS_KEYS`
- `GARMIN_CONNECT_ENABLED`
- `GARMIN_SYNC_ENABLED`
- `IMPORT_TASK_MODE`

### Poznámky ke konfiguraci

- bez `DJANGO_SECRET_KEY` aplikace nenaběhne
- databáze je v `settings.py` nastavena na PostgreSQL
- výchozí `IMPORT_TASK_MODE=inline` spouští import v procesu aplikace
- pro Garmin synchronizaci je potřeba mít nakonfigurované ukládání tokenů
- `GARMIN_CONNECT_ENABLED=false` schová a zablokuje nové připojení Garmin účtu
- `GARMIN_SYNC_ENABLED=false` schová a zablokuje Garmin synchronizaci, ale ponechá možnost účet odpojit

## Demo data

Repozitář obsahuje připravený management command pro naplnění demo prostředí:

```bash
cd backend
python manage.py seed_coach_demo
```

Command vytvoří:

- demo trenéra `coach_demo@endurobuddy.local`
- tři demo sportovce
- skupinu `A-team`
- několik měsíců ukázkových plánů

Všechny demo účty mají heslo `demo12345`.

## Testování

Spuštění celé testovací sady:

```bash
cd backend
python manage.py test
```

Testy v projektu pokrývají mimo jiné:

- FIT import flow
- Garmin importer
- rekonstrukci intervalů
- coach plánování
- bezpečnost vybraných profile/settings akcí
- frontend regresní scénáře dashboardu

## Užitečné soubory

- `backend/inspect_fit.py`
  jednoduchý nástroj pro inspekci struktury `.fit` souborů
- `docs/wireframes/`
  wireframy a návrhy obrazovek
- `docker-compose.yml`
  lokální stack pro web a PostgreSQL
