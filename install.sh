#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# install.sh — cài đặt hyprw từ TTY (chưa có GUI)
#
# Giả định trước khi chạy:
#   - Arch Linux đã cài xong phần nền (base, network, user thường có sudo)
#   - Driver GPU (đặc biệt NVIDIA) đã cài sẵn — script này KHÔNG đụng tới
#     driver, vì chọn sai driver có thể làm hỏng cả máy, ngoài phạm vi 1
#     script dotfiles nên cố tình bỏ qua thay vì đoán bừa.
#   - Đang đăng nhập bằng user thường (KHÔNG chạy script này bằng root)
#
# Sau khi chạy xong + reboot: chọn session "hyprw" ở màn hình đăng nhập SDDM.
#
# Chạy:  chmod +x install.sh && ./install.sh
# ══════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Màu + log ──────────────────────────────────────────────────────
C_GREEN='\033[0;32m'; C_YELLOW='\033[1;33m'; C_RED='\033[0;31m'; C_BLUE='\033[0;34m'; C_RESET='\033[0m'
log()  { echo -e "${C_BLUE}[*]${C_RESET} $1"; }
ok()   { echo -e "${C_GREEN}[✓]${C_RESET} $1"; }
warn() { echo -e "${C_YELLOW}[!]${C_RESET} $1"; }
die()  { echo -e "${C_RED}[✗] $1${C_RESET}" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.hyprw-backup-$(date +%Y%m%d-%H%M%S)"

# ── 0. Kiểm tra điều kiện trước khi làm gì cả ───────────────────────
[ "$EUID" -eq 0 ] && die "Đừng chạy bằng root — chạy bằng user thường, script sẽ tự dùng sudo khi cần."
command -v pacman >/dev/null 2>&1 || die "Không thấy pacman — script này chỉ chạy trên Arch Linux (hoặc distro dựa trên Arch)."
[ -d "$SCRIPT_DIR/.config" ] || die "Không thấy thư mục .config/ cạnh install.sh — chạy script ngay trong thư mục repo đã clone."
ping -c1 -W3 archlinux.org >/dev/null 2>&1 || die "Không có mạng — cần mạng để tải gói. Kiểm tra lại kết nối rồi chạy lại."

log "Bắt đầu cài hyprw. Sẽ hỏi mật khẩu sudo 1 lần, sau đó chạy không cần ngồi canh."
sudo -v
# Giữ sudo "sống" xuyên suốt, khỏi bị hỏi lại giữa chừng khi cài lâu
( while true; do sudo -n true; sleep 60; kill -0 "$$" 2>/dev/null || exit; done ) &
SUDO_KEEPALIVE_PID=$!
trap 'kill "$SUDO_KEEPALIVE_PID" 2>/dev/null || true' EXIT

# ── 1. Backup config cũ (nếu có) trước khi ghi đè ───────────────────
log "Sao lưu config cũ (nếu có) vào $BACKUP_DIR ..."
mkdir -p "$BACKUP_DIR"
NEED_BACKUP=(hypr waybar dunst fuzzel foot gtk-3.0 gtk-4.0 wlogout fastfetch qt5ct qt6ct fcitx5 xdg-desktop-portal btop starship.toml)
for item in "${NEED_BACKUP[@]}"; do
    if [ -e "$HOME/.config/$item" ]; then
        mkdir -p "$BACKUP_DIR/.config"
        cp -r "$HOME/.config/$item" "$BACKUP_DIR/.config/"
    fi
done
[ -f "$HOME/.zshrc" ] && cp "$HOME/.zshrc" "$BACKUP_DIR/zshrc.bak"
ok "Đã backup xong (nếu trước đó có gì thì giờ nằm ở $BACKUP_DIR, không mất gì cả)."

# ── 2. Cài gói chính thức (pacman, không cần AUR) ───────────────────
log "Cài các gói chính thức qua pacman (có thể mất vài phút)..."
PACMAN_PKGS=(
    # Hyprland ecosystem
    hyprland hyprland-guiutils hyprlock hypridle sddm
    xdg-desktop-portal-hyprland xdg-desktop-portal-gtk
    polkit polkit-kde-agent
    # Bar / thông báo / launcher / terminal
    waybar dunst fuzzel foot
    # Tiện ích phiên làm việc
    grim slurp wl-clipboard brightnessctl awww cliphist playerctl
    thunar gvfs
    # Trình duyệt (Super+B, cũng ghim sẵn trong dock.py)
    firefox
    # Menu nguồn tự viết (xem .config/hypr/scripts/power-menu.py) — dùng
    # lại đúng gtk-layer-shell mà waybar đã tải sẵn, không thêm framework
    # mới nào (không eww/AGS/Astal) để giữ nhẹ
    python-gobject gtk-layer-shell
    # Wifi + Bluetooth kiểu Windows Quick Settings (xem
    # .config/hypr/scripts/quick-settings.py) — dùng nmcli/bluetoothctl,
    # không cần applet nền (nm-applet/blueman). network-manager-applet chỉ
    # để có sẵn nm-connection-editor (rule float trong WindowRules.lua) làm
    # phương án dự phòng cho cấu hình nâng cao mà quick-settings.py CHƯA hỗ
    # trợ (IP tĩnh, VPN, 802.1x...)
    networkmanager network-manager-applet bluez bluez-utils
    # Âm thanh (PipeWire)
    pipewire pipewire-pulse pipewire-alsa wireplumber
    # Theming
    qt5ct qt6ct papirus-icon-theme ttf-jetbrains-mono-nerd
    # Gõ tiếng Việt
    fcitx5 fcitx5-gtk fcitx5-qt fcitx5-unikey fcitx5-configtool
    # Shell
    zsh starship zsh-autosuggestions zsh-syntax-highlighting
    # Theo dõi hệ thống
    fastfetch btop
    # Cần để build gói AUR ở bước sau
    git base-devel
)
sudo pacman -Syu --needed --noconfirm "${PACMAN_PKGS[@]}"
ok "Xong phần gói chính thức."

# ── 3. Bootstrap yay (AUR helper) nếu máy chưa có ───────────────────
if ! command -v yay >/dev/null 2>&1; then
    log "Chưa có yay — cài yay để lấy 2-3 gói chỉ có trên AUR (theme GTK)..."
    tmp_yay="$(mktemp -d)"
    git clone --depth 1 https://aur.archlinux.org/yay-bin.git "$tmp_yay/yay-bin"
    (cd "$tmp_yay/yay-bin" && makepkg -si --noconfirm)
    rm -rf "$tmp_yay"
    ok "Đã cài yay."
else
    ok "Đã có yay sẵn, bỏ qua bước cài."
fi

# ── 4. Cài gói AUR (chỉ 1 gói duy nhất cần AUR — theme GTK Catppuccin) ─
log "Cài theme GTK Catppuccin (AUR, không có trên repo chính thức)..."
yay -S --needed --noconfirm catppuccin-gtk-theme-mocha
ok "Xong phần AUR."

# ── 5. Copy toàn bộ .config/ vào ~/.config/ ─────────────────────────
log "Copy config vào ~/.config/ ..."
mkdir -p "$HOME/.config"
cp -rT "$SCRIPT_DIR/.config" "$HOME/.config"
ok "Đã copy .config/."

# zshrc là ngoại lệ CỐ Ý: đích thật của nó là ~/.zshrc, KHÔNG phải
# ~/.config/zshrc (zsh không tự đọc config từ trong .config), nên file
# này được để riêng ở gốc repo và copy thẳng vào đúng chỗ ở đây.
cp "$SCRIPT_DIR/zshrc" "$HOME/.zshrc"
ok "Đã copy zshrc -> ~/.zshrc."

# ── 6. Wallpaper: copy ra ~/.config/hypr/wallpapers/ + đặt ảnh mặc định ─
log "Copy wallpaper..."
WALLPAPER_DIR="$HOME/.config/hypr/wallpapers"
mkdir -p "$WALLPAPER_DIR"
cp "$SCRIPT_DIR"/wallpaper/*.jpg "$SCRIPT_DIR"/wallpaper/*.jpeg "$WALLPAPER_DIR/" 2>/dev/null || true
# "current.jpg" là SYMLINK (đúng cơ chế wallpaper-select.sh dùng), không phải
# file copy riêng — trỏ sẵn vào 1 ảnh mặc định, Super+W sau này đổi lại được.
DEFAULT_WALLPAPER="$WALLPAPER_DIR/river_to_castle_theme_blue.jpeg"
[ -f "$DEFAULT_WALLPAPER" ] && ln -sfn "$DEFAULT_WALLPAPER" "$WALLPAPER_DIR/current.jpg"
ok "Đã copy $(find "$WALLPAPER_DIR" -maxdepth 1 -name '*.jp*g' | wc -l) ảnh wallpaper."

# ── 7. Fix theme GTK4 — cần symlink thủ công, riêng settings.ini là CHƯA ĐỦ ─
# (GTK3 chỉ cần gtk-theme-name trong settings.ini là đủ; GTK4 cần thêm
#  gtk.css/gtk-dark.css/assets được symlink vào ~/.config/gtk-4.0/ —
#  đây là bước hay bị bỏ sót, kể cả trong các bản review trước của bộ này)
log "Symlink theme cho GTK4..."
THEME_DIR="/usr/share/themes/Catppuccin-Mocha-Standard-Blue-Dark"
if [ -d "$THEME_DIR" ]; then
    mkdir -p "$HOME/.themes"
    ln -sfn "$THEME_DIR" "$HOME/.themes/Catppuccin-Mocha-Standard-Blue-Dark"
    if [ -d "$THEME_DIR/gtk-4.0" ]; then
        ln -sfn "$THEME_DIR/gtk-4.0/assets" "$HOME/.config/gtk-4.0/assets"
        ln -sfn "$THEME_DIR/gtk-4.0/gtk.css" "$HOME/.config/gtk-4.0/gtk.css"
        ln -sfn "$THEME_DIR/gtk-4.0/gtk-dark.css" "$HOME/.config/gtk-4.0/gtk-dark.css"
        ok "Đã symlink GTK4 theme."
    else
        warn "Gói theme không có thư mục gtk-4.0/ — app GTK4 có thể không lên đúng theme, GTK3 vẫn ổn."
    fi
else
    warn "Không thấy $THEME_DIR — kiểm tra lại gói catppuccin-gtk-theme-mocha đã cài đúng chưa."
fi

# ── 8. Đặt zsh làm shell mặc định ────────────────────────────────────
if [ "$(basename "$SHELL")" != "zsh" ]; then
    log "Đặt zsh làm shell mặc định..."
    # sudo chsh (không phải chsh trần) — chsh trần sẽ hỏi LẠI mật khẩu đăng
    # nhập của chính bạn qua PAM, phá vỡ lời hứa "chỉ hỏi mật khẩu 1 lần"
    sudo chsh -s /usr/bin/zsh "$(whoami)" || warn "Đổi shell thất bại — tự chạy 'chsh -s /usr/bin/zsh' sau cũng được."
else
    ok "zsh đã là shell mặc định."
fi

# ── 9. Bật NetworkManager + Bluetooth (cần cho quick-settings.py) ──────
for svc in NetworkManager.service bluetooth.service; do
    if ! systemctl is-enabled "$svc" >/dev/null 2>&1; then
        log "Bật $svc..."
        sudo systemctl enable --now "$svc"
        ok "Đã bật $svc."
    else
        ok "$svc đã được bật từ trước, bỏ qua."
    fi
done

# ── 10. Session SDDM ─────────────────────────────────────────────────
# Dùng "start-hyprland" (wrapper chính thức từ Hyprland 0.53+, có crash
# recovery + safe mode, tự lo phần systemd graphical-session.target) làm
# lệnh Exec trong session — không gọi thẳng "Hyprland" (xem Master Tutorial
# trên wiki.hypr.land: SDDM "works flawlessly" đúng khi dùng start-hyprland).
log "Cài session 'hyprw' cho SDDM..."
sudo install -Dm644 "$SCRIPT_DIR/sddm/hyprw.desktop" /usr/share/wayland-sessions/hyprw.desktop
ok "Đã cài session — chọn 'hyprw' ở màn hình đăng nhập SDDM."

if ! systemctl is-enabled sddm.service >/dev/null 2>&1; then
    log "Bật SDDM khởi động cùng hệ thống..."
    sudo systemctl enable sddm.service
    ok "Đã bật SDDM."
else
    ok "SDDM đã được bật từ trước, bỏ qua."
fi

# Lưu ý: sddm cần bản ≥0.20.0 để tránh bug cũ gây treo máy ~90s lúc tắt
# (SDDM bug 1476) — bản Arch hiện tại đã đủ mới, không cần làm gì thêm.

# ── Xong ─────────────────────────────────────────────────────────────
echo
ok "CÀI XONG."
echo -e "  • Config cũ (nếu có)  : ${C_YELLOW}$BACKUP_DIR${C_RESET}"
echo -e "  • Wallpaper mặc định  : river_to_castle_theme_blue.jpeg (đổi bằng Super+W sau khi vào)"
echo -e "  • Gõ tiếng Việt       : Super+Space để bật/tắt Unikey"
echo -e "  • Shell mặc định      : zsh (có hiệu lực từ lần đăng nhập tiếp theo)"
echo
warn "Driver GPU (đặc biệt NVIDIA) KHÔNG nằm trong script này — nếu chưa cài, làm trước khi reboot."
echo
log "Giờ chạy: ${C_GREEN}reboot${C_RESET} — ở màn hình đăng nhập SDDM, chọn session 'hyprw' trước khi gõ mật khẩu."
