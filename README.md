# hyprw

Cấu hình đầy đủ: Hyprland (Lua, ≥0.55) + Waybar + hyprlock + hypridle + wlogout,
theme Catppuccin Mocha đồng bộ. Tối ưu cho laptop Intel + NVIDIA RTX 3050 hybrid.

## Quan trọng trước khi cài
Hyprland ≥0.55 (5/2026) đã đổi hẳn cấu hình sang **Lua**, bỏ cú pháp `.conf` cũ.
Nếu máy bạn đã có `~/.config/hypr/hyprland.conf` từ trước — **xoá nó đi**,
chỉ dùng `hyprland.lua` trong bộ này.

## Cài vào máy
```bash
mkdir -p ~/.config/hypr ~/.config/waybar ~/.config/wlogout ~/.config/gtk-3.0 ~/.config/gtk-4.0

cp hypr/hyprland.lua   ~/.config/hypr/hyprland.lua
cp hypr/hypridle.conf  ~/.config/hypr/hypridle.conf
cp hypr/hyprlock.conf  ~/.config/hypr/hyprlock.conf
cp hypr/hyprpaper.conf ~/.config/hypr/hyprpaper.conf

cp waybar/config.jsonc ~/.config/waybar/config.jsonc
cp waybar/style.css    ~/.config/waybar/style.css

cp wlogout/layout      ~/.config/wlogout/layout
cp wlogout/style.css   ~/.config/wlogout/style.css

cp gtk-3.0/settings.ini ~/.config/gtk-3.0/settings.ini
cp gtk-4.0/settings.ini ~/.config/gtk-4.0/settings.ini

mkdir -p ~/.config/fastfetch
cp fastfetch/config.jsonc ~/.config/fastfetch/config.jsonc

mkdir -p ~/.config/dunst ~/.config/fuzzel ~/.config/foot
cp dunst/dunstrc      ~/.config/dunst/dunstrc
cp fuzzel/fuzzel.ini  ~/.config/fuzzel/fuzzel.ini
cp foot/foot.ini      ~/.config/foot/foot.ini

cp shell/zshrc         ~/.zshrc
cp shell/starship.toml ~/.config/starship.toml
```

Đặt zsh làm shell mặc định (bắt buộc, không thì `.zshrc` không tự chạy khi mở terminal):
```bash
chsh -s /usr/bin/zsh
```
Đăng xuất/đăng nhập lại (hoặc mở terminal mới) để áp dụng.

## Cài package
```bash
sudo pacman -S hyprland waybar dunst hyprpaper hypridle hyprlock wlogout \
               foot thunar fuzzel cliphist \
               grim slurp wl-clipboard wireplumber brightnessctl playerctl \
               hyprpolkitagent qt6ct nwg-look papirus-icon-theme networkmanager \
               ttf-jetbrains-mono-nerd fastfetch \
               zsh zsh-autosuggestions zsh-syntax-highlighting starship

# Theme GTK (AUR — cần paru/yay)
paru -S catppuccin-gtk-theme-blue
```

## Việc cần làm sau khi cài
1. **Ảnh nền:** bỏ vào `~/Pictures/wallpaper.jpg` (dùng chung cho hyprpaper + hyprlock)
2. **Màn hình 144Hz:** `hyprctl monitors` lấy tên thật, sửa khối `hl.monitor({...})`
   đầu file `hyprland.lua`
3. **Theme Qt:** chạy `qt6ct` một lần, chọn theme tối trong GUI để app Qt đồng bộ
   với GTK
4. **NVIDIA hybrid — tránh Electron app (Discord/VSCode/Chrome) treo máy lúc boot:**
   sửa `/etc/mkinitcpio.conf`, dòng `MODULES=`, thêm `i915` **trước** các module
   nvidia:
   ```
   MODULES=(i915 nvidia nvidia_modeset nvidia_uvm nvidia_drm)
   ```
   Rồi chạy `sudo mkinitcpio -P` và reboot. Đây là lỗi rất hay gặp trên laptop
   Intel+NVIDIA, dễ tưởng nhầm là máy bị treo.

## Cấu trúc thư mục
```
hypr/hyprland.lua     — cấu hình chính: bind, animation, window rules (Lua)
hypr/hypridle.conf    — quản lý idle/khoá máy tự động (định dạng riêng, không Lua)
hypr/hyprlock.conf    — giao diện màn hình khoá (định dạng riêng, không Lua)
hypr/hyprpaper.conf   — hình nền
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
- Blur/animation đã bật sẵn (RTX 3050 dư sức) — muốn tắt cho nhẹ hơn nữa, sửa
  `blur.enabled = false` trong `hyprland.lua`
- hypridle tự tạm dừng khi trình duyệt/video player đang phát video hoặc game
  đang fullscreen (chuẩn Wayland idle-inhibit) — không cần lo màn hình tự khoá
  giữa lúc chơi game/xem phim với hầu hết app hiện đại
