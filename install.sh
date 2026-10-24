#!/bin/bash
# Rosary for Omarchy.
#
#   ./install.sh               theme, cursors, terminal rice, daily rotation
#   ./install.sh --all         ...plus the boot splash (asks for sudo)
#   ./install.sh --no-cursors  keep your present mouse cursor
#   ./install.sh --no-rotate   install the theme but no daily timer/hooks
#   ./install.sh --plymouth    repaint the boot splash (asks for sudo)
#   ./install.sh --uninstall   remove the theme, timer and cursors
#
# The theme is installed as a git clone in ~/.config/omarchy/themes/rosary, so
# `omarchy theme update` pulls it like any other theme from a repository. The
# cursor, script, timer and hooks are links into that clone, so a pull reaches
# all of them; rerun ./install.sh afterwards to reapply the theme.
#
# The theme follows the traditional weekday order of the Rosary: Sunday and
# Wednesday Glorious, Monday and Saturday Joyful, Tuesday and Friday
# Sorrowful, Thursday Luminous. At midnight the next set takes over.
set -euo pipefail

THEME=rosary
TITLE="Rosary"
CURSOR=Rosary
SRC="$(cd "$(dirname "$0")" && pwd)"
THEMES_DIR="$HOME/.config/omarchy/themes"
THEME_DIR="$THEMES_DIR/$THEME"
CURSOR_DIR="$HOME/.local/share/icons/$CURSOR"
BIN="$HOME/.local/bin/rosary-daily"
UNIT_DIR="$HOME/.config/systemd/user"
HOOK_DIR="$HOME/.config/omarchy/hooks"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/rosary"
USER_BG="$HOME/.config/omarchy/backgrounds/$THEME"
CURRENT_NAME="$HOME/.local/state/omarchy/current/theme.name"
COPY_FILES=(colors.toml btop.theme icons.theme chromium.theme preview.png
  unlock.png paintings cursors extras scripts systemd README.md CREDITS.md LICENSE)

cursors=1 rotate=1 plymouth=0 uninstall=0
for arg in "$@"; do
  case "$arg" in
  --all) plymouth=1 ;;
  --plymouth | --boot) plymouth=1 ;;
  --no-cursors) cursors=0 ;;
  --no-rotate) rotate=0 ;;
  --uninstall) uninstall=1 ;;
  --yes | -y) : ;;
  -h | --help)
    sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
    ;;
  *)
    echo "unknown option: $arg" >&2
    exit 1
    ;;
  esac
done

command -v omarchy >/dev/null || { echo "This needs Omarchy (https://omarchy.org)." >&2; exit 1; }

current_theme() { cat "$CURRENT_NAME" 2>/dev/null || true; }

if ((uninstall)); then
  if [[ $(current_theme) == "$THEME" ]]; then
    echo "$TITLE is the active theme. Switch away first (omarchy theme set <name>), then run --uninstall." >&2
    exit 1
  fi
  systemctl --user disable --now rosary-daily.timer >/dev/null 2>&1 || true
  rm -f "$UNIT_DIR/rosary-daily.timer" "$UNIT_DIR/rosary-daily.service" "$BIN"
  # Also the generic hook names older installers wrote.
  rm -f "$HOOK_DIR/theme-set.d/rosary.hook" "$HOOK_DIR/post-boot.d/rosary.hook" \
    "$HOOK_DIR/theme-set.d/theme-set.hook" "$HOOK_DIR/post-boot.d/post-boot.hook"
  rm -rf "$CURSOR_DIR" "$STATE" "$USER_BG"
  systemctl --user daemon-reload >/dev/null 2>&1 || true
  [[ $SRC -ef $THEME_DIR ]] || rm -rf "$THEME_DIR"
  if command -v living-themes >/dev/null 2>&1; then
    living-themes apply "$(current_theme)" >/dev/null 2>&1 || true
  fi
  echo "Removed $TITLE, its cursors and its daily timer."
  [[ $SRC -ef $THEME_DIR ]] && echo "This checkout is the installed theme folder; remove it yourself: rm -rf $THEME_DIR"
  exit 0
fi

echo "✝ Installing $TITLE"

# --- theme checkout ----------------------------------------------------------
# Omarchy's `theme update` pulls the themes under ~/.config/omarchy/themes that
# are real git checkouts, so install this one as a clone rather than a copy.
# Omarchy keeps no Lua from a cloned theme, which is why the border gradient
# lives in colors.toml and there is no hyprland.lua in this repository.
REPO_URL=$(git -C "$SRC" remote get-url origin 2>/dev/null || true)

if [[ $SRC -ef $THEME_DIR ]]; then
  echo "✝ Using this checkout in place"
elif [[ -L $THEME_DIR ]]; then
  echo "✝ $THEME_DIR is a symlinked working copy; leaving it alone."
  echo "  omarchy theme update skips symlinks: update it with git -C $(readlink -f "$THEME_DIR") pull"
elif [[ -d $THEME_DIR/.git ]]; then
  echo "✝ Updating $TITLE"
  git -C "$THEME_DIR" pull --ff-only ||
    echo "warning: could not fast-forward the installed theme; using what is checked out." >&2
