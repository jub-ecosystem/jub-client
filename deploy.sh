#!/bin/bash
readonly env_file=${1:-".env.dev"}
docker compose -p jub --env-file "$env_file" -f jub-api.yml down
docker compose -p jub --env-file "$env_file" -f jub-api.yml up -d

docker compose -p jub --env-file "$env_file" -f xolo.yml down
docker compose -p jub --env-file "$env_file" -f xolo.yml up -d
