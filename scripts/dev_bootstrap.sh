#!/usr/bin/env bash
# Rebuild this repo's dev environment after a container reset (2026-10-23):
# the two venvs, the headless Chromium for browser checks, the git hooks and
# the git push login. Idempotent: every step checks before it acts, so a re-run
# on a working container only verifies. The recipe it automates is
# docs/RESTART.md "After a container reset".
#
#   scripts/dev_bootstrap.sh                 everything
#   scripts/dev_bootstrap.sh --no-d1         skip .venv-d1
#   scripts/dev_bootstrap.sh --no-browser    skip Chromium
#   scripts/dev_bootstrap.sh --no-hooks      leave core.hooksPath alone
#
# Never prompts and never writes outside the repo, /tmp and the venvs. The
# Databricks OAuth login is interactive, so it is printed, not run.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$(pwd)

DO_D1=1 DO_BROWSER=1 DO_HOOKS=1
for arg in "$@"; do
    case "$arg" in
        --no-d1) DO_D1=0 ;;
        --no-browser) DO_BROWSER=0 ;;
        --no-hooks) DO_HOOKS=0 ;;
        -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
        *) echo "unknown option: $arg" >&2; exit 2 ;;
    esac
done

PW_BROWSERS=/tmp/pw
PW_LIBS=/tmp/pwlibs
PW_DEBS=/tmp/pwdebs
PW_LD="$PW_LIBS/usr/lib/x86_64-linux-gnu:$PW_LIBS/lib/x86_64-linux-gnu"
PW_PACKAGES="libglib2.0-0 libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libdbus-1-3
libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libasound2
libatspi2.0-0 libwayland-server0 libdrm2 libxi6 libxrender1 libxext6 libx11-6 libxcb1
libxau6 libxdmcp6 libbsd0 libmd0 libxcb-randr0"
GLOBAL_HOOKS=$(git config --global --get core.hooksPath || true)
LOCAL_HOOKS="$REPO/.git/codegen-hooks"

summary=()
step() { printf '\n== %s ==\n' "$1"; }
ok() { summary+=("ok    $1"); }
todo() { summary+=("TODO  $1"); }

# -- venvs (uv: pip's isolated pyspark build failed on 2026-10-23) --------------
venv() {   # <dir> <extras> [constraints]
    local dir=$1 extras=$2 constraints=${3:-}
    step "$dir"
    [ -x "$dir/bin/python" ] || uv venv --python 3.12 "$dir"
    if [ -n "$constraints" ]; then
        uv pip install --quiet --python "$dir/bin/python" -e ".[$extras]" -c "$constraints"
    else
        uv pip install --quiet --python "$dir/bin/python" -e ".[$extras]"
    fi
    "$dir/bin/python" -c "import codegen, pytest, xdist" && ok "$dir ($extras)"
}
command -v uv >/dev/null || { echo "uv is required (https://docs.astral.sh/uv/)" >&2; exit 1; }
venv .venv "dev,ui,live,databricks"
[ "$DO_D1" = 1 ] && venv .venv-d1 "dev,databricks" constraints/acfc_d1.txt

# -- headless Chromium for Playwright checks (no root: libs unpacked to /tmp) ----
chromium() {
    step "chromium"
    command -v node >/dev/null || { todo "chromium: node is not installed"; return; }
    [ -d ui/frontend/node_modules/playwright ] || (cd ui/frontend && npm ci --silent)
    PLAYWRIGHT_BROWSERS_PATH=$PW_BROWSERS node ui/frontend/node_modules/playwright/cli.js \
        install chromium-headless-shell >/dev/null
    local shell
    shell=$(find "$PW_BROWSERS" -type f -name chrome-headless-shell -perm -u+x | head -n 1)
    [ -n "$shell" ] || { todo "chromium: no chrome-headless-shell under $PW_BROWSERS"; return; }
    if LD_LIBRARY_PATH=$PW_LD ldd "$shell" | grep -q "not found"; then
        mkdir -p "$PW_DEBS" "$PW_LIBS"
        # shellcheck disable=SC2086  # the package list is word-split on purpose
        (cd "$PW_DEBS" && apt-get download $PW_PACKAGES >/dev/null)
        for deb in "$PW_DEBS"/*.deb; do dpkg -x "$deb" "$PW_LIBS"; done
    fi
    if LD_LIBRARY_PATH=$PW_LD ldd "$shell" | grep "not found"; then
        todo "chromium: libraries still missing (listed above)"
    else
        ok "chromium: LD_LIBRARY_PATH=$PW_LD PLAYWRIGHT_BROWSERS_PATH=$PW_BROWSERS node <script>"
    fi
}
[ "$DO_BROWSER" = 1 ] && chromium

# -- git hooks: the repo's pre-push guard AND the container's global hooks -------
# The container's global core.hooksPath (its post-commit syncs the Workspace)
# shadows scripts/git-hooks. A local hooks dir inside .git (never tracked) runs
# both: for each hook either side defines, the repo's first, then the global's,
# with the same arguments and stdin; the hook fails if either fails.
hooks() {
    step "git hooks"
    mkdir -p "$LOCAL_HOOKS"
    local names
    names=$( (ls scripts/git-hooks; [ -n "$GLOBAL_HOOKS" ] && ls "$GLOBAL_HOOKS") 2>/dev/null \
             | sort -u)
    for name in $names; do
        cat > "$LOCAL_HOOKS/$name" <<EOF
#!/usr/bin/env bash
# Written by scripts/dev_bootstrap.sh: runs the repo's $name hook, then the global one.
# stdin is buffered in a file, byte for byte: \$(cat) would drop the last newline,
# and pre-push's 'while read' loop then never sees its (only) line.
input=\$(mktemp)
trap 'rm -f "\$input"' EXIT
cat > "\$input"
status=0
for hook in "$REPO/scripts/git-hooks/$name" "$GLOBAL_HOOKS/$name"; do
    if [ -x "\$hook" ]; then
        "\$hook" "\$@" < "\$input" || status=\$?
    fi
done
exit \$status
EOF
        chmod +x "$LOCAL_HOOKS/$name"
    done
    git config core.hooksPath "$LOCAL_HOOKS"
    ok "git hooks: $(echo "$names" | tr '\n' ' ')-> $LOCAL_HOOKS (repo first, then ${GLOBAL_HOOKS:-no global})"
}
[ "$DO_HOOKS" = 1 ] && hooks

# -- git push login --------------------------------------------------------------
step "git push"
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
    gh auth setup-git && ok "git push via the gh login"
else
    todo "git push: run 'gh auth login', then re-run this script"
fi

# -- things that need a person ----------------------------------------------------
if [ ! -f /tmp/cgs/oauth.cfg ]; then
    todo "Databricks OAuth (the App's API): BROWSER=echo DATABRICKS_CONFIG_FILE=/tmp/cgs/oauth.cfg \
databricks auth login --host <DEFAULT profile host> --profile codegen-oaut (docs/RESTART.md)"
fi
SETTINGS=/app/python/source_code/.claude/settings.json
if [ -f "$SETTINGS" ] && "$REPO/.venv/bin/python" -c "
import json, sys
stop = json.load(open(sys.argv[1])).get('hooks', {}).get('Stop')
sys.exit(0 if stop and 'mlflow' in json.dumps(stop).lower() else 1)" "$SETTINGS"; then
    todo "the MLflow Stop hook is back in $SETTINGS: delete hooks.Stop (docs/RESTART.md)"
fi

printf '\n== summary ==\n'
printf '%s\n' "${summary[@]}"