elif [[ -n $REPO_URL ]]; then
  echo "✝ Cloning $TITLE into $THEME_DIR"
  mkdir -p "$THEMES_DIR"
  rm -rf "$THEME_DIR"
  git clone --quiet -- "$REPO_URL" "$THEME_DIR"
else
  echo "✝ Copying $TITLE into $THEME_DIR"
  echo "  (this checkout has no git remote, so omarchy theme update will not track it)"
  mkdir -p "$THEMES_DIR"
  rm -rf "$THEME_DIR"
  mkdir -p "$THEME_DIR"
  for f in "${COPY_FILES[@]}"; do
    cp -a "$SRC/$f" "$THEME_DIR/"
  done
fi

# --- paintings ---------------------------------------------------------------
if [[ $(find "$THEME_DIR/paintings" -maxdepth 1 -name '*-[0-9][0-9]-*.jpg' 2>/dev/null | wc -l) -ne 20 ]]; then
  echo "Expected 20 paintings in $THEME_DIR/paintings. Build them with scripts/build-wallpapers.py." >&2
  exit 1
fi

# Older builds carried a private Plymouth package; the splash now uses
# Omarchy's own pipeline and unlock.png.
rm -rf "$THEME_DIR/plymouth" "$THEME_DIR/extras/boot.sh" "$THEME_DIR/extras/boot.plymouth"

# --- cursors -----------------------------------------------------------------
if ((cursors)); then
  echo "✝ Installing the $CURSOR crucifix cursors"
  # A clone keeps the cursor package deleted by an earlier --no-cursors run.
  if [[ -d $THEME_DIR/.git && ! -e $THEME_DIR/extras/cursor ]]; then
    git -C "$THEME_DIR" checkout -- extras/cursor 2>/dev/null || true
  fi
  mkdir -p "$(dirname "$CURSOR_DIR")"
  rm -rf "$CURSOR_DIR"
  ln -sfn "$THEME_DIR/cursors/$CURSOR" "$CURSOR_DIR"
else
  # Living Themes applies extras/cursor on every theme change, so take it out
  # of the installed theme when the user wants to keep their own cursor.
  rm -f "$THEME_DIR/extras/cursor"
fi

# --- daily rotation ----------------------------------------------------------
# The script, units and hooks are links into the theme clone, so `omarchy theme
# update` refreshes them without a second install.
mkdir -p "$(dirname "$BIN")" "$UNIT_DIR"
[[ -x $THEME_DIR/scripts/rosary-daily ]] || chmod +x "$THEME_DIR/scripts/rosary-daily"
ln -sfn "$THEME_DIR/scripts/rosary-daily" "$BIN"

if ((rotate)); then
  echo "✝ Installing the daily mystery timer"
  ln -sfn "$THEME_DIR/systemd/rosary-daily.service" "$UNIT_DIR/rosary-daily.service"
  ln -sfn "$THEME_DIR/systemd/rosary-daily.timer" "$UNIT_DIR/rosary-daily.timer"

  install_hook() {
    local kind=$1 script=$2
    mkdir -p "$HOOK_DIR/$kind.d"
    # Older installers copied the script under its own name, which can collide
    # with another theme's hook. Remove that copy when it is still ours.
    if [[ -f $HOOK_DIR/$kind.d/$script && ! -L $HOOK_DIR/$kind.d/$script ]] &&
      cmp -s "$THEME_DIR/scripts/hooks/$script" "$HOOK_DIR/$kind.d/$script"; then
      rm -f "$HOOK_DIR/$kind.d/$script"
    fi
    ln -sfn "$THEME_DIR/scripts/hooks/$script" "$HOOK_DIR/$kind.d/rosary.hook"
  }
  install_hook theme-set theme-set.hook
  install_hook post-boot post-boot.hook

  systemctl --user daemon-reload >/dev/null 2>&1 || true
  systemctl --user enable --now rosary-daily.timer >/dev/null 2>&1 || true
fi

# --- terminal rice, cursor and login chime -----------------------------------
if command -v living-themes >/dev/null 2>&1; then
  living-themes apply "$THEME" >/dev/null 2>&1 || true
elif ((cursors)); then
  gsettings set org.gnome.desktop.interface cursor-theme "$CURSOR" >/dev/null 2>&1 || true
  hyprctl setcursor "$CURSOR" "${XCURSOR_SIZE:-24}" >/dev/null 2>&1 || true
  echo "  note: Living Themes is not installed, so the prompt, fastfetch, lazygit and"
  echo "        fzf/eza extras stay in extras/ until you install it."
fi

# --- apply -------------------------------------------------------------------
echo "✝ Switching to $TITLE"
omarchy theme set "$THEME"
"$BIN" --force

if ((plymouth)); then
  echo "✝ Repainting the boot splash (sudo)"
  omarchy-plymouth-set-by-theme "$THEME"
fi

cat <<DONE

✝ Done. Today is $(date +%A): $("$BIN" --print-set), $("$BIN" --status | sed -n 's/.*mystery set: *//p').
  rosary-daily --status          what is showing, and which set is in place
  rosary-daily --force           set today's first painting now
  rosary-daily --tick            advance one painting
  omarchy theme update           pull the theme when it changes upstream
  omarchy-plymouth-set-by-theme rosary   put the badge on the boot splash (sudo)
DONE
