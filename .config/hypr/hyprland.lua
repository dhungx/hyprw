--[[
════════════════════════════════════════════════════════════
HYPRLAND CONFIG — entry point, chỉ chứa require() tới từng module
Cú pháp LUA (Hyprland ≥0.55) — KHÔNG dùng được cú pháp .conf cũ

Mỗi require() là 1 scope Lua riêng biệt (lỗi ở 1 file không làm sập các
file khác) — đây là lý do chính thức Hyprland khuyên chia nhỏ, không chỉ
để dễ quản lý. Sửa module nào thì mở đúng file đó trong modules/, không
cần đụng vào file này.

Nếu bạn có file hyprland.conf cũ (bản .conf, không phải .lua) — XOÁ nó đi,
chỉ giữ cây modules/ này. Hyprland đọc ~/.config/hypr/hyprland.lua.
════════════════════════════════════════════════════════════
]]

require("modules.Monitors")
require("modules.ENVariables")
require("modules.Startup_Apps")
require("modules.LookAndFeel")
require("modules.Input")
require("modules.Keybinds")
require("modules.WindowRules")

--[[
════════════════════════════════════════════════════════════
CẦN CÀI (paru -S / pacman -S) để chạy đủ chức năng:

hyprland waybar dunst hyprpaper hypridle hyprlock wlogout
foot thunar fuzzel cliphist
grim slurp wl-clipboard wireplumber brightnessctl playerctl
hyprpolkitagent qt5ct qt6ct nwg-look
catppuccin-gtk-theme-blue (AUR)   -- hoặc đổi GTK_THEME trong ENVariables.lua

Chưa nằm trong Lua (định dạng RIÊNG, không phải Lua), làm theo README:
- hypridle.conf, hyprlock.conf, hyprpaper.conf
- waybar/config.jsonc + style.css
- wlogout/layout + style.css
- qt5ct/qt5ct.conf, qt6ct/qt6ct.conf
════════════════════════════════════════════════════════════
]]
