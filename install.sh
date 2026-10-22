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
# The theme follows the traditional weekday order of the Rosary: Sunday and
# Wednesday Glorious, Monday and Saturday Joyful, Tuesday and Friday
# Sorrowful, Thursday Luminous. At midnight the next set takes over.
set -euo pipefail

THEME=rosary
TITLE="Rosary"
CURSOR=Rosary
SRC="$(cd "$(dirname "$0")" && pwd)"
THEME_DIR="$HOME/.config/omarchy/themes/$THEME"
CURSOR_DIR="$HOME/.local/share/icons/$CURSOR"
BIN="$HOME/.local/bin/rosary-daily"
UNIT_DIR="$HOME/.config/systemd/user"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/rosary"
USER_BG="$HOME/.config/omarchy/backgrounds/$THEME"
CURRENT_NAME="$HOME/.local/state/omarchy/current/theme.name"
THEME_FILES=(colors.toml btop.theme icons.theme chromium.theme hyprland.lua
  preview.png unlock.png paintings extras)

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
    sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
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
  rm -f "$HOME/.config/omarchy/hooks/theme-set.d/theme-set.hook" \
        "$HOME/.config/omarchy/hooks/post-boot.d/post-boot.hook"
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

# --- paintings ---------------------------------------------------------------
if [[ $(find "$SRC/paintings" -maxdepth 1 -name '*-[0-9][0-9]-*.jpg' 2>/dev/null | wc -l) -ne 20 ]]; then
  echo "Expected 20 paintings in $SRC/paintings. Build them with scripts/build-wallpapers.py." >&2
  exit 1
fi

# --- theme files -------------------------------------------------------------
mkdir -p "$THEME_DIR/backgrounds"
# Older builds carried a private Plymouth package; the splash now uses
# Omarchy's own pipeline and unlock.png.
rm -rf "$THEME_DIR/plymouth" "$THEME_DIR/extras/boot.sh" "$THEME_DIR/extras/boot.plymouth"
if ! [[ $SRC -ef $THEME_DIR ]]; then
  for f in "${THEME_FILES[@]}"; do
    rm -rf "${THEME_DIR:?}/$f"
    cp -a "$SRC/$f" "$THEME_DIR/"
  done
  if ((!cursors)); then rm -f "$THEME_DIR/extras/cursor"; fi
fi

# --- cursors -----------------------------------------------------------------
if ((cursors)); then
  echo "✝ Installing the $CURSOR crucifix cursors"
  rm -rf "$CURSOR_DIR"
  mkdir -p "$(dirname "$CURSOR_DIR")"
  cp -a "$SRC/cursors/$CURSOR" "$CURSOR_DIR"
fi

# --- daily rotation ----------------------------------------------------------
mkdir -p "$(dirname "$BIN")" "$UNIT_DIR" "$HOME/.config/omarchy/hooks"
install -m 755 "$SRC/scripts/rosary-daily" "$BIN"
if ((rotate)); then
  echo "✝ Installing the daily mystery timer"
  install -m 644 "$SRC/systemd/rosary-daily.service" "$UNIT_DIR/rosary-daily.service"
  install -m 644 "$SRC/systemd/rosary-daily.timer" "$UNIT_DIR/rosary-daily.timer"
  if command -v omarchy-hook-install >/dev/null 2>&1; then
    omarchy hook install theme-set "$SRC/scripts/hooks/theme-set.hook" >/dev/null
    omarchy hook install post-boot "$SRC/scripts/hooks/post-boot.hook" >/dev/null
  else
    mkdir -p "$HOME/.config/omarchy/hooks/theme-set.d" "$HOME/.config/omarchy/hooks/post-boot.d"
    install -m 755 "$SRC/scripts/hooks/theme-set.hook" "$HOME/.config/omarchy/hooks/theme-set.d/"
    install -m 755 "$SRC/scripts/hooks/post-boot.hook" "$HOME/.config/omarchy/hooks/post-boot.d/"
  fi
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
  omarchy-plymouth-set-by-theme rosary   put the badge on the boot splash (sudo)
DONE
