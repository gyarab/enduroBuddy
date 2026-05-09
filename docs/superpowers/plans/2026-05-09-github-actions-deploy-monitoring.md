# GitHub Actions Auto-Deploy + Monitoring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatické nasazení na server při push do `main` + email monitoring přes UptimeRobot.

**Architecture:** GitHub Actions runner (GitHub-hosted, ubuntu-latest) se SSH připojí na server, spustí `git pull` + `docker compose up`. Server se autentizuje vůči private GitHub repo pomocí deploy klíče. Monitoring zajišťuje externí UptimeRobot.

**Tech Stack:** GitHub Actions, SSH (ed25519), Docker Compose, UptimeRobot

---

## Přehled souborů

| Soubor | Akce | Popis |
|--------|------|-------|
| `.github/workflows/deploy.yml` | Modify | Přepsat trigger + runner + SSH deploy kroky |

Vše ostatní jsou manuální kroky na serveru nebo v GitHub/UptimeRobot UI.

---

### Task 1: Zjisti veřejnou IP serveru

Potřebuješ veřejnou IP (nebo hostname) serveru pro GitHub Secret `SERVER_HOST`. `gawt` je jen lokální alias, GitHub Actions ho nezná.

- [ ] **Spusť na serveru:**

```bash
curl -s https://api.ipify.org
```

- [ ] **Ulož si výstup** (IPv4 adresa, např. `1.2.3.4`) — použiješ ji v Task 5 jako `SERVER_HOST`.

- [ ] **Ověř SSH přístup přes IP z lokálu** (volitelné, ověření):

```bash
ssh holcman@<IP>
```

---

### Task 2: Vygeneruj deploy klíč na serveru

Deploy klíč slouží k tomu, aby server mohl `git pull` z private GitHub repa bez hesla.

- [ ] **Spusť na serveru:**

```bash
ssh-keygen -t ed25519 -C "endurobuddy-deploy" -f ~/.ssh/id_ed25519_deploy -N ""
```

- [ ] **Zobraz veřejný klíč a zkopíruj ho:**

```bash
cat ~/.ssh/id_ed25519_deploy.pub
```

Výstup bude vypadat jako: `ssh-ed25519 AAAA... endurobuddy-deploy`

---

### Task 3: Přidej deploy klíč do GitHub repa

- [ ] Otevři `https://github.com/vojtecholcman/enduroBuddy/settings/keys`
- [ ] Klikni **Add deploy key**
- [ ] Title: `endurobuddy-server-deploy`
- [ ] Key: vlož obsah z `cat ~/.ssh/id_ed25519_deploy.pub`
- [ ] **Allow write access: NE** (read-only stačí)
- [ ] Klikni **Add key**

---

### Task 4: Nastav SSH config na serveru a změň remote

Bez SSH config by server použil výchozí klíč (`~/.ssh/id_rsa` nebo `id_ed25519`), ne náš deploy klíč.

- [ ] **Přidej na serveru do `~/.ssh/config`:**

```bash
cat >> ~/.ssh/config << 'EOF'

Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_deploy
  IdentitiesOnly yes
EOF
```

- [ ] **Nastav správná práva:**

```bash
chmod 600 ~/.ssh/config
```

- [ ] **Změň git remote z HTTPS na SSH:**

```bash
cd ~/endurobuddy
git remote set-url origin git@github.com:vojtecholcman/enduroBuddy.git
git remote -v
```

Očekávaný výstup:
```
origin  git@github.com:vojtecholcman/enduroBuddy.git (fetch)
origin  git@github.com:vojtecholcman/enduroBuddy.git (push)
```

- [ ] **Přidej GitHub do known_hosts a otestuj připojení:**

```bash
ssh-keyscan -H github.com >> ~/.ssh/known_hosts
ssh -T git@github.com
```

Očekávaný výstup:
```
Hi vojtecholcman! You've successfully authenticated, but GitHub does not provide shell access.
```

- [ ] **Otestuj git pull:**

```bash
cd ~/endurobuddy && git pull
```

Očekávaný výstup: `Already up to date.` (nebo stažení commitů)

---

### Task 5: Vygeneruj server access klíč (pro GitHub Actions)

Tento klíč slouží GitHub Actions runneru k SSH přístupu na server. Generuj **lokálně** (na svém počítači, ne na serveru).

- [ ] **Spusť lokálně:**

```bash
ssh-keygen -t ed25519 -C "github-actions-endurobuddy" -f ~/.ssh/id_ed25519_gha_deploy -N ""
```

- [ ] **Zobraz veřejný klíč:**

```bash
cat ~/.ssh/id_ed25519_gha_deploy.pub
```

- [ ] **Přidej veřejný klíč do `authorized_keys` na serveru:**

```bash
# spusť lokálně:
ssh-copy-id -i ~/.ssh/id_ed25519_gha_deploy.pub holcman@<IP_SERVERU>
```

