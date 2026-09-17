#!/usr/bin/env bash
# wallpaper-select.sh — chọn wallpaper qua fuzzel, chuyển bằng awww có animation.
# Bind: Super+W (xem modules/Keybinds.lua)
#
# An toàn tài nguyên: lệnh `awww img` chỉ GỬI yêu cầu cho awww-daemon (vốn đã
# chạy sẵn nền để hiện wallpaper tĩnh) rồi THOÁT NGAY — bản thân script này
# không đứng chờ, không loop. Animation chuyển cảnh chạy bên trong tiến trình
# daemon có sẵn đó trong đúng khoảng --transition-duration rồi tự dừng lại ở
# trạng thái idle bình thường — không có gì mới bị bỏ lại chạy nền.

WALLPAPER_DIR="$HOME/.config/hypr/wallpapers"
CURRENT_LINK="$WALLPAPER_DIR/current.jpg"

mkdir -p "$WALLPAPER_DIR"

# Liệt kê ảnh có thật, loại trừ chính symlink "current.jpg" để khỏi hiện lại
selected=$(find "$WALLPAPER_DIR" -maxdepth 1 -type f \
    \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) \
    ! -name 'current.jpg' -printf '%f\n' \
    | sort \
    | fuzzel --dmenu --prompt="Chọn wallpaper: ")

# Bấm Esc / không chọn gì -> thoát êm, không đổi gì cả
[ -z "$selected" ] && exit 0

target="$WALLPAPER_DIR/$selected"
[ -f "$target" ] || exit 1

# Cập nhật symlink "current" — hyprlock.conf trỏ vào đây nên màn khoá cũng
# tự đồng bộ theo wallpaper vừa chọn, không cần sửa gì thêm
ln -sfn "$target" "$CURRENT_LINK"

# Random 1 hiệu ứng đẹp mỗi lần cho đỡ nhàm — cả 5 kiểu đều mượt, an toàn để
# "chơi thoải mái" như bạn nói vì chỉ chạy đúng 1 lần, đúng thời lượng khai báo
transitions=(wipe wave grow center outer)
pick_transition=${transitions[$RANDOM % ${#transitions[@]}]}

awww img "$target" \
    --transition-type "$pick_transition" \
    --transition-duration 1.2 \
    --transition-fps 60
