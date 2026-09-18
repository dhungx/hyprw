-- modules/Monitors.lua
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