Nebo manuálně — na serveru:
```bash
echo "<obsah .pub souboru>" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

- [ ] **Ověř SSH přihlášení s novým klíčem (lokálně):**

```bash
ssh -i ~/.ssh/id_ed25519_gha_deploy holcman@<IP_SERVERU> "echo OK"
```

Očekávaný výstup: `OK`

---

### Task 6: Přidej GitHub Secrets

- [ ] Otevři `https://github.com/vojtecholcman/enduroBuddy/settings/secrets/actions`
- [ ] Přidej Secret **`SERVER_SSH_KEY`**:
  - Hodnota: obsah soukromého klíče z `cat ~/.ssh/id_ed25519_gha_deploy`
  - Celý obsah včetně `-----BEGIN OPENSSH PRIVATE KEY-----` a `-----END OPENSSH PRIVATE KEY-----`

- [ ] Přidej Secret **`SERVER_HOST`**:
  - Hodnota: veřejná IP serveru z Task 1 (např. `1.2.3.4`)

- [ ] Přidej Secret **`SERVER_USER`**:
  - Hodnota: `holcman`

---

### Task 7: Ověř compose příkaz na serveru

Před zápisem workflow zkontroluj, jaký compose příkaz aktuálně funguje (jestli jen `docker-compose.yml` nebo i `docker-compose.prod.yml`).

- [ ] **Spusť na serveru:**

```bash
cd ~/endurobuddy
ls docker-compose*.yml
```

- [ ] **Spusť dry-run** (nezačne rebuild, jen zobrazí co by dělal):

```bash
docker compose config --quiet && echo "docker-compose.yml OK"
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet && echo "prod OK"
```

- [ ] **Rozhodnutí:** Pokud server používá oba soubory (Traefik labels jsou potřeba), použij v deploy příkazu `-f docker-compose.yml -f docker-compose.prod.yml`. Pokud stačí základní soubor, použij jen `docker compose up -d --build`.

  > Na základě výstupu uprav workflow v Task 8 — výchozí verze v plánu používá pouze `docker-compose.yml`.

---

### Task 8: Přepiš deploy workflow

- [ ] **Uprav [.github/workflows/deploy.yml](.github/workflows/deploy.yml):**

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Setup SSH key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SERVER_SSH_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key

      - name: Add server to known_hosts
        run: |
          ssh-keyscan -H ${{ secrets.SERVER_HOST }} >> ~/.ssh/known_hosts

      - name: Deploy
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.SERVER_USER }}@${{ secrets.SERVER_HOST }} "
            cd ~/endurobuddy &&
            git pull &&
            docker compose up -d --build &&
            docker compose ps
          "
```

> Pokud Task 7 ukázal, že je potřeba i `docker-compose.prod.yml`, nahraď `docker compose up -d --build` za `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`.

- [ ] **Commitni a pushni na main:**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add SSH auto-deploy on push to main"
git push origin main
```

- [ ] **Sleduj běh workflow:**
  Otevři `https://github.com/vojtecholcman/enduroBuddy/actions` a počkej na výsledek.

- [ ] **Ověř výstup:**
  - Všechny kroky zelené ✓
  - V logu `Deploy` step vidíš výstup `docker compose ps` se všemi running kontejnery

---

### Task 9: UptimeRobot — nastavení monitoringu

Čistě manuální setup v UptimeRobot UI, žádné změny v kódu.

- [ ] Zaregistruj se na `https://uptimerobot.com` (free tier stačí)

- [ ] Přidej alert contact:
  - Settings → Alert Contacts → Add Alert Contact
  - Type: **E-mail**
  - E-mail: `vojta.holcman@outlook.cz`
  - Potvrď přes ověřovací email

- [ ] Přidej první monitor:
  - Monitors → Add New Monitor
  - Monitor Type: **HTTP(S)**
  - Friendly Name: `EnduroBuddy — hlavní web`
  - URL: `https://endurobuddy.cz`
  - Monitoring Interval: **5 minutes**
  - Alert Contacts: vyber přidaný email kontakt
  - Klikni **Create Monitor**

- [ ] Přidej druhý monitor:
  - Monitor Type: **HTTP(S)**
  - Friendly Name: `EnduroBuddy — app`
  - URL: `https://app.endurobuddy.cz`
  - Monitoring Interval: **5 minutes**
  - Alert Contacts: vyber přidaný email kontakt
  - Klikni **Create Monitor**

- [ ] Ověř že oba monitory svítí zeleně (Status: Up)

---

### Task 10: Aktualizuj CLAUDE.md

- [ ] **Přidej do sekce "Aktivní plány a změny" v [CLAUDE.md](CLAUDE.md):**

```markdown
### 2026-05-09 — GitHub Actions auto-deploy + UptimeRobot monitoring ✅ KOMPLETNÍ

- Deploy workflow: push do `main` → SSH deploy na server (`holcman@<IP>`)
- Server: deploy klíč v `~/.ssh/id_ed25519_deploy` pro git pull z private repa
- GitHub Secrets: `SERVER_SSH_KEY`, `SERVER_HOST`, `SERVER_USER`
- Monitoring: UptimeRobot free, HTTP(S) monitoring `endurobuddy.cz` + `app.endurobuddy.cz`, email notifikace
```

- [ ] **Commitni:**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with auto-deploy and monitoring setup"
git push origin main
```
