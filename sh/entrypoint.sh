#!/bin/sh

redis-server /app/conf/redis.conf &
python -m py.master
tail -f /dev/null