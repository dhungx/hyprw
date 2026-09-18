# hyprw

Cấu hình đầy đủ: Hyprland (Lua, ≥0.55) + Waybar + hyprlock + hypridle + wlogout,
theme Catppuccin Mocha đồng bộ. Tối ưu cho laptop Intel + NVIDIA RTX 3050 hybrid.

## Quan trọng trước khi cài
Hyprland ≥0.55 (5/2026) đã đổi hẳn cấu hình sang **Lua**, bỏ cú pháp `.conf` cũ.
Nếu máy bạn đã có `~/.config/hypr/hyprland.conf` từ trước — **xoá nó đi**,
chỉ dùng `hyprland.lua` trong bộ này.

## Cài vào máy
Từ TTY (chưa cần vào GUI), clone repo rồi chạy đúng 1 file:
```bash
git clone <url-repo-của-bạn> hyprw
cd hyprw
chmod +x install.sh
./install.sh
```
Script tự lo: cài package (pacman + AUR qua yay, tự bootstrap yay nếu chưa có),
backup config cũ nếu có, copy `.config/` vào `~/.config/`, copy `zshrc` vào
`~/.zshrc`, copy wallpaper + tạo symlink `current.jpg` mặc định, symlink theme
GTK4, đặt zsh làm shell mặc định, cài session `hyprw` cho SDDM + bật SDDM.
Xong thì `reboot` — ở màn hình đăng nhập SDDM, chọn session **"hyprw"** trước
khi gõ mật khẩu (không phải "Hyprland" mặc định).

Cấu trúc repo:
```
install.sh      — chạy 1 lần duy nhất lúc cài mới
.config/        — copy y nguyên cấu trúc sang ~/.config/ (kể cả starship.toml,
                   nằm trực tiếp trong .config/ vì đó đúng là đích thật của nó)
zshrc           — KHÔNG nằm trong .config/ vì đích thật là ~/.zshrc, không phải
                   ~/.config/zshrc — install.sh tự copy đúng chỗ
wallpaper/      — để ngoài .config/ cho gọn repo (ảnh nặng, không phải "config"),
                   install.sh tự copy vào ~/.config/hypr/wallpapers/ lúc cài
sddm/           — session hyprw.desktop, install.sh tự cài vào
                   /usr/share/wayland-sessions/ (thư mục hệ thống, không phải
                   ~/.config nên tách riêng khỏi cây .config/ ở trên)
```

Việc duy nhất **không** nằm trong `install.sh` (cố ý bỏ ngoài, rủi ro cao nếu
tự động hoá sai): driver GPU, đặc biệt NVIDIA — cần cài sẵn trước khi chạy script.

## Việc cần làm sau khi cài (không script hoá được, tuỳ máy mỗi người)
1. **Màn hình 144Hz:** `hyprctl monitors` lấy tên thật, sửa khối `hl.monitor({...})`
   trong `~/.config/hypr/modules/Monitors.lua`
2. **NVIDIA hybrid — tránh Electron app (Discord/VSCode/Chrome) treo máy lúc boot:**
   sửa `/etc/mkinitcpio.conf`, dòng `MODULES=`, thêm `i915` **trước** các module
   nvidia:
   ```
   MODULES=(i915 nvidia nvidia_modeset nvidia_uvm nvidia_drm)
   ```
   Rồi chạy `sudo mkinitcpio -P` và reboot. Đây là lỗi rất hay gặp trên laptop
   Intel+NVIDIA, dễ tưởng nhầm là máy bị treo.

## Cấu trúc thư mục
```
hypr/hyprland.lua     — entry point, chỉ có require() tới từng module
hypr/modules/         — Monitors, ENVariables, Startup_Apps, LookAndFeel,
                        Input, Keybinds, WindowRules — mỗi thứ 1 file riêng
                        (kiểu chia của JaKooLit/KooL, sửa module nào mở
                        đúng file đó, không cần đụng hyprland.lua)
hypr/hypridle.conf    — quản lý idle/khoá máy tự động (định dạng riêng, không Lua)
hypr/hyprlock.conf    — giao diện màn hình khoá (định dạng riêng, không Lua)
hypr/scripts/         — wallpaper-select.sh (Super+W), ime-select.sh (Super+Shift+Space),
                        osd-volume.sh + osd-brightness.sh (popup % khi chỉnh phím media)
btop/                 — resource monitor theme Catppuccin Mocha, alias thay htop
fcitx5/               — gõ tiếng Việt (Unikey) + tiếng Anh
wallpaper/            — 8 ảnh nền có sẵn, copy sang ~/.config/hypr/wallpapers/
waybar/               — thanh bar
wlogout/              — menu nguồn (khoá/đăng xuất/tắt máy)
gtk-3.0, gtk-4.0/     — đồng bộ theme cho app GTK
```

