#!/bin/bash
readonly env_file=${1:-".env.dev"}
readonly enable_xolo=${2:-0}


set -a
[ -f "$env_file" ] && . "$env_file"
set +a

docker compose -p jub --env-file "$env_file" -f jub-api.yml down
docker compose -p jub --env-file "$env_file" -f jub-api.yml up -d
if [ "$enable_xolo" = 1 ]; then
    2>&1 echo "Enabling XOLO..."
    2>&1 echo "XOLO will be available at http://localhost:${XOLO_PORT}"
    docker compose -p jub --env-file "$env_file" -f xolo.yml down
    docker compose -p jub --env-file "$env_file" -f xolo.yml up -d
else
    2>&1 echo "XOLO is disabled. To enable it, run the script with the second argument set to '1':"
    2>&1 echo "./deploy.sh <env_file> 1"
fi