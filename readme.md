# EnduroBuddy Backend

Backendová část aplikace EnduroBuddy slouží pro import, ukládání a analýzu sportovních aktivit (primárně běžeckých) ze souborů ve formátu FIT.  
Systém je navržen s důrazem na datovou efektivitu, rozšiřitelnost a budoucí přechod na produkční infrastrukturu.

Projekt vzniká jako součást individuální odborné činnosti (IOČ).

---

## Hlavní vlastnosti

- Import sportovních aktivit ze souborů FIT  
- Automatické parsování a normalizace dat  
- Ukládání analyticky relevantních metrik  
- Detekce typu aktivity (run, workout, apod.)  
- Intervalová struktura tréninku  
- Přehledné administrační rozhraní  
- Dashboard pro zobrazování výsledků  

---

## Architektura

Aplikace je postavena jako vícevrstvý systém:

- Prezentační vrstva – dashboard a admin rozhraní  
- Aplikační logika – Django views, signály  
- Servisní vrstva – FIT parser  
- Datová vrstva – relační databáze  

Cílem návrhu je:

- oddělení logiky zpracování dat od webové vrstvy  
- jednoduchý přechod na PostgreSQL  
- vysoký výkon při práci s větším objemem aktivit  

---

## Použité technologie

| Oblast | Technologie |
|------|-----------|
| Backend | Python 3.14 |
| Framework | Django 5 |
| Databáze | SQLite (vývoj), PostgreSQL (plán) |
| Import dat | FIT format, fitparse |
| Frontend | Django templates |
| Verzování | Git |

---

## Datový model (zjednodušený)

### Activity
- čas zahájení  
- typ sportu  
- délka trvání  
- vzdálenost  
- průměrné tempo  
- průměrná a maximální TF  

### ActivityInterval
- pořadí intervalu  
- délka  
- vzdálenost  
- tempo  
- tepová frekvence  

### ActivityFile
- zdrojový soubor  
- typ souboru  
- vazba na aktivitu  

Systém vědomě neukládá surová senzorová data s vysokou frekvencí.

---

## Struktura projektu

# EnduroBuddy Backend

Backendová část aplikace EnduroBuddy slouží pro import, ukládání a analýzu sportovních aktivit (primárně běžeckých) ze souborů ve formátu FIT.  
Systém je navržen s důrazem na datovou efektivitu, rozšiřitelnost a budoucí přechod na produkční infrastrukturu.

Projekt vzniká jako součást individuální odborné činnosti (IOČ).

---

## Hlavní vlastnosti

- Import sportovních aktivit ze souborů FIT  
- Automatické parsování a normalizace dat  
- Ukládání analyticky relevantních metrik  
- Detekce typu aktivity (run, workout, apod.)  
- Intervalová struktura tréninku  
- Přehledné administrační rozhraní  
- Dashboard pro zobrazování výsledků  

---

## Architektura

Aplikace je postavena jako vícevrstvý systém:

- Prezentační vrstva – dashboard a admin rozhraní  
- Aplikační logika – Django views, signály  
- Servisní vrstva – FIT parser  
- Datová vrstva – relační databáze  

Cílem návrhu je:

- oddělení logiky zpracování dat od webové vrstvy  
- jednoduchý přechod na PostgreSQL  
- vysoký výkon při práci s větším objemem aktivit  

---

## Použité technologie

| Oblast | Technologie |
|------|-----------|
| Backend | Python 3.14 |
| Framework | Django 5 |
| Databáze | PostgreSQL |
| Import dat | FIT format, fitparse, GarminAPI |
| Frontend | Django templates |
| Verzování | Git |

---

## Datový model (zjednodušený)

### Activity
- čas zahájení  
- typ sportu  
- délka trvání  
- vzdálenost  
- průměrné tempo  
- průměrná a maximální TF  

### ActivityInterval
- pořadí intervalu  
- délka  
- vzdálenost  
- tempo  
- tepová frekvence  

### ActivityFile
- zdrojový soubor  
- typ souboru  
- vazba na aktivitu  

Systém vědomě neukládá surová senzorová data s vysokou frekvencí.

---

## Instalace

### 1.1 Klonování repozitáře přes SHH

```bash
git clone git@github.com:vojtecholcman/enduroBuddy.git
cd backend
```
### 1.2 Klonování repozitáře přes URL

```bash
git clone https://github.com/vojtecholcman/enduroBuddy.git
cd backend
```
### 2. Virtuální prostředí

```bash
py -3 -m .venv venv
```

### 3. Aktivate virtuálního prostředí

```bash
source .venv/Scripts/Activate
```

### 4. Instalace závislostí
```bash
pip install -r requirements.txt
```

### 5. Migrace databáze
```bash
python manage.py migrate
```

### 6. Migrace databáze
```bash
python manage.py createsuperuser
```

### 7. Spuštění serveru
```bash
python manage.py runserver
```