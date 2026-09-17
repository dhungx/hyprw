#!/usr/bin/env bash
# ime-select.sh — mở menu fuzzel chọn thẳng ngôn ngữ gõ (không phải cycle mù).
# Bind: Super+Shift+Space (xem modules/Keybinds.lua)
#
# Super+Space (đổi nhanh, cycle 2 chiều) do CHÍNH fcitx5 xử lý qua
# Hotkey/TriggerKeys trong fcitx5/config — không cần Hyprland can thiệp, nên
# hoạt động toàn cục ở mọi app kể cả khi Hyprland không có focus xử lý phím.
# Script này CHỈ lo phần "mở bảng chọn cụ thể" — việc riêng, dùng fuzzel.

declare -A IMES=(
    ["Tiếng Anh (US)"]="keyboard-us"
    ["Tiếng Việt (Unikey)"]="unikey"
)

selected=$(printf '%s\n' "${!IMES[@]}" | fuzzel --dmenu --prompt="Chọn ngôn ngữ gõ: ")

# Bấm Esc / không chọn -> thoát êm
[ -z "$selected" ] && exit 0

imname="${IMES[$selected]}"
[ -z "$imname" ] && exit 1

fcitx5-remote -s "$imname"
