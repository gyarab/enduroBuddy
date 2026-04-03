# EnduroBuddy Visual Style Guide

## Cíl směru

EnduroBuddy má působit jako přesný pracovní nástroj pro vytrvalostní sport, ne jako lifestyle aplikace. Vizuální styl má být moderní, klidný, úsporný a silně orientovaný na čitelnost dat, plánování a každodenní používání trenérem i sportovcem.

Klíčová slova:

- minimalistický
- technický, ale ne chladný
- funkční před efektem
- soustředěný na výkon, rytmus a disciplínu
- důvěryhodný při práci s daty

## Co jsme chtěli vědomě neudělat

Při návrhu jsem se opřel o vizuální směr podobných endurance aplikací a vědomě se od něj odchýlil:

- `Strava` často staví identitu na silné oranžové, výkonové energii a komunitní dynamice.
- `Garmin Connect` působí utilitárněji, často přes množství karet, metrik a systémových vzorů.
- `TrainingPeaks` je více “coaching analytics” platforma, s důrazem na kalendář, grafy a výkonnostní data.
- `intervals.icu` je velmi datově husté a analytické prostředí.

Z těchto referencí plyne jeden záměr: EnduroBuddy nemá být ani sportovní sociální síť, ani přeplněný analytický cockpit. Má působit jako čistý tréninkový workspace.

Navržené odlišení:

- místo výrazné oranžové nebo modré použít tlumenou tmavou základnu s chladnou zeleno-šedou akcentní linkou
- omezit počet “loud” barev a místo toho stavět kontrast přes velikost, hustotu a prázdný prostor
- nepoužívat agresivní gradienty ani fitness-marketing vizuál
- zvýrazňovat důležité stavy přes strukturu a rytmus, ne přes neustálé barevné výkřiky

Poznámka:
Výše uvedené odlišení je návrhová syntéza na základě veřejně dostupných popisů a běžně známých vlastností podobných aplikací, ne kopie konkrétních obrazovek.

## Typografie

### Primární identitní font

Používej `Space Grotesk` jako display font:

- logo
- hlavní H1
- výrazné názvy sekcí
- velké numerické highlighty nebo hero titulky

Nepoužívej ho pro:

- dlouhé odstavce
- tabulky
- formuláře
- malé popisky
- husté dashboardy

Důvod:
U vytrvalostní a plánovací aplikace je rozhodující čitelnost. `Space Grotesk` může dodat charakter značce, ale hlavní provozní text potřebuje neutrálnější sans-serif.

### Doporučený pracovní font

Pro vše ostatní používej jednoduchý sans-serif s vysokou čitelností. Pokud nechceš zatím řešit licencování nebo webfonty, můžeš začít takto:

```css
font-family: "Segoe UI Variable Text", "Segoe UI", "Inter", sans-serif;
```

### Typografická hierarchie

- `Display / Hero`: Space Grotesk, 44-56 px, tracking lehce utažený
- `H1`: Space Grotesk, 32-40 px
- `H2`: sans-serif, 24-28 px, 600-700
- `H3`: sans-serif, 18-20 px, 600
- `Body`: sans-serif, 15-16 px, 400-500
- `Meta / Label`: sans-serif, 12-13 px, 600, kapitálky jen výjimečně
- `Data / Numeric`: sans-serif, 16-28 px, 600-700

## Barevný systém

### Základní paleta

```text
Ink 950        #101714   hlavní tmavé pozadí
Ink 900        #16201c   sekundární tmavá plocha
Panel 800      #1d2924   karty / sticky panely / modal top
Mist 300       #d7dfdb   hlavní světlý text na tmavém
Mist 200       #e9efec   světlé plochy a inverzní background
Slate 500      #7f9088   sekundární text
Line 600       #2d3a35   border na tmavém
Line 200       #cfd8d4   border na světlém
Accent 500     #61c48f   primární akcent
Accent 600     #4bad79   hover primárních CTA
Alert 500      #ff7a59   kritické upozornění
Warn 500       #d9a441   upozornění / pending
Info 500       #77b7d7   informační stav
```

### Charakter barev

- Tmavá základna evokuje soustředění a ranní trénink.
- Zelený akcent nepůsobí jako kopie Stravy ani Garminu.
- Světlé plochy lze používat pro tabulky, exporty nebo printable modu.
- Kritické stavy mají být vzácné a barevně jasné.

### Poměr barev

- 70 % neutrální tmavé a světlé plochy
- 20 % struktura, border, hover, disabled
- 10 % akcent a stavové barvy

## Tvarosloví

- Radius: 14 px pro karty a vstupy, 18 px pro větší panely, 999 px pro pills
- Border: tenký a klidný, ne silný
- Stíny: mělké, spíš ambientní než “floating”
- Ikony: jednoduché line nebo duotone, bez agresivních sport piktogramů
- Grid: 8 px systém

## Layout principy

### Základní nálada

- hodně vzduchu kolem primárních dat
- kompaktní tabulky jen tam, kde dávají smysl
- jasné rozdělení na plánovací vrstvu, analytickou vrstvu a akční vrstvu

### Doporučená šířka a spacing

- hlavní kontejner: 1280-1440 px
- sekce mezi sebou: 24-32 px
- vnitřní padding karet: 20-24 px
- hustý datový mód: 12-16 px

