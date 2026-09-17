-- modules/Startup_Apps.lua
hl.on("hyprland.start", function()
    -- Export biến môi trường vào systemd + D-Bus activation environment.
    -- BẮT BUỘC để xdg-desktop-portal-hyprland tìm đúng config theo tên desktop
    -- và hoạt động đúng — thiếu dòng này là nguyên nhân phổ biến nhất khiến
    -- screen share qua Zoom/OBS/Discord không chạy được trên Hyprland.
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE")
    hl.exec_cmd("waybar")
    hl.exec_cmd("awww-daemon")
    -- Nạp wallpaper đang chọn ngay khi khởi động — --transition-type none vì
    -- đây là lần vẽ đầu tiên, chưa có gì để "chuyển từ" nên không cần animation
    hl.exec_cmd("sleep 0.5 && awww img ~/.config/hypr/wallpapers/current.jpg --transition-type none")
    hl.exec_cmd("hypridle")
    hl.exec_cmd("dunst")
    hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
    hl.exec_cmd("wl-paste --watch cliphist store")   -- nạp clipboard history nền
end)
