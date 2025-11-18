# Aplikace pro správu a analýzu tréninkového plánu

## Popis projektu
Cílem projektu je navrhnout, implementovat a otestovat aplikaci pro analýzu běžeckých tréninků, které jsou získávány z externích zdrojů (ze souborů ve formátu FIT).  
Aplikace umožňuje uživateli sledovat vývoj výkonnosti v čase, vyhodnocovat jednotlivé tréninky a na základě těchto analýz efektivně plánovat další běžeckou přípravu.

Projekt vznikl v rámci individuální odborné činnosti (IOČ).

---

## Cíle projektu
- Získávat data o sportovních aktivitách z externích zdrojů (soubory).
- Zpracovat a analyzovat tato data.
- Přehledně zobrazovat klíčové metriky výkonu (vzdálenost, tempo, tepová frekvence, převýšení apod.).
- Umožnit uživateli sledovat vývoj výkonnosti a plánovat další trénink.

---

## Funkcionalita aplikace
- Import dat ze souborů ve formátu FIT.
- Ukládání aktivit do databáze.
- Vizualizace tréninkových dat pomocí grafů a tabulek.
- Generování osobních statistik a přehledů.
- Filtrování a porovnávání jednotlivých tréninků.
- Výpočet základních analytických ukazatelů (např. průměrné tempo, celkový objem, zátěžové ukazatele).

---

## Použité technologie
| Oblast | Technologie / nástroje |
|:--|:--|
| Programovací jazyk | HTML, JS, PHP / Java / Springboot, SQL |
| Datové formáty | FIT SDK, JSON |
| Architektura | Vícevrstvá – datová, aplikační a prezentační vrstva |
| Vývojové nástroje | NetBeans / VS Code, Git |

---

## Návrh systému
- **Datový model:** Ukládá informace o trénincích – datum, vzdálenost, čas, průměrné tempo, srdeční tep, převýšení apod.
- **Zpracování dat:** Parsování FIT souborů a jejich převod do interní struktury.
- **Analytická vrstva:** Výpočet statistik, trendů a průměrných hodnot.
- **Uživatelské rozhraní:** Přehledné zobrazení tréninkových výsledků, tabulek a grafů.

---

## Testování
Testování aplikace probíhalo pomocí:
- ručního testování funkcionalit,
- ověřování správnosti výpočtů a zobrazených dat,
- porovnávání výsledků s daty z Garmin Connect.
<!-- 
---

## Uživatelská příručka

### Instalace
1. Naklonujte repozitář:
   ```bash
   git clone https://github.com/vojtecholcman/trainingdDiary.git -->