### Hierarchie obrazovky

1. nahoře kontext: období, role, jméno sportovce, rychlé akce
2. pod tím hlavní plán nebo přehled tréninků
3. sekundárně metriky, poznámky, filtry, importy
4. naposled pomocné nebo historické bloky

## Komponenty

### Tlačítka

- `Primary`: tmavé pozadí + Accent, používá se střídmě
- `Secondary`: outline nebo tlumené vyplnění
- `Ghost`: na toolbar a filtry
- `Danger`: jen na destruktivní akce

Pravidlo:
Na jedné ploše by ideálně mělo být pouze jedno opravdu dominantní CTA.

### Inputy

- výška 44-48 px
- tmavý nebo světlý surface podle kontextu
- placeholder slabší než label
- focus ring přes jemný zelený glow, ne default browser blue

### Search bar

- větší než běžný input
- vlevo ikona
- vpravo quick action nebo filtr
- výsledky vizuálně kompaktní a rychle skenovatelné

### Tabulky

- primárně pro týdenní nebo měsíční přehled
- lehké oddělení řádků
- sticky header
- řádek po hoveru jen jemně zvýraznit
- důležité hodnoty zarovnávat konzistentně

### Karty

- jedna karta = jeden účel
- nerozmělňovat je do mnoha malých metrických dlaždic bez priority
- u výkonnostních metrik používat velké číslo + malý kontext pod ním

### Badges a chips

- role: `Coach`, `Athlete`
- typ tréninku: `Easy`, `Tempo`, `Intervals`, `Long Run`
- stav: `Done`, `Planned`, `Missed`, `Pending Import`

### Scrollbar

- tenká
- s nízkým kontrastem
- thumb lehce kulatý
- při hoveru o něco viditelnější

### Modaly a panely

- šířka 560-720 px
- hlavička velmi čistá
- destruktivní nebo potvrzovací akce vždy dole vpravo
- důležitá metadata mít i bez scrollu

## Tone of UI

Texty v rozhraní by měly být:

- krátké
- technicky srozumitelné
- bez marketingových frází
- podporující disciplínu a jistotu

Příklady:

- místo `Crush your goals today` použít `Dnešní plán`
- místo `Amazing progress` použít `Objem roste 3. týden v řadě`
- místo `Upload your workout now!` použít `Importovat aktivitu`

## Motion

Animace jen tam, kde zvyšují orientaci:

- jemný reveal při načtení dashboardu
- rychlý fade/slide u dropdownu a modalu
- subtlní highlight po uložení změn
- žádné výrazné bounce nebo sporty “energy flashes”

Doporučení:

- duration 140-220 ms pro běžné interakce
- ease-out pro vstup
- ease-in-out pro stavy

## Přístupnost

- kontrast textu minimálně WCAG AA
- neindikovat stav jen barvou
- focus state musí být vždy viditelný
- hit area u tlačítek minimálně 40 x 40 px
- tabulky a filtry musí fungovat i při zvětšení textu

## Doporučené tokeny

```css
:root {
  --eb-bg: #101714;
  --eb-bg-elevated: #16201c;
  --eb-surface: #1d2924;
  --eb-surface-soft: #22312b;
  --eb-text: #e9efec;
  --eb-text-muted: #9eb0a8;
  --eb-text-strong: #ffffff;
  --eb-line: #2d3a35;
  --eb-line-soft: #3a4a43;
  --eb-accent: #61c48f;
  --eb-accent-hover: #4bad79;
  --eb-danger: #ff7a59;
  --eb-warning: #d9a441;
  --eb-info: #77b7d7;
  --eb-radius-sm: 10px;
  --eb-radius-md: 14px;
  --eb-radius-lg: 18px;
  --eb-shadow-1: 0 8px 24px rgba(0, 0, 0, 0.18);
  --eb-shadow-2: 0 18px 48px rgba(0, 0, 0, 0.24);
}
```

## Doporučené použití Space Grotesk

Silné použití:

- wordmark `EnduroBuddy`
- login / onboarding hero
- hlavní page title
- section break titulky u marketingovějších částí

Střídmé použití:

- číselné highlighty
- názvy top-level dashboard modulů

Nevhodné použití:

- formuláře
- sidebar navigace
- dropdowny
- dense table headers
- malé button labely

## Co obsahuje HTML showcase

Soubor `docs/visual-style-preview.html` obsahuje:

- paletu
- typografii
- tlačítka
- inputy a search bar
- select, segmented control, checkbox, switch
- badges a stavy
- metrické karty
- tabulku
- scrollovatelný panel
- notifikaci
- modal preview
- skeleton loading

## Doporučení pro další krok

Pokud se ti tenhle směr bude líbit, další rozumný krok je:

1. připojit open-source font `Space Grotesk`
2. převést tokeny do jedné centrální CSS vrstvy
3. aplikovat styl nejdřív na login, top nav a dashboard shell
4. až potom řešit detailní stavy tabulek, kalendáře a modálů

## Použité online reference

- TrainingPeaks App Store: https://apps.apple.com/id/app/trainingpeaks/id408047715
- Garmin Connect App Store: https://apps.apple.com/ae/app/garmin-connect/id583446403
- Strava Apps directory: https://www.strava.com/apps/social-motivation
