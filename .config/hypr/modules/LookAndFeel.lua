-- modules/LookAndFeel.lua — general/decoration/animations/dwindle/misc
hl.config({
    general = {
        gaps_in = 4,
        gaps_out = 8,
        border_size = 2,
        col = {
            active_border = { colors = { "rgba(89b4faee)", "rgba(cba6f7ee)" }, angle = 45 },
            inactive_border = "rgba(45475aaa)",
        },
        resize_on_border = true,
        layout = "dwindle",
    },
    decoration = {
        rounding = 8,
        rounding_power = 2,
        active_opacity = 0.92,          -- cửa sổ đang dùng: trong suốt nhẹ, đủ thấy mờ phía sau
        inactive_opacity = 0.85,        -- cửa sổ không focus: trong suốt rõ hơn 1 chút, dễ phân biệt đang dùng cái nào
        fullscreen_opacity = 1.0,       -- fullscreen (video/game) LUÔN đặc — không áp dụng độ trong suốt ở trên
        shadow = {
            enabled = true,
            range = 4,
            render_power = 3,
            color = 0xaa1a1a1a,
        },
        blur = {
            enabled = true,             -- máy bạn (RTX 3050) dư sức, bật cho đẹp
            size = 4,
            passes = 2,
            vibrancy = 0.17,
        },
    },
    animations = {
        enabled = true,
    },
    dwindle = {
        preserve_split = true,
    },
    misc = {
        force_default_wallpaper = 0,     -- tắt wallpaper mascot mặc định của Hyprland
        disable_hyprland_logo = true,
        vfr = true,                      -- variable frame rate — tiết kiệm pin khi rảnh
    },
})

-- Đường cong animation — giữ mặc định chính thức, mượt và nhẹ
hl.curve("easeOutQuint", { type = "bezier", points = { { 0.23, 1 }, { 0.32, 1 } } })
hl.curve("linear", { type = "bezier", points = { { 0, 0 }, { 1, 1 } } })
hl.curve("easy", { type = "spring", mass = 1, stiffness = 71.26, dampening = 15.83 })

hl.animation({ leaf = "windows", enabled = true, speed = 4.79, spring = "easy" })
hl.animation({ leaf = "border", enabled = true, speed = 5.4, bezier = "easeOutQuint" })
hl.animation({ leaf = "fade", enabled = true, speed = 3, bezier = "linear" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 2, bezier = "linear", style = "fade" })
hl.animation({ leaf = "layers", enabled = true, speed = 3, bezier = "easeOutQuint" })
