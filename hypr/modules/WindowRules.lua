-- modules/WindowRules.lua — window rules + layer rules
-- Fix lỗi kéo cửa sổ XWayland hay gặp (khuyến nghị chính thức từ Hyprland)
hl.window_rule({
    name = "fix-xwayland-drags",
    match = { class = "^$", title = "^$", xwayland = true, float = true, fullscreen = false, pin = false },
    no_focus = true,
})

-- Các app hay cần nổi (float) thay vì tile
hl.window_rule({ match = { class = "pavucontrol" }, float = true })
hl.window_rule({ match = { class = "nm-connection-editor" }, float = true })
hl.window_rule({ match = { title = "File Operation Progress" }, float = true })   -- hộp thoại copy/paste của Thunar

-- Picture-in-picture cho trình duyệt — luôn nổi, luôn trên cùng, góc nhỏ
hl.window_rule({
    match = { title = "Picture-in-Picture" },
    float = true,
    pin = true,
    size = "25% 25%",
    move = "onscreen 73% onscreen 73%",
})

-- Layer rules — blur cho bar/launcher/lock
hl.layer_rule({ match = { namespace = "waybar" }, blur = true })
hl.layer_rule({ match = { namespace = "fuzzel" }, blur = true })
hl.layer_rule({ match = { namespace = "wlogout" }, blur = true })
