#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
state="$root/.firefly-demo"
image="${FIREFLY_DEMO_IMAGE:-fireflyiii/core:latest}"
container="ff-iii-luciferin-demo"
volume="ff-iii-luciferin-demo-db"
url="http://127.0.0.1:18080"

command -v docker >/dev/null || { echo 'Docker is required.' >&2; exit 1; }
command -v python3 >/dev/null || { echo 'Python 3 is required.' >&2; exit 1; }
mkdir -p "$state"
chmod 700 "$state"

if [[ ! -f "$state/app_key" ]]; then
  if docker volume inspect "$volume" >/dev/null 2>&1; then
    echo "Existing demo database has no local app key in $state/app_key. Restore it before starting." >&2
    exit 1
  fi
  python3 -c 'import base64, secrets; print("base64:" + base64.b64encode(secrets.token_bytes(32)).decode())' > "$state/app_key"
  chmod 600 "$state/app_key"
fi

docker volume create "$volume" >/dev/null
if ! docker container inspect "$container" >/dev/null 2>&1; then
  docker pull "$image"
  docker run --rm --entrypoint sh \
    -v "$volume:/var/www/html/storage/database" "$image" \
    -c 'touch /var/www/html/storage/database/database.sqlite'
  docker run -d --name "$container" \
    -p 127.0.0.1:18080:8080 \
    -v "$volume:/var/www/html/storage/database" \
    -e APP_ENV=testing \
    -e "APP_KEY=$(cat "$state/app_key")" \
    -e "APP_URL=$url" \
    -e SITE_OWNER=e2e@example.invalid \
    -e DB_CONNECTION=sqlite \
    -e MAIL_MAILER=log \
    "$image" >/dev/null
elif [[ "$(docker inspect -f '{{.State.Running}}' "$container")" != true ]]; then
  docker start "$container" >/dev/null
fi

current_image="$(docker inspect -f '{{.Config.Image}}' "$container")"
if [[ "$current_image" != "$image" ]]; then
  echo "Existing demo container uses $current_image; requested $image." >&2
  echo "Stop and remove the container to change images; the database volume is preserved." >&2
fi

ready=false
for _ in {1..60}; do
  if python3 - "$url/login" <<'PY' >/dev/null 2>&1
import sys
import urllib.request

urllib.request.urlopen(sys.argv[1], timeout=2).close()
PY
  then
    ready=true
    break
  fi
  sleep 2
done
if [[ "$ready" != true ]]; then
  echo "Firefly III did not become ready. Check: docker logs $container" >&2
  exit 1
fi

if [[ ! -s "$state/env" ]]; then
  # The command refuses to create a second user, which is fine after an interrupted setup.
  docker exec "$container" php artisan system:create-first-user e2e@example.invalid >/dev/null 2>&1 || true
  docker cp "$root/scripts/e2e/create_token.php" "$container:/tmp/create_token.php" >/dev/null
  docker exec "$container" php /tmp/create_token.php >/dev/null
  token="$(docker exec "$container" cat /tmp/e2e-token)"
  if [[ -z "$token" || "$token" == *$'\n'* ]]; then
    echo 'Firefly III did not produce a valid token.' >&2
    exit 1
  fi
  umask 077
  printf 'FIREFLY_URL=%s\nFIREFLY_TOKEN=%s\n' "$url" "$token" > "$state/env"
fi

set -a
# shellcheck disable=SC1091
source "$state/env"
set +a
python3 "$root/scripts/demo/seed.py"

echo
echo "Firefly III is running at $url"
echo "Credentials: $state/env"
echo 'Run an example from the repository root:'
echo '  set -a; source .firefly-demo/env; set +a'
echo '  uv run python examples/min_usage_search.py'
echo 'Stop it with: bash scripts/demo/stop.sh'
