#!/bin/bash

set -e

REMOTE_USER="holcman"
REMOTE_HOST="gawt.dtcloud.cz"
REMOTE_DIR="/home/holcman/backups/endurobuddy"

CONTAINER_NAME="endurobuddy-db"
COMPOSE_SERVICE="db"

DB_NAME="endurobuddy"
DB_USER="endurobuddy"

LOCAL_DIR="./db_backups"

mkdir -p "$LOCAL_DIR"

echo "Hledám poslední zálohu na serveru..."

LATEST_BACKUP=$(ssh "$REMOTE_USER@$REMOTE_HOST" "ls -t $REMOTE_DIR/endurobuddy_*.sql.gz | head -n 1")

if [ -z "$LATEST_BACKUP" ]; then
    echo "Nebyla nalezena žádná záloha."
    exit 1
fi

BACKUP_FILE=$(basename "$LATEST_BACKUP")
LOCAL_BACKUP_PATH="$LOCAL_DIR/$BACKUP_FILE"

echo "Poslední záloha:"
echo "$BACKUP_FILE"

echo "Stahuji zálohu přes SCP..."

scp "$REMOTE_USER@$REMOTE_HOST:$LATEST_BACKUP" "$LOCAL_BACKUP_PATH"

echo "Kontroluji Docker container..."

if ! docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    echo "Container '$CONTAINER_NAME' neběží. Spouštím službu '$COMPOSE_SERVICE'..."

    docker compose up -d "$COMPOSE_SERVICE"

    echo "Čekám na start PostgreSQL..."
    sleep 5
fi

echo "Nahrávám zálohu do Docker containeru '$CONTAINER_NAME'..."

gunzip -c "$LOCAL_BACKUP_PATH" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"

echo "Import databáze dokončen."

echo "Mažu lokální zálohu..."
rm -f "$LOCAL_BACKUP_PATH"

echo "Mažu složku db_backups..."
rmdir "$LOCAL_DIR" 2>/dev/null || true

echo "Hotovo. Záloha byla úspěšně obnovena a lokální soubory smazány."
