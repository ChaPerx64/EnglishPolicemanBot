#!/bin/bash
docker stop ep_bot_container || true && docker rm ep_bot_container || true
docker build -t chapardev/ep_bot .
docker run \
    --name ep_bot_container \
    --env-file '.env.dev' \
    --mount source=ep_bot_volume,target=/ep_bot/db \
    chapardev/ep_bot
docker image prune -f
