#!/usr/bin/env bash
# osd-brightness.sh up|down — chỉnh độ sáng qua brightnessctl, hiện OSD qua dunst

case "$1" in
    up)   brightnessctl -e4 -n2 set 5%+ > /dev/null ;;
    down) brightnessctl -e4 -n2 set 5%- > /dev/null ;;
    *) echo "Dùng: $0 up|down" >&2; exit 1 ;;
esac

# brightnessctl -m in ra: device,class,current,percent%,max — lấy thẳng cột
# percent, khỏi phải tự tính current/max*100 bằng tay
percent=$(brightnessctl -m | cut -d, -f4 | tr -d '%')

dunstify -a "Brightness" -u low -r 91191 -t 2000 -h int:value:"$percent" \
    -i display-brightness-symbolic "Độ sáng: ${percent}%"
