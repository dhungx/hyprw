--[[
════════════════════════════════════════════════════════════
HYPRLAND CONFIG — bản "rice" hoàn chỉnh
Cú pháp LUA (Hyprland ≥0.55) — KHÔNG dùng được cú pháp .conf cũ
(bind = ..., general { } kiểu cũ đã bị khai tử từ bản 0.55, 5/2026)

Nếu bạn có file hyprland.conf cũ (bản mình đưa trước đây) — XOÁ nó đi,
chỉ giữ file .lua này. Hyprland sẽ đọc ~/.config/hypr/hyprland.lua.
════════════════════════════════════════════════════════════
]]

------------------
---- MÀN HÌNH ----
------------------
-- Để "preferred,auto,auto" lúc đầu. Sau khi vào máy thật, chạy
-- `hyprctl monitors` lấy đúng tên (vd eDP-1), sửa lại dòng dưới cho đúng 144Hz.
hl.monitor({
    output = "",
    mode = "preferred",
    position = "auto",
    scale = "auto",
})
-- Ví dụ khi đã biết tên thật (bỏ comment, xoá khối phía trên):
-- hl.monitor({ output = "eDP-1", mode = "1920x1080@144", position = "auto", scale = 1 })

---------------------
---- APP MẶC ĐỊNH ----
---------------------
local terminal = "foot"
local fileManager = "thunar"
local menu = "fuzzel"
local lockCmd = "hyprlock"

-------------------
---- AUTOSTART ----
-------------------
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

-------------------------------
---- BIẾN MÔI TRƯỜNG ----
-------------------------------
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("XCURSOR_THEME", "Adwaita")     -- đổi tên theme nếu cài theme cursor khác

-- Theme GTK/Qt đồng bộ (cần cài theme tương ứng qua pacman/AUR trước)
hl.env("GTK_THEME", "Catppuccin-Mocha-Standard-Blue-Dark")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")

-- ── Tối ưu GPU cho laptop hybrid (Intel iGPU + NVIDIA RTX 3050) ──
-- iHD = giải mã video bằng iGPU Intel, tiết kiệm pin, không giành VRAM với NVIDIA.
-- Dùng `prime-run <lệnh>` để ép app/game chạy bằng GPU rời khi cần hiệu năng.
hl.env("LIBVA_DRIVER_NAME", "iHD")

-- Nếu gặp lỗi màn hình đen / multi-monitor trên hybrid graphics, thử thêm
-- (không set sẵn vì tuỳ máy, chỉ set khi thật sự gặp lỗi):
-- hl.env("AQ_DRM_DEVICES", "/dev/dri/card1:/dev/dri/card0")

-----------------------
---- GIAO DIỆN ----
-----------------------
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
        active_opacity = 1.0,
        inactive_opacity = 0.95,        -- cửa sổ không focus hơi mờ nhẹ — dấu hiệu "sạch" dễ nhận
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

---------------
---- INPUT ----
---------------
hl.config({
    input = {
        kb_layout = "us",
        follow_mouse = 1,
        sensitivity = 0,
        touchpad = {
            natural_scroll = true,
            tap_to_click = true,
        },
    },
})

---------------------
---- PHÍM TẮT ----
---------------------
local mainMod = "SUPER"

-- App cơ bản
hl.bind(mainMod .. " + RETURN", hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + Q", hl.dsp.window.close())
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd(menu))
hl.bind(mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + P", hl.dsp.window.pseudo())
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit"))
hl.bind(mainMod .. " + F", hl.dsp.exec_cmd("hyprctl dispatch fullscreen 0"))

-- Khoá máy / đăng xuất (cần cài: hyprlock, wlogout)
hl.bind(mainMod .. " + L", hl.dsp.exec_cmd(lockCmd))
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("wlogout"))

-- Di chuyển focus
hl.bind(mainMod .. " + left", hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up", hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down", hl.dsp.focus({ direction = "down" }))

-- Workspace 1-10 + đẩy cửa sổ qua workspace khác
for i = 1, 10 do
    local key = i % 10
    hl.bind(mainMod .. " + " .. key, hl.dsp.focus({ workspace = i }))
    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }))
end

-- Scratchpad (workspace ẩn, tiện thả app phụ như nhạc/note)
hl.bind(mainMod .. " + S", hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))

-- Chuyển workspace bằng lăn chuột
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))

-- Kéo / resize cửa sổ bằng chuột
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Clipboard history (cần cài: cliphist)
hl.bind(mainMod .. " + C", hl.dsp.exec_cmd("cliphist list | fuzzel --dmenu | cliphist decode | wl-copy"))

-- Screenshot (cần cài: grim, slurp, wl-clipboard)
hl.bind("", "PRINT", hl.dsp.exec_cmd("grim -g \"$(slurp)\" - | wl-copy"))
hl.bind(mainMod .. " + PRINT", hl.dsp.exec_cmd("grim - | wl-copy"))   -- chụp toàn màn hình

-- Volume / Brightness (locked+repeating = giữ phím vẫn tăng/giảm liên tục)
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), { locked = true, repeating = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), { locked = true })
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), { locked = true, repeating = true })

-- Media keys (cần cài: playerctl)
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })

--------------------------------
---- WINDOW RULES ----
--------------------------------
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

--------------------------------
---- LAYER RULES (blur cho bar/launcher/lock) ----
--------------------------------
hl.layer_rule({ match = { namespace = "waybar" }, blur = true })
hl.layer_rule({ match = { namespace = "fuzzel" }, blur = true })
hl.layer_rule({ match = { namespace = "wlogout" }, blur = true })

--[[
════════════════════════════════════════════════════════════
CẦN CÀI (paru -S / pacman -S) để file này chạy đủ chức năng:

hyprland waybar dunst hyprpaper hypridle hyprlock wlogout
foot thunar fuzzel cliphist
grim slurp wl-clipboard wireplumber brightnessctl playerctl
hyprpolkitagent qt6ct nwg-look
catppuccin-gtk-theme-blue (AUR)   -- hoặc đổi GTK_THEME ở trên theo theme bạn thích

Chưa có trong file này, làm riêng theo hướng dẫn kèm theo:
- hypridle.conf, hyprlock.conf, hyprpaper.conf (định dạng RIÊNG, không phải Lua)
- waybar/config.jsonc + style.css
- wlogout/layout + style.css
════════════════════════════════════════════════════════════
]]
