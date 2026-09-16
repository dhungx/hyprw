-- modules/Startup_Apps.lua
hl.on("hyprland.start", function()
    -- Export biến môi trường vào systemd + D-Bus activation environment.
    -- BẮT BUỘC để xdg-desktop-portal-hyprland tìm đúng config theo tên desktop
    -- và hoạt động đúng — thiếu dòng này là nguyên nhân phổ biến nhất khiến
    -- screen share qua Zoom/OBS/Discord không chạy được trên Hyprland.
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE")
    hl.exec_cmd("waybar")
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("hypridle")
    hl.exec_cmd("dunst")
    hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
    hl.exec_cmd("wl-paste --watch cliphist store")   -- nạp clipboard history nền
end)