## Phím tắt đầy đủ
| Phím | Chức năng |
|---|---|
| Super+Enter | Mở terminal (foot) |
| Super+R | App launcher (fuzzel) |
| Super+E | File manager (thunar) |
| Super+Q | Đóng cửa sổ |
| Super+V | Bật/tắt cửa sổ nổi |
| Super+F | Fullscreen |
| Super+P | Pseudo-tile |
| Super+J | Đổi hướng chia dwindle |
| Super+L | Khoá máy |
| Super+M | Menu nguồn (wlogout) |
| Super+C | Clipboard history |
| Super+W | **Đổi wallpaper runtime** — mở picker, chọn ảnh, chuyển có animation ngay, không cần sửa file/reload |
| Super+Space | **Đổi nhanh Anh ↔ Việt** (fcitx5 xử lý trực tiếp, hoạt động mọi app) |
| Super+Shift+Space | **Mở bảng chọn ngôn ngữ gõ cụ thể** (menu fuzzel) |
| Super+trái/phải/lên/xuống | Di chuyển focus |
| Super+1..0 | Chuyển workspace |
| Super+Shift+1..0 | Đẩy cửa sổ qua workspace khác |
| Super+S | Workspace ẩn (scratchpad) |
| Super+Shift+S | Đẩy cửa sổ vào scratchpad |
| Super+lăn chuột | Chuyển workspace |
| Super+chuột trái kéo | Di chuyển cửa sổ |
| Super+chuột phải kéo | Resize cửa sổ |
| PrintScreen | Chụp vùng chọn |
| Super+PrintScreen | Chụp toàn màn hình |
| Phím Volume/Brightness/Media | Tự động, có sẵn |

## Ghi chú
- **Đăng nhập:** cài xong chọn session **"hyprw"** ở màn hình SDDM (không
  phải "Hyprland" mặc định) — `install.sh` đã tự cài file session + bật
  SDDM, không cần làm gì thêm
- **Bar dạng "gọn động":** cụm CPU/RAM/volume/mạng/pin mặc định chỉ hiện
  icon — di chuột vào mới trượt ra số liệu đầy đủ (dùng tính năng
  `group`+`drawer` chính thức của waybar, GtkRevealer vẽ animation, không
  cần script/daemon phụ). Đồng hồ tương tự: gọn chỉ giờ:phút, hover ra
  thứ/ngày/tháng. Đây là hành vi cố ý, không phải bar bị thiếu số liệu
- Icon trên bar dùng glyph Nerd Font (không emoji) — cần font
  `ttf-jetbrains-mono-nerd` đã có trong danh sách cài ở trên. Mã icon đã đối
  chiếu trực tiếp với dữ liệu gốc `github.com/ryanoasis/nerd-fonts` (không
  đoán từ trí nhớ). Icon volume/battery/WiFi tự đổi theo dữ liệu thật (%
  volume, % pin, cường độ tín hiệu), không phải icon tĩnh
- Icon WiFi dùng đúng hình quạt sóng chuẩn (Material Design Icons
  `wifi_strength_1..4` + `wifi_strength_off` khi mất mạng, mã U+F091F–U+F092D)
  — 5 trạng thái, đổi theo cường độ tín hiệu thật, không còn chữ. Đây là icon
  nằm ở vùng mã 5-hex-digit nên chèn thẳng ký tự Unicode trong file, không
  dùng escape `\uXXXX` như các icon khác (JSON chỉ hỗ trợ 4 hex cho escape).
  Nếu thấy ô vuông trống thay vì icon → font chưa cài đúng, kiểm tra
  `fc-list | grep -i nerd`
- `fastfetch/config.jsonc` hiện 11 module: OS, Kernel, Uptime, Packages,
  Shell, WM, Terminal, CPU, GPU, Memory, Disk
- `dunst`, `fuzzel`, `foot` đã có theme Catppuccin Mocha riêng (trước đây có
  cài nhưng chưa có config — sẽ hiện giao diện mặc định nếu thiếu 3 file này)
- zsh dùng `zsh-autosuggestions` + `zsh-syntax-highlighting` (source đúng
  path pacman cài, tự bỏ qua nếu chưa cài, không lỗi) + prompt `starship`
  theme cùng bảng màu. Nhớ chạy `chsh -s /usr/bin/zsh` — chỉ cài package
  không tự đổi shell mặc định
- `wlogout` giờ dùng icon Nerd Font thật (đặt trong field `text` của layout,
  hiển thị như label thật — không phải PNG hay CSS content ảo), đồng bộ với
  waybar
- `portals.conf` + dòng `dbus-update-activation-environment` trong
  `hyprland.lua` — cần cả 2 để screen share qua Zoom/OBS/Discord chạy đúng.
  Thiếu export biến môi trường vào systemd là nguyên nhân phổ biến nhất gây
  lỗi portal trên Hyprland, không chỉ riêng thiếu file portals.conf
