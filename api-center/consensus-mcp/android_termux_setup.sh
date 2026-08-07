#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="a15280020511/evidence-data-center"
WORKDIR="${HOME}/evidence-data-center"
TOKEN_FILE="${HOME}/.config/evidence-data-center/consensus-oauth-token.json"

say() {
  printf '\n==> %s\n' "$1"
}

fail() {
  printf '\nERROR: %s\n' "$1" >&2
  exit 1
}

command -v pkg >/dev/null 2>&1 || fail "This helper must be run inside Termux on Android."

say "Installing Python, Git and GitHub CLI"
pkg update -y
pkg install -y python git gh

say "Fetching the latest Intelligence Center code"
if [ -d "${WORKDIR}/.git" ]; then
  git -C "${WORKDIR}" fetch origin main
  git -C "${WORKDIR}" checkout main
  git -C "${WORKDIR}" pull --ff-only origin main
else
  git clone "https://github.com/${REPO}.git" "${WORKDIR}"
fi
cd "${WORKDIR}"

say "Installing pinned Consensus MCP dependencies"
python -m pip install --disable-pip-version-check --no-input \
  -r api-center/consensus-mcp/requirements.txt

say "Checking GitHub authorization"
if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  printf '\nGitHub will show a browser/device login. Complete it with the repository-owner account.\n'
  gh auth login --hostname github.com --git-protocol https --web
fi

gh auth status --hostname github.com >/dev/null 2>&1 || fail "GitHub authorization did not complete."

say "Starting one-time Consensus Free-account OAuth"
printf '%s\n' \
  "A Consensus authorization URL will appear below." \
  "Tap/open that URL on this SAME phone, sign in to your Consensus Free account, and approve access." \
  "The browser will return to http://127.0.0.1:8765/callback, which Termux is listening on." \
  "Do not close Termux while the browser authorization is in progress."

python api-center/consensus-mcp/oauth_bootstrap.py bootstrap \
  --timeout 600 \
  --no-browser

[ -f "${TOKEN_FILE}" ] || fail "OAuth token file was not created."
chmod 600 "${TOKEN_FILE}" 2>/dev/null || true

say "Installing refresh token directly into GitHub Actions Secret"
python - "${TOKEN_FILE}" <<'PY' | gh secret set CONSENSUS_MCP_REFRESH_TOKEN --repo "${REPO}"
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1]).expanduser()
value = json.loads(path.read_text(encoding="utf-8"))
refresh = str(value.get("refresh_token") or "").strip()
if not refresh:
    raise SystemExit("refresh token missing")
sys.stdout.write(refresh)
PY

say "Removing the local OAuth token file after GitHub Secret installation"
rm -f "${TOKEN_FILE}"

printf '\nSUCCESS\n'
printf '%s\n' \
  "Consensus Free OAuth bootstrap is complete." \
  "GitHub Secret CONSENSUS_MCP_REFRESH_TOKEN has been installed without printing the token." \
  "The local token file was deleted." \
  "Return to ChatGPT and say: 已经加好了"
