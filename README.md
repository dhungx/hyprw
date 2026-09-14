# My Hyprland Dots — bản tối thiểu ngày 1

## Cài vào máy
```bash
mkdir -p ~/.config/hypr ~/.config/waybar
cp hypr/hyprland.conf ~/.config/hypr/hyprland.conf
cp hypr/hyprpaper.conf ~/.config/hypr/hyprpaper.conf
cp waybar/config.jsonc ~/.config/waybar/config.jsonc
cp waybar/style.css ~/.config/waybar/style.css
```

## Cài gói cần thiết
```bash
sudo pacman -S hyprland waybar dunst hyprpaper hypridle foot thunar fuzzel \
               grim slurp wl-clipboard wireplumber brightnessctl playerctl \
               pavucontrol networkmanager
```

## Trước khi chạy
1. Bỏ ảnh vào `~/Pictures/wallpaper.jpg`, hoặc comment 2 dòng trong hyprpaper.conf
   + dòng `exec-once = hyprpaper` trong hyprland.conf nếu chưa có ảnh.
2. Sau khi vào máy thật: `hyprctl monitors` để lấy đúng tên màn hình,
   sửa dòng `monitor=` đầu hyprland.conf cho đúng 144Hz.

## Phím tắt chính
- Super+Enter — mở terminal (foot)
- Super+R — mở launcher (fuzzel)
- Super+Q — đóng cửa sổ
- Super+E — file manager (thunar)
- Super+1..0 — chuyển workspace
- Super+Shift+1..0 — đẩy cửa sổ qua workspace khác
- Super+trái/phải/lên/xuống — di chuyển focus
