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
Danh sách package đầy đủ + thứ tự cài: xem install.sh (nguồn duy nhất,
tránh 2 nơi ghi 2 danh sách rồi lệch nhau theo thời gian).

Các file KHÔNG phải Lua (định dạng riêng), tham khảo README:
- hypridle.conf, hyprlock.conf
- waybar/config.jsonc + style.css
- scripts/power-menu.py (thay wlogout — xem comment đầu file đó)
- qt5ct/qt5ct.conf, qt6ct/qt6ct.conf
════════════════════════════════════════════════════════════
]]
