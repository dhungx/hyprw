# hyprw

Cấu hình đầy đủ: Hyprland (Lua, ≥0.55) + Waybar + hyprlock + hypridle + menu
nguồn tự viết (thay wlogout — lý do xem phần "Menu nguồn" bên dưới),
theme Catppuccin Mocha đồng bộ. Tối ưu cho laptop Intel + NVIDIA RTX 3050 hybrid.

## Quan trọng trước khi cài
Hyprland ≥0.55 (5/2026) đã đổi hẳn cấu hình sang **Lua**, bỏ cú pháp `.conf` cũ.
Nếu máy bạn đã có `~/.config/hypr/hyprland.conf` từ trước — **xoá nó đi**,
chỉ dùng `hyprland.lua` trong bộ này.

## Cài vào máy
Từ TTY (chưa cần vào GUI), clone repo rồi chạy đúng 1 file:
```bash
git clone --depth 1 https://github.com/dhungx/hyprw
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
                        osd-volume.sh + osd-brightness.sh (popup % khi chỉnh phím media),
                        power-menu.py (Super+M, xem phần "Menu nguồn")
btop/                 — resource monitor theme Catppuccin Mocha, alias thay htop
fcitx5/               — gõ tiếng Việt (Unikey) + tiếng Anh
wallpaper/            — 8 ảnh nền có sẵn, copy sang ~/.config/hypr/wallpapers/
waybar/               — thanh bar
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
| Super+M | Menu nguồn dạng bar (Super+M lần nữa hoặc Esc để đóng) |
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
- **Menu nguồn (Super+M) không còn dùng wlogout** — đọc thẳng mã nguồn
  (`ArtsyMacaw/wlogout/main.c`) xác nhận nó hardcode neo cả 4 cạnh màn hình
  (`for j in 4 edges: gtk_layer_set_anchor(win, j, TRUE)`), không có config
  nào đổi được — đây là giới hạn code gốc, không phải thiếu tuỳ chọn.
  `scripts/power-menu.py` viết bằng Python + PyGObject + `gtk-layer-shell`
  (dùng lại đúng thư viện waybar đã tải sẵn — không thêm framework mới như
  Quickshell/eww/AGS/Astal; đo thực tế Quickshell tốn ~400MB RAM + GPU
  trung bình 15%/đỉnh 50% so với GTK3 chỉ vài chục MB gần 0% GPU).

  **Hiệu ứng "3 viên thuốc gộp thành 1"** — bấm Super+M, 3 viên thuốc thật
  của waybar (workspaces / đồng hồ / system-pill+tray) trông như tự di
  chuyển + co giãn khít lại thành 1 viên thuốc dài giữa màn hình, rồi 5
  icon nguồn mờ dần hiện ra bên trong. Đã qua 2 bản, vài quyết định kỹ
  thuật quan trọng:
  - **Ẩn waybar thật bằng signal, không "che" giả lập** — bản đầu tạo 3
    overlay kích thước ước lượng để che khít lên 3 viên thuốc thật, ước
    lượng sai vài chục px là lộ 1 phần ra ngoài, thấy rõ lúc animation
    chạy. Bản này chuyển sang **ẩn thật** waybar qua `killall -SIGUSR1
    waybar` (waybar tự hỗ trợ qua key `"on-sigusr1": "hide"` /
    `"on-sigusr2": "show"` trong `config.jsonc` — xác nhận qua man page
    chính thức `waybar.5`, dùng giá trị tường minh thay vì mặc định
    `toggle`/`reload` vì `toggle` mặc định được chính người dùng Waybar
    báo cáo lệch trạng thái khi gửi signal dồn dập). Sau khi ẩn, không
    còn gì thật ở dưới để lộ ra — kích thước overlay từ đây chỉ còn ảnh
    hưởng thẩm mỹ, không còn gây lỗi hiển thị. `SIGUSR2` (hiện lại) được
    gửi đúng lúc animation đóng đã chạy ~80%, không đợi đóng hẳn — lúc đó
    overlay gần vô hình nên chồng lấp ngắn không ai nhận ra, còn đợi đóng
    hẳn mới gửi sẽ có 1 khoảng trống (không overlay, không waybar) rõ hơn.
    Lưu ý đã biết: waybar không tự báo trạng thái qua signal, nên
    `SIGUSR2` làm nó "show" có thể chớp/delay/IO nhẹ — ghi nhận từ 1 dự án
    có thật (`waybar_auto_hide`) dùng đúng kỹ thuật này, chấp nhận được,
    không phải lỗi code ở đây
  - **Mỗi cửa sổ chỉ tạo 1 lần, animate bằng `Gtk.Fixed` thay vì resize
    lặp lại** — bản đầu gọi `GtkLayerShell.set_margin()`/`resize()` mỗi
    khung hình (~20 lần/animation), mỗi lần là 1 vòng đàm phán thật với
    Wayland compositor. Bản này tạo mỗi cửa sổ đúng 1 lần ở kích thước
    hợp bao (union) của vị trí gốc + đích, bên trong dùng `Gtk.Fixed` di
    chuyển/đổi cỡ 1 widget con — thao tác nội bộ GTK, không đàm phán
    Wayland, nhẹ hơn nhiều
  - **Không dùng CSS transform để "bay"** — xác nhận qua mailing list
    chính thức GNOME (gtk-list, 05/2017) + docs.gtk.org/gtk3: GTK3 không
    có CSS `transform` cho widget thường (chỉ `-gtk-icon-transform` cho
    icon). Toàn bộ animation tween thẳng x/y/width/height qua
    `GLib.timeout_add`
  - **Chỉ 1 trong 3 cửa sổ (viên ở giữa) giữ nút bấm thật** — 2 viên
    trái/phải chỉ là nền màu phẳng, co nhỏ dần về 0 và ẩn đi ngay khi viên
    giữa phình to chiếm trọn viên thuốc gộp — đỡ phải chia 5 nút cắt ngang
    qua ranh giới 3 cửa sổ khác nhau. Cũng chỉ cửa sổ này nhận keyboard
    (`ON_DEMAND`) để phím Esc hoạt động — bản đầu vô tình đặt `NONE` cho
    cả 3, khiến Esc không bao giờ nhận được sự kiện, đã sửa
  - **Toạ độ 3 viên thuốc là ước lượng** — lấy độ phân giải màn hình qua
    `hyprctl monitors -j` (chọn đúng monitor có `"focused": true`, không
    mặc định monitor đầu/toạ độ (0,0) — quan trọng nếu dùng nhiều màn
    hình), còn bề rộng mỗi viên (`WORKSPACES_WIDTH`, `CLOCK_WIDTH`,
    `SYSTEM_TRAY_WIDTH` đầu file) là suy đoán theo layout đã biết, đánh
    dấu rõ trong code — giờ chỉ ảnh hưởng thẩm mỹ điểm bắt đầu animation
    (do đã ẩn waybar thật), không còn là chỗ rủi ro gây lỗi hiển thị nữa
  - **Icon `suspend` sửa lại** — mã cũ `\uf4ee` nhầm thuộc bộ Octicon,
    đổi sang `\uf186` (nf-fa-moon, "Power Sleep Symbol") cho đúng bộ Font
    Awesome dùng xuyên suốt các icon còn lại
  - **Xử lý bấm Super+M liên tục nhanh** — có theo dõi vị trí THẬT đang
    đứng mỗi khung hình (`state["current"]`) — nếu bấm đóng giữa lúc đang
    mở dở, tween ngược bắt đầu đúng từ vị trí dở dang đó, không nhảy cóc
    tới vị trí "đã gộp xong" trước rồi mới lùi lại
  - Không chạy nền thường trực — mỗi lần Super+M spawn mới, dùng file PID
    trong `$XDG_RUNTIME_DIR`; bấm lại thì gửi `SIGUSR1` cho tiến trình
    đang chạy để tự đóng, không mở thêm bản thứ 2. RAM = 0 khi không dùng
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
