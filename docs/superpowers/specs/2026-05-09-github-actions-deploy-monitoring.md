# GitHub Actions Auto-Deploy + Monitoring

**Datum:** 2026-05-09  
**Status:** Approved

## Kontext

Server `gawt` (holcman@gawt) dosud nasazuje manuálně — `git pull` + `docker compose up`. Kód byl v školním repozitáři `gyarab/endurobuddy`. Cílem je přejít na soukromé GitHub repo, automatizovat nasazení při merge do `main` a zavést monitoring s email notifikacemi.

## Cíle

1. Push do `main` → automatické nasazení na server bez manuálního zásahu
2. Veškerý vývoj probíhá ve feature větvích; `main` = produkce
3. Email notifikace při výpadku serveru (i při obnovení)

## Architektura CI/CD

### Přístupová model — dvě SSH klíčové páry

**1. Deploy klíč (server → GitHub)**
- Účel: server stáhne kód z private repa pomocí `git pull`
- Generuje se na serveru: `ssh-keygen -t ed25519 -C "endurobuddy-deploy" -f ~/.ssh/id_ed25519_deploy`
- Veřejný klíč → přidán do GitHub repa jako Deploy Key (Settings → Deploy keys, read-only)
- SSH config na serveru (~/.ssh/config):
  ```
  Host github.com
    IdentityFile ~/.ssh/id_ed25519_deploy
    IdentitiesOnly yes
  ```
- Git remote na serveru změněn z HTTPS na SSH:
  `git remote set-url origin git@github.com:<owner>/endurobuddy.git`

**2. Server access klíč (GitHub Actions → server)**
- Účel: GitHub Actions runner se SSH připojí na server a spustí deploy příkazy
- Generuje se lokálně (nebo kdekoliv mimo server): `ssh-keygen -t ed25519 -C "github-actions-deploy"`
- Soukromý klíč → uložen jako GitHub Secret `SERVER_SSH_KEY`
- Veřejný klíč → přidán do `~/.ssh/authorized_keys` na serveru

### GitHub Secrets

| Secret | Hodnota |
|--------|---------|
| `SERVER_SSH_KEY` | Soukromý klíč pro přístup na server (PEM/OpenSSH formát) |
| `SERVER_HOST` | Hostname nebo IP adresa serveru |
| `SERVER_USER` | `holcman` |

### Workflow (`.github/workflows/deploy.yml`)

- **Trigger:** `on: push: branches: [main]`
- **Runner:** `ubuntu-latest` (GitHub-hosted)
- **Kroky:**
  1. Setup SSH agenta s klíčem ze Secret
  2. Přidat server do `known_hosts` (zabránění MITM při prvním připojení)
  3. SSH na server → `cd ~/endurobuddy && git pull && docker compose up -d --build`
  4. Volitelně: `docker compose ps` pro ověření stavu kontejnerů v logu

### Deploy příkaz na serveru

```bash
cd ~/endurobuddy && git pull && docker compose up -d --build
```

Používá pouze `docker-compose.yml` (stejně jako dosavadní manuální nasazení). Traefik labels jsou v `docker-compose.prod.yml` — tento soubor se na serveru použije pouze pokud je to aktuální praxe.

> **Poznámka k prod compose:** Při implementaci ověřit, jakým příkazem se aktuálně nasazuje (jestli jen `docker compose` nebo `docker compose -f docker-compose.yml -f docker-compose.prod.yml`), a workflow tomu přizpůsobit.

## Monitoring

### Nástroj: UptimeRobot (free tier)

Externě hostovaná služba — monitoring běží mimo server, takže funguje i při úplném výpadku VM.

**Monitory:**
| URL | Typ | Interval |
|-----|-----|---------|
| `https://endurobuddy.cz` | HTTP(S) | 5 minut |
| `https://app.endurobuddy.cz` | HTTP(S) | 5 minut |

**Notifikace:**
- Email: `vojta.holcman@outlook.cz`
- Odesílat při: pádu i obnovení

**Setup:** Čistě manuální v UptimeRobot UI — žádné změny v kódu ani na serveru.

## Změny v repozitáři

- `.github/workflows/deploy.yml` — přepsán: trigger `push:main`, GitHub-hosted runner, SSH deploy
- Žádné další změny v kódu

## Změny na serveru

- Nový SSH klíč `~/.ssh/id_ed25519_deploy` (deploy klíč pro GitHub)
- Úprava `~/.ssh/config` pro použití deploy klíče
- Změna git remote na SSH URL soukromého repa
- Přidání veřejného klíče GitHub Actions runneru do `~/.ssh/authorized_keys`

## Workflow pro vývoj (po implementaci)

```
feat/<tema> → implementace → push → merge to main → automatické nasazení
```

Větev `main` je vždy stav produkce. Feature větve se mergují až po otestování na localhostu.

## Co tato spec neřeší

- Rollback strategie při selhání deploye (řeší se manuálně přes `git reset` + redeploy)
- Spouštění testů v CI před deployem (možné rozšíření v budoucnu)
- Staging prostředí
