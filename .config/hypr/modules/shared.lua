-- modules/shared.lua
-- Giá trị dùng chung giữa nhiều module — mỗi file require() là 1 scope Lua
-- riêng, "local" khai ở file khác KHÔNG thấy được ở đây, nên phải qua file
-- này. Module nào cần dùng thì: local shared = require("modules.shared")

return {
    terminal    = "foot",
    fileManager = "thunar",
    menu        = "fuzzel",
    lockCmd     = "hyprlock",
    mainMod     = "SUPER",
}
