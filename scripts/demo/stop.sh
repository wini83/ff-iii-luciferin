#!/usr/bin/env bash
set -euo pipefail

container="ff-iii-luciferin-demo"
if docker container inspect "$container" >/dev/null 2>&1; then
  docker stop "$container" >/dev/null
  echo 'Firefly III stopped. The demo database and credentials are preserved.'
else
  echo 'Firefly III demo container does not exist.'
fi
