#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GIT_BASH="/c/Program Files/Git/git-bash.exe"

echo "Spouštím databázi přes Docker Compose..."
cd "$PROJECT_DIR"
docker compose up -d db

echo "Otevírám frontend..."

"$GIT_BASH" -c "
cd '$PROJECT_DIR/frontend' &&

if [ ! -d node_modules ]; then
    echo 'Chybí node_modules, spouštím pnpm install...'
    pnpm install
fi

pnpm run dev

exec bash
" &

echo "Otevírám backend..."

"$GIT_BASH" -c "
cd '$PROJECT_DIR/backend' &&

source ../.venv/Scripts/activate &&

./manage.py runserver

exec bash
" &

echo "Hotovo."