- `qt5ct`/`qt6ct`: biến `QT_QPA_PLATFORMTHEME` set thành **"qt5ct"** (không
  phải "qt6ct") — qt6ct tự nhận diện giá trị này để theme luôn cả app Qt6, set
  ngược lại sẽ làm app Qt5 mất theme. Cả 2 đã có sẵn `qt5ct.conf`/`qt6ct.conf`
  + file màu Catppuccin Mocha khớp đúng bảng màu dùng xuyên suốt rice, không
  cần tự mở GUI chỉnh tay
- **Đổi wallpaper runtime (Super+W):** dùng `awww` thay `hyprpaper` — hyprpaper
  không hỗ trợ animation chuyển cảnh, đổi tức thì. `awww` là bản đổi tên của
  `swww` (đổi tên 10/2025, chuyển qua Codeberg) — trên Arch hiện tại package
  tên `swww` sẽ tự trỏ sang `awww`, nhưng lệnh thật là `awww`/`awww-daemon`,
  KHÔNG phải `swww`/`swww-daemon`. Script trong repo này đã dùng đúng tên mới.
  Về an toàn tài nguyên: `awww img` chỉ gửi lệnh cho `awww-daemon` (vốn chạy
  nền sẵn để hiện wallpaper tĩnh, không phải process mới) rồi thoát ngay —
  animation chạy đúng trong khoảng `--transition-duration` (1.2s) bên trong
  daemon đó rồi tự về trạng thái idle bình thường, không có gì bị bỏ lại chạy
  thêm sau khi chuyển xong
- Cấu hình Hyprland đã chia theo module (`hypr/modules/`), giống kiểu
  JaKooLit/KooL — sửa gì thì mở đúng file đó (`Keybinds.lua` cho phím tắt,
  `WindowRules.lua` cho window rules...), `hyprland.lua` chỉ còn
  `require()`. 1 lưu ý kỹ thuật: mỗi file `require()` là 1 scope Lua riêng
  — biến dùng chung (`terminal`, `mainMod`...) nằm ở `modules/shared.lua`,
  module nào cần thì tự `require("modules.shared")`, không tự thấy biến
  của file khác
- **OSD volume/brightness:** dùng thẳng `dunst` đã cài sẵn (`dunstify -h
  int:value:N`) để vẽ progress bar thật trong notification — không cần cài
  thêm package OSD riêng (swayosd, wob...). Cờ `-r <id cố định>` trong 2
  script làm notification mới đè lên cũ thay vì xếp chồng khi bấm liên tục
- **Gõ tiếng Việt:** `fcitx5/profile` đã khai sẵn 2 IME (`keyboard-us` +
  `unikey`), không cần tự mở `fcitx5-configtool` thêm tay. `Super+space` đổi
  nhanh 2 chiều (do chính fcitx5 xử lý qua `Hotkey/TriggerKeys`, hoạt động ở
  mọi app kể cả khi Hyprland không cần biết). `Super+Shift+Space` mở menu
  fuzzel chọn thẳng ngôn ngữ, dùng `fcitx5-remote -s <tên>` phía sau. Nếu sau
  khi cài gõ tiếng Việt không lên (tên IME `unikey` có thể lệch giữa các bản
  đóng gói), mở `fcitx5-configtool` 1 lần, vào tab Input Method xem tên chính
  xác Unikey hiện ra là gì rồi sửa lại `fcitx5/profile` + `ime-select.sh` cho
  khớp
- **`btop`** thay `htop`/`top` — file theme lấy nguyên văn từ repo chính thức
  `catppuccin/btop` (không tự đoán màu), alias `htop`/`top` trong `.zshrc` đã
  trỏ sang `btop` luôn nên gõ thói quen cũ vẫn ra đúng app mới
- Blur/animation đã bật sẵn (RTX 3050 dư sức) — muốn tắt cho nhẹ hơn nữa, sửa
  `blur.enabled = false` trong `hypr/modules/LookAndFeel.lua`
- hypridle tự tạm dừng khi trình duyệt/video player đang phát video hoặc game
  đang fullscreen (chuẩn Wayland idle-inhibit) — không cần lo màn hình tự khoá
  giữa lúc chơi game/xem phim với hầu hết app hiện đại
- **Sửa lỗi khi viết `install.sh`:** README bản trước ghi gói `hyprpolkitagent`,
  nhưng `Startup_Apps.lua` lại gọi thẳng đường dẫn
  `/usr/lib/polkit-kde-authentication-agent-1` — đây là 2 package KHÁC NHAU
  (`hyprpolkitagent` là agent tối giản riêng của Hyprland, nằm ở path khác).
  Cài `hyprpolkitagent` theo README cũ thì dòng exec đó sẽ gọi vào file không
  tồn tại → polkit không chạy, GUI xin quyền admin sẽ không hiện ra bao giờ.
  `install.sh` đã sửa đúng thành gói `polkit-kde-agent` (khớp path thật đang
  dùng). Gói `cliphist`, `playerctl`, `thunar`, `gvfs` cũng bị thiếu trong
  danh sách cài ở README bản trước dù được dùng thật trong `Keybinds.lua`/
  `shared.lua` — `install.sh` đã bổ sung đủ.
