#!/bin/bash
set -e

git pull

if docker compose version &>/dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi
