#!/bin/bash

PROJECT="$(cygpath -u "$USERPROFILE")/projects/endurobuddy-private"

GIT_BASH="/c/Program Files/Git/git-bash.exe"
DOCKER_DESKTOP="/c/Program Files/Docker/Docker/Docker Desktop.exe"

# 1) git pull – otevře okno, přejde do projektu a stáhne změny
cmd.exe /c start "EnduroBuddy - git pull" "$GIT_BASH" --login -i -c "
cd \"$PROJECT\" || { echo 'Složka projektu neexistuje'; read; exit 1; }
git pull
echo
read -p 'Hotovo. Stiskni Enter pro zavření...'
"

# 2) backend – spustí Docker Desktop, aktivuje venv a spustí Django server
cmd.exe /c start "EnduroBuddy - backend" "$GIT_BASH" --login -i -c "
\"$DOCKER_DESKTOP\" &

cd \"$PROJECT/backend\" || { echo 'Složka backend neexistuje'; read; exit 1; }

echo 'Čekám na Docker...'
until docker info >/dev/null 2>&1; do
  sleep 2
done

source ../.venv/Scripts/activate || { echo 'Nepodařilo se aktivovat venv'; read; exit 1; }

./manage.py runserver

echo
read -p 'Server skončil. Stiskni Enter pro zavření...'
"

# 3) frontend – přejde do frontend složky a spustí dev server
cmd.exe /c start "EnduroBuddy - frontend" "$GIT_BASH" --login -i -c "
cd \"$PROJECT/frontend\" || { echo 'Složka frontend neexistuje'; read; exit 1; }

pnpm run dev

echo
read -p 'Frontend skončil. Stiskni Enter pro zavření...'
"
