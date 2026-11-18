#!/usr/bin/env bash
# Deploys the Upwork agent to a Linux server with Docker. Run from this folder:
#   bash deploy.sh
# It only touches $DEST and the "upwork-agent" container.
#
# Server details live in deploy.env (git-ignored), for example:
#   DEPLOY_HOST=ubuntu@your.server.ip
#   DEPLOY_KEY=$HOME/.ssh/your_key
#   DEPLOY_DEST=/opt/upwork-agent
set -euo pipefail

cd "$(dirname "$0")"
[ -f deploy.env ] && source deploy.env

HOST="${DEPLOY_HOST:?Set DEPLOY_HOST in deploy.env (e.g. ubuntu@your.server.ip)}"
KEY="${DEPLOY_KEY:-$HOME/.ssh/id_ed25519}"
DEST="${DEPLOY_DEST:-/opt/upwork-agent}"
SSH=(ssh -i "$KEY" -o IdentitiesOnly=yes "$HOST")

[ -f .env ] || { echo "No .env in this folder"; exit 1; }

echo "== 1/4 Checking the Groq model name"
GROQ_API_KEY=$(grep -E '^GROQ_API_KEY=' .env | cut -d= -f2- | tr -d '"\r')
GROQ_MODEL=$(grep -E '^GROQ_MODEL=' .env | cut -d= -f2- | tr -d '"\r')
MODELS=$(curl -fsS https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY" \
  | python3 -c 'import sys,json; print("\n".join(sorted(m["id"] for m in json.load(sys.stdin)["data"])))') \
  || { echo "Groq rejected the API key in .env. Fix GROQ_API_KEY and re-run."; exit 1; }
if ! grep -qx "$GROQ_MODEL" <<<"$MODELS"; then
  echo "GROQ_MODEL=$GROQ_MODEL is not available on this Groq account. Available models:"
  echo "$MODELS" | sed 's/^/  /'
  echo "Set GROQ_MODEL in .env to one of these and re-run."
  exit 1
fi
echo "   $GROQ_MODEL is available"
REPLY=$(curl -sS https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" -H "Content-Type: application/json" \
  -d "{\"model\":\"$GROQ_MODEL\",\"max_tokens\":2000,\"messages\":[{\"role\":\"user\",\"content\":\"Write one friendly sentence greeting a new client.\"}]}")
if ! python3 -c 'import sys,json; t=(json.load(sys.stdin)["choices"][0]["message"].get("content") or "").strip(); print("   test reply:", t); sys.exit(0 if t else 1)' <<<"$REPLY"; then
  echo "Groq did not return a usable reply for $GROQ_MODEL. Raw response:"; echo "$REPLY" | head -c 600; echo
  exit 1
fi

echo "== 2/4 Preparing $DEST on the server"
"${SSH[@]}" "sudo mkdir -p $DEST && sudo chown ubuntu:ubuntu $DEST && mkdir -p $DEST/data"

echo "== 3/4 Uploading code"
rsync -az --delete -e "ssh -i $KEY -o IdentitiesOnly=yes" \
  --exclude data/ --exclude backup-original/ --exclude deploy.env --exclude '__pycache__/' --exclude .git/ --exclude .DS_Store \
  ./ "$HOST:$DEST/"
"${SSH[@]}" "chmod 600 $DEST/.env"

echo "== 4/4 Building and starting the container"
"${SSH[@]}" "cd $DEST && docker compose up -d --build && sleep 25 && docker compose ps && echo '--- last log lines ---' && docker compose logs --tail 25"

echo
echo "Done. Send /test to the bot in Telegram."
echo "Logs later:  ssh -i $KEY $HOST 'cd $DEST && docker compose logs -f --tail 50'"
