#!/usr/bin/env bash
# osd-volume.sh up|down|mute — chỉnh volume qua wpctl, hiện OSD qua dunst
# (dùng dunstify -h int:value:N để vẽ progress bar thật trong notification,
# không cần cài thêm package OSD riêng)

case "$1" in
    up)   wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+ ;;
    down) wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%- ;;
    mute) wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle ;;
    *) echo "Dùng: $0 up|down|mute" >&2; exit 1 ;;
esac

info=$(wpctl get-volume @DEFAULT_AUDIO_SINK@)
percent=$(echo "$info" | grep -oP '[0-9]+\.[0-9]+' | awk '{printf "%d", $1*100}')

# -r <id cố định> để notification MỚI đè lên notification CŨ thay vì xếp
# chồng — bấm liên tục phím volume chỉ thấy 1 popup cập nhật số, không phải
# hàng loạt popup xếp hàng
if echo "$info" | grep -q MUTED; then
    dunstify -a "Volume" -u low -r 91190 -t 2000 -i audio-volume-muted-symbolic "Tắt tiếng"
else
    dunstify -a "Volume" -u low -r 91190 -t 2000 -h int:value:"$percent" \
        -i audio-volume-high-symbolic "Âm lượng: ${percent}%"
fi
