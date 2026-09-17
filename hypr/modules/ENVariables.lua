-- modules/ENVariables.lua
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("XCURSOR_THEME", "Adwaita")     -- đổi tên theme nếu cài theme cursor khác

-- Theme GTK/Qt đồng bộ (cần cài theme tương ứng qua pacman/AUR trước)
hl.env("GTK_THEME", "Catppuccin-Mocha-Standard-Blue-Dark")
-- QUAN TRỌNG: giá trị PHẢI là "qt5ct" (không phải "qt6ct") để theme được CẢ
-- app Qt5 lẫn Qt6 — qt6ct được thiết kế để tự nhận diện giá trị "qt5ct" và áp
-- dụng theme cho app Qt6 luôn. Set thành "qt6ct" sẽ làm app Qt5 mất theme.
hl.env("QT_QPA_PLATFORMTHEME", "qt5ct")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")           -- ưu tiên Wayland, dự phòng XWayland
hl.env("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1") -- tránh app Qt tự vẽ thanh title xấu

-- Gõ tiếng Việt (fcitx5 + Unikey) — cần cho GTK/Qt/SDL nhận đúng input method
hl.env("GTK_IM_MODULE", "fcitx")
hl.env("QT_IM_MODULE", "fcitx")
hl.env("XMODIFIERS", "@im=fcitx")
hl.env("SDL_IM_MODULE", "fcitx")

-- ── Tối ưu GPU cho laptop hybrid (Intel iGPU + NVIDIA RTX 3050) ──
-- iHD = giải mã video bằng iGPU Intel, tiết kiệm pin, không giành VRAM với NVIDIA.
-- Dùng `prime-run <lệnh>` để ép app/game chạy bằng GPU rời khi cần hiệu năng.
hl.env("LIBVA_DRIVER_NAME", "iHD")

-- Nếu gặp lỗi màn hình đen / multi-monitor trên hybrid graphics, thử thêm
-- (không set sẵn vì tuỳ máy, chỉ set khi thật sự gặp lỗi):
-- hl.env("AQ_DRM_DEVICES", "/dev/dri/card1:/dev/dri/card0")
