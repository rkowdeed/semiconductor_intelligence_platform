#!/usr/bin/env bash
# Minimal TCP wait helper: wait-for-it.sh host:port -- command args...
set -e

hostport="$1"
shift
host="${hostport%%:*}"
port="${hostport##*:}"

echo "Waiting for ${host}:${port}..."
until (echo > /dev/tcp/"${host}"/"${port}") >/dev/null 2>&1; do
  sleep 1
done
echo "${host}:${port} is available."

if [ "$1" = "--" ]; then
  shift
  exec "$@"
fi
