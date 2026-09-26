#!/usr/bin/env python3
"""
quick-settings.py — Bảng Wifi + Bluetooth + Âm lượng + Độ sáng GỘP CHUNG
kiểu Windows Quick Settings. Mở bằng Super+A, hoặc bấm vào BẤT KỲ phần nào
trong cụm hệ thống trên waybar (cpu/memory/pulseaudio/network/bluetooth/
battery — xem on-click trong .config/waybar/config.jsonc); riêng icon
nguồn (custom/power) vẫn mở power-menu.py như cũ, không đổi.

BẢN 2 (bản này) — ĐỔI HẲN CƠ CHẾ MỞ/ĐÓNG so với bản 1:

Bản 1 mở bằng Gtk.Revealer neo góc phải, thả xuống tại chỗ — độc lập,
không liên quan gì tới hình dạng waybar thật. Bản này đổi sang CÙNG CƠ
CHẾ với power-menu.py: viên thuốc hệ thống thật (#group-system-pill) tự
"biến hình", PHÌNH TO ra thành bảng cài đặt, tái định vị về GIỮA MÀN HÌNH
— coi power-menu.py là bản THAM CHIẾU kỹ thuật, copy lại các phần đã kiểm
chứng: hide_waybar()/show_waybar() (SIGUSR1/2, xem man waybar.5), Pill (1
cửa sổ layer-shell union_bbox cố định + Gtk.Fixed, không resize window
thật mỗi khung hình), tween() (Gtk.Widget.add_tick_callback theo frame
clock thật, không dùng GLib.timeout_add — xem lý do trong hàm tween()).

KHÁC 1 CHỖ so với power-menu.py: power-menu có 3 viên (trái/giữa/phải)
cùng tham gia — trái/phải CO VỀ 0 trong lúc giữa PHÌNH TO. Ở đây chỉ có
ĐÚNG 1 viên (viên hệ thống) vừa co vừa mang nội dung — không có "viên
khác" nào cần co/ẩn riêng, vì workspaces/đồng hồ/tray không liên quan gì
tới Wifi/Bluetooth/Âm lượng/Độ sáng nên không cần động tới. waybar vẫn ẩn
CẢ THANH (không có cách ẩn riêng 1 module qua signal — waybar chỉ hỗ trợ
ẩn/hiện toàn bộ cửa sổ, xem on-sigusr1/on-sigusr2 trong config.jsonc) —
workspaces/đồng hồ/tray vì vậy cũng biến mất TẠM THỜI cùng lúc, giống hệt
những gì đã xảy ra (và được chấp nhận) trong lúc power-menu.py mở.

GIỚI HẠN ĐÃ BIẾT (test kỹ trước khi coi là hoàn chỉnh):
- Kích thước/vị trí viên hệ thống lúc NGHỈ (ĐIỂM XUẤT PHÁT animation) là
  ước lượng từ padding/font-size thật trong style.css + config.jsonc,
  giống hệt cách power-menu.py ước lượng workspaces/tray — waybar không
  có IPC trả toạ độ pixel thật. Sai số ở đây ít nghiêm trọng hơn bên
  power-menu vì overlay MỜ DẦN opacity ngay khi xuất hiện (che bớt lệch),
  và waybar thật đã ẩn hẳn trước khi animation hình dạng bắt đầu.
- Ghép Bluetooth mới CHỈ chắc ăn với thiết bị "Just Works" (đa số tai
  nghe/loa hiện đại, không cần nhập mã PIN). Thiết bị cần XÁC NHẬN PIN
  qua lại (vài bàn phím/chuột cũ) sẽ báo lỗi ghép — dùng `bluetoothctl`
  trực tiếp trong terminal cho các trường hợp đó.
- Danh sách wifi lấy từ CACHE của NetworkManager (không ép rescan mỗi lần
  mở, tránh chờ lâu) — bấm nút refresh nếu vừa di chuyển tới nơi mới.
- Không có gạch nối mạng LAN riêng, chỉ wifi.

TOGGLE (không đổi so với bản 1): PID file + SIGUSR1 riêng của chính script
này (khác SIGUSR1 gửi cho waybar ở trên — 2 việc khác nhau), giống hệt cơ
chế trong power-menu.py.
"""
import json
import os
import re
import signal
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GLib, Gtk, GtkLayerShell, Pango

PIDFILE = os.path.join(
    os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "hyprw-quick-settings.pid"
)

# ── Animation (copy quy ước từ power-menu.py — xem giải thích trong hàm
# tween() phía dưới) ───────────────────────────────────────────────────
ANIM_DURATION_MS = 260  # co/phình hình dạng
CONTENT_FADE_DURATION_MS = 180  # fade nội dung sau khi phình xong
SHOW_WAYBAR_AT_RATIO = 0.80
OPEN_HIDE_BUFFER_MS = 120
POST_REVERSE_BUFFER_MS = 120
FINAL_FADE_DURATION_MS = 150

# ── Kích thước bảng khi mở, đặt GIỮA MÀN HÌNH (không neo theo waybar nữa
# vì lúc này waybar thật đã ẩn hẳn) — đủ chỗ cho danh sách wifi + bluetooth
# (đã giới hạn chiều cao list riêng, xem WIFI_LIST_MAX_HEIGHT/
# BT_LIST_MAX_HEIGHT) + 2 thanh trượt mà không bị góc trên/dưới cắt chữ.
PANEL_WIDTH = 380
PANEL_HEIGHT = 680  # ước lượng nội dung thật ~622px + margin 26px = 648px,
# để dư ~32px an toàn — quá thấp thì lúc thêm nội dung GTK sẽ tự ép cửa sổ
# to hơn số này (set_size_request chỉ là mức TỐI THIỂU), gây khựng 1 nhịp
# đúng lúc nội dung xuất hiện.
WIFI_LIST_MAX_HEIGHT = 176
BT_LIST_MAX_HEIGHT = 152

# ── Vị trí/kích thước viên hệ thống lúc NGHỈ — tính từ style.css +
# config.jsonc thật, CÙNG CÔNG THỨC đang dùng trong power-menu.py (xem
# comment ở đó) để 2 script không lệch nhau nếu waybar đổi cấu hình sau
# này. cpu/memory/battery hiện "icon NN%" (có chữ số), pulseaudio/network/
# bluetooth/custom-power chỉ-icon — 2 nhóm khác bề rộng nhau.
BAR_TOP = 6
BAR_HEIGHT = 34
FONT_SIZE = 13
MONO_CHAR_WIDTH = FONT_SIZE * 0.6
EDGE_MARGIN = 3
MODULE_SPACING = 4
SYSTEM_PILL_OUTER_PADDING = 8
SYSTEM_PILL_ICON_ONLY_COUNT = 4  # pulseaudio, network, bluetooth, custom/power
SYSTEM_PILL_ICON_ONLY_WIDTH = 12 + FONT_SIZE
SYSTEM_PILL_PERCENT_COUNT = 3  # cpu, memory, battery
SYSTEM_PILL_PERCENT_WIDTH = 12 + FONT_SIZE + 4 * MONO_CHAR_WIDTH
TRAY_OUTER_PADDING = 16
TRAY_ICON_COUNT = 2
TRAY_ICON_WIDTH = 20

# Y HỆT icon dùng trong .config/waybar/config.jsonc (format-icons của
# module "network") — đồng bộ hình, không tự vẽ icon khác.
WIFI_BAR_ICONS = ["\U000f091f", "\U000f0922", "\U000f0925", "\U000f0928"]
ICON_WIFI_OFF = "\U000f092d"
# Y HỆT icon dùng trong power-menu.py (ACTIONS) — khoá = ổ khoá, refresh
# dùng chung glyph với "Khởi động lại" (cùng ý niệm "circular arrows").
ICON_LOCK = "\uf023"
ICON_REFRESH = "\uf021"
ICON_BLUETOOTH = "\uf293"
ICON_SCAN = "\uf002"
ICON_CLOSE = "\uf00d"
ICON_VOLUME_HIGH = "\uf028"
ICON_VOLUME_LOW = "\uf027"
ICON_VOLUME_MUTE = "\uf026"
ICON_BRIGHTNESS = "\uf185"

_BT_ICON_MAP = {
    "audio-card": "\uf025",
    "audio-headset": "\uf025",
    "audio-headphones": "\uf025",
    "input-keyboard": "\uf11c",
    "input-mouse": "\uf8cc",
    "input-gaming": "\uf11b",
    "phone": "\uf10b",
}
_BT_ICON_DEFAULT = ICON_BLUETOOTH

# CSS nằm trong bytes literal (b\"\"\"...\"\"\") -> CHỈ ĐƯỢC ASCII, kể cả
# trong comment. Đã ăn lỗi này 1 lần khi sửa power-menu.py, ghi lại đây
# để lần sau khỏi lặp: khong dung dau tieng Viet, khong dung em-dash (—).
CSS = b"""
window#qs-pill { background-color: transparent; }
fixed { background-color: transparent; }
box.qs-card {
    background-color: rgba(30, 30, 46, 0.90);
    border: 2px solid rgba(137, 180, 250, 0.35);
    border-radius: 20px;
}
label.qs-header-icon {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 15px;
    color: #cdd6f4;
}
label.qs-header-title {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 13px;
    font-weight: bold;
    color: #cdd6f4;
}
button.qs-icon-btn, button.qs-close {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 4px 8px;
    border-radius: 999px;
    color: #a6adc8;
    font-family: "JetBrainsMono Nerd Font";
}
button.qs-icon-btn:hover, button.qs-close:hover {
    background-color: rgba(255, 255, 255, 0.10);
    color: #cdd6f4;
}
switch {
    background-color: rgba(255, 255, 255, 0.12);
    border: none;
    border-radius: 999px;
    min-width: 40px;
    min-height: 22px;
}
switch:checked {
    background-color: rgba(137, 180, 250, 0.55);
}
switch slider {
    background-color: #cdd6f4;
    border-radius: 999px;
    min-width: 18px;
    min-height: 18px;
}
button.qs-row {
    background: transparent;
    border: none;
    box-shadow: none;
    border-radius: 12px;
    padding: 2px;
}
button.qs-row:hover { background-color: rgba(255, 255, 255, 0.08); }
button.qs-row:disabled { opacity: 0.5; }
label.qs-row-icon {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 14px;
    color: #89b4fa;
}
label.qs-row-title {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 12px;
    color: #cdd6f4;
}
label.qs-row-sub {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 11px;
    color: #a6adc8;
}
label.qs-row-connected {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 10px;
    color: #a6e3a1;
}
label.qs-status, label.qs-empty {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 10px;
    color: #a6adc8;
}
label.qs-error {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 10px;
    color: #f38ba8;
}
entry.qs-password {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(137, 180, 250, 0.35);
    border-radius: 8px;
    color: #cdd6f4;
    font-family: "JetBrainsMono Nerd Font";
    font-size: 12px;
    padding: 4px 8px;
}
button.qs-primary {
    background-color: rgba(137, 180, 250, 0.25);
    border: none;
    border-radius: 999px;
    color: #cdd6f4;
    padding: 5px 14px;
    font-family: "JetBrainsMono Nerd Font";
    font-size: 11px;
}
button.qs-primary:hover { background-color: rgba(137, 180, 250, 0.40); }
scale { min-height: 20px; }
scale trough {
    background-color: rgba(255, 255, 255, 0.10);
    border-radius: 999px;
    min-height: 6px;
}
scale highlight {
    background-color: rgba(137, 180, 250, 0.55);
    border-radius: 999px;
    min-height: 6px;
}
scale slider {
    background-color: #cdd6f4;
    border-radius: 999px;
    min-width: 14px;
    min-height: 14px;
    margin: -4px 0;
}
scale slider:hover { background-color: #ffffff; }
"""


# ─────────────────────────── tiện ích chung ────────────────────────────
def already_running():
    """Trả về PID nếu panel đang mở (dùng để TOGGLE — mở lần nữa = đóng),
    None nếu chưa chạy hoặc PID trong file đã chết (xem power-menu.py,
    cùng 1 cơ chế PID file để 2 script nhất quán)."""
    try:
        with open(PIDFILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return pid
    except Exception:
        return None


def cleanup_pidfile():
    try:
        os.remove(PIDFILE)
    except Exception:
        pass


def get_focused_monitor():
    """Y hệt power-menu.py — đọc hyprctl monitors -j, chọn ĐÚNG monitor
    đang focus (không mặc định monitor đầu/toạ độ (0,0))."""
    try:
        out = subprocess.run(
            ["hyprctl", "monitors", "-j"], capture_output=True, text=True, timeout=2
        ).stdout
        monitors = json.loads(out)
        for m in monitors:
            if m.get("focused"):
                return m["width"], m["height"], m["x"], m["y"]
        if monitors:
            m = monitors[0]
            return m["width"], m["height"], m["x"], m["y"]
    except Exception:
        pass
    return 1920, 1080, 0, 0


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def union_bbox(a, b):
    """Y hệt power-menu.py — hợp bao 2 hình chữ nhật {x,y,w,h}, dùng làm
    kích thước CỬA SỔ THẬT cố định (tạo 1 lần, không resize lại)."""
    x0, y0 = min(a["x"], b["x"]), min(a["y"], b["y"])
    x1 = max(a["x"] + a["w"], b["x"] + b["w"])
    y1 = max(a["y"] + a["h"], b["y"] + b["h"])
    return dict(x=x0, y=y0, w=x1 - x0, h=y1 - y0)


def hide_waybar():
    """SIGUSR1 -> "hide" (xem on-sigusr1 trong config.jsonc) — ẨN THẬT cả
    thanh waybar, không có cách ẩn riêng 1 module qua signal (xem docstring
    đầu file)."""
    subprocess.run(["killall", "-SIGUSR1", "waybar"], stderr=subprocess.DEVNULL)


def show_waybar():
    subprocess.run(["killall", "-SIGUSR2", "waybar"], stderr=subprocess.DEVNULL)


class Pill:
    """Y hệt class Pill trong power-menu.py — 1 cửa sổ layer-shell tạo 1
    LẦN duy nhất ở kích thước union_bbox, không resize lại. Chứa 1
    Gtk.Fixed + 1 widget con (self.child) được di chuyển/đổi kích thước
    nội bộ (không đàm phán Wayland) qua move_child()."""

    def __init__(self, name, monitor_x, window_bbox):
        self.bbox = window_bbox

        self.win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.win.set_name(name)
        self.win.set_decorated(False)

        GtkLayerShell.init_for_window(self.win)
        GtkLayerShell.set_layer(self.win, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_namespace(self.win, "hyprw-quick-settings")
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_keyboard_mode(self.win, GtkLayerShell.KeyboardMode.ON_DEMAND)

        left_margin = window_bbox["x"] - monitor_x
        GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.LEFT, int(left_margin))
        GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.TOP, int(window_bbox["y"]))
        self.win.set_size_request(int(window_bbox["w"]), int(window_bbox["h"]))

        self.fixed = Gtk.Fixed()
        self.win.add(self.fixed)

        self.child = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.child.get_style_context().add_class("qs-card")
        self.fixed.put(self.child, 0, 0)

    def move_child(self, x, y, w, h):
        rel_x = x - self.bbox["x"]
        rel_y = y - self.bbox["y"]
        self.fixed.move(self.child, int(rel_x), int(rel_y))
        self.child.set_size_request(max(1, int(w)), max(1, int(h)))


def tween(widget, get_frames, duration_ms, on_done=None, on_ratio=None):
    """Y hệt power-menu.py — animate qua Gtk.Widget.add_tick_callback,
    đồng bộ frame clock thật của compositor thay vì GLib.timeout_add (xem
    docstring gốc trong power-menu.py để biết lý do đầy đủ)."""
    state = {"start_us": None, "ratio_fired": False}

    def tick(_widget, frame_clock):
        now_us = frame_clock.get_frame_time()
        if state["start_us"] is None:
            state["start_us"] = now_us
        t = min(1.0, (now_us - state["start_us"]) / 1000 / duration_ms)
        get_frames(ease_out_cubic(t))
        if on_ratio and not state["ratio_fired"] and t >= SHOW_WAYBAR_AT_RATIO:
            state["ratio_fired"] = True
            on_ratio()
        if t >= 1.0:
            if on_done:
                on_done()
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    widget.add_tick_callback(tick)


def animate_window_opacity(win, target, duration_ms, on_done=None):
    """Fade CẢ CỬA SỔ (không phải nội dung) — dùng add_tick_callback riêng
    (không qua tween() ở trên vì tween() dành cho get_frames(t) đổi HÌNH
    DẠNG, còn cái này chỉ đổi 1 con số opacity, tách riêng cho gọn)."""
    start = win.get_opacity()
    state = {"start_us": None}

    def tick(_widget, frame_clock):
        now_us = frame_clock.get_frame_time()
        if state["start_us"] is None:
            state["start_us"] = now_us
        t = min(1.0, (now_us - state["start_us"]) / 1000 / duration_ms)
        win.set_opacity(start + (target - start) * t)
        if t >= 1.0:
            if on_done:
                on_done()
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    win.add_tick_callback(tick)


def run_async(work_fn, done_cb):
    """subprocess nmcli/bluetoothctl có thể mất vài giây (scan) -> KHÔNG
    được gọi trực tiếp trên main thread GTK (đứng hình cả UI, cả bàn
    phím/chuột vì đây là layer-shell surface). Chạy work_fn() ở thread
    nền, đẩy done_cb(result) lại main thread qua GLib.idle_add — GTK
    không thread-safe, mọi thao tác lên widget PHẢI ở main thread."""

    def worker():
        try:
            result = work_fn()
        except Exception as e:
            result = e
        GLib.idle_add(done_cb, result)

    threading.Thread(target=worker, daemon=True).start()


def _parse_terse(line):
    """Tách 1 dòng terse của nmcli (-t) theo dấu ':', bỏ qua dấu ':' đã bị
    nmcli tự escape thành '\\:' bên trong 1 field (vd SSID chứa dấu hai
    chấm) — xem `man nmcli` mục TERSE OUTPUT FORMAT."""
    fields, cur, i = [], [], 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line):
            cur.append(line[i + 1])
            i += 2
            continue
        if c == ":":
            fields.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    fields.append("".join(cur))
    return fields


# ─────────────────────────── backend: nmcli ────────────────────────────
def wifi_radio_enabled():
    try:
        out = subprocess.run(
            ["nmcli", "radio", "wifi"], capture_output=True, text=True, timeout=3
        ).stdout.strip()
        return out == "enabled"
    except Exception:
        return True  # nmcli lỗi tạm thời -> đừng tự ý khoá UI lại


def set_wifi_radio(enabled):
    try:
        subprocess.run(
            ["nmcli", "radio", "wifi", "on" if enabled else "off"],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass


def rescan_wifi():
    try:
        subprocess.run(["nmcli", "dev", "wifi", "rescan"], capture_output=True, timeout=10)
    except Exception:
        pass


def list_wifi_networks():
    """[{ssid, signal:int, secured:bool, in_use:bool}, ...] — gộp trùng
    SSID (1 mạng có thể có nhiều AP/BSSID cùng tên), ưu tiên giữ bản đang
    IN-USE, rồi tới bản tín hiệu mạnh nhất. Sắp mạng đang dùng lên đầu."""
    try:
        out = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,IN-USE", "dev", "wifi", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout
    except Exception:
        return []

    best = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = _parse_terse(line)
        if len(parts) < 4:
            continue
        ssid, signal, security, in_use = parts[0], parts[1], parts[2], parts[3]
        if not ssid:
            continue  # mạng ẩn tên -> bỏ qua, ngoài phạm vi bảng này
        try:
            signal_i = int(signal)
        except ValueError:
            signal_i = 0
        cand = dict(
            ssid=ssid,
            signal=signal_i,
            secured=security not in ("", "--"),
            in_use="*" in in_use,
        )
        existing = best.get(ssid)
        if existing is None:
            best[ssid] = cand
        elif cand["in_use"] and not existing["in_use"]:
            best[ssid] = cand
        elif cand["in_use"] == existing["in_use"] and cand["signal"] > existing["signal"]:
            best[ssid] = cand

    nets = list(best.values())
    nets.sort(key=lambda n: (not n["in_use"], -n["signal"]))
    return nets


def connect_wifi(ssid, password=None):
    """Không truyền password trước: nếu SSID đã có profile lưu sẵn hoặc
    là mạng mở, lệnh này tự nối được luôn. Chỉ khi thất bại VÀ mạng có
    khoá mới cần hỏi mật khẩu (xem Panel._on_wifi_row_clicked)."""
    cmd = ["nmcli", "dev", "wifi", "connect", ssid]
    if password:
        cmd += ["password", password]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    except subprocess.TimeoutExpired:
        return False, "Quá thời gian chờ kết nối"
    except Exception as e:
        return False, str(e)
    if proc.returncode == 0:
        return True, ""
    lines = (proc.stderr or proc.stdout or "Lỗi không rõ").strip().splitlines()
    return False, (lines[-1] if lines else "Lỗi không rõ")


def disconnect_wifi():
    try:
        out = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "dev"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout
        for line in out.splitlines():
            parts = _parse_terse(line)
            if len(parts) >= 3 and parts[1] == "wifi" and parts[2] == "connected":
                subprocess.run(
                    ["nmcli", "dev", "disconnect", parts[0]], capture_output=True, timeout=5
                )
                return True
    except Exception:
        pass
    return False


# ────────────────────────── backend: bluetoothctl ───────────────────────
def bt_powered():
    try:
        out = subprocess.run(
            ["bluetoothctl", "show"], capture_output=True, text=True, timeout=3
        ).stdout
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Powered:"):
                return line.split(":", 1)[1].strip() == "yes"
    except Exception:
        pass
    return False


def set_bt_power(enabled):
    try:
        subprocess.run(
            ["bluetoothctl", "power", "on" if enabled else "off"],
            capture_output=True,
            timeout=8,
        )
    except Exception:
        pass


def _bt_info(mac):
    """1 lần gọi `bluetoothctl info` lấy CẢ Connected lẫn Icon — đỡ phải
    gọi 2 lần riêng cho mỗi thiết bị (list_paired_bt_devices cần cả 2)."""
    try:
        out = subprocess.run(
            ["bluetoothctl", "info", mac], capture_output=True, text=True, timeout=5
        ).stdout
    except Exception:
        return dict(connected=False, icon=_BT_ICON_DEFAULT)
    connected, icon_name = False, None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Connected:"):
            connected = line.split(":", 1)[1].strip() == "yes"
        elif line.startswith("Icon:"):
            icon_name = line.split(":", 1)[1].strip()
    return dict(connected=connected, icon=_BT_ICON_MAP.get(icon_name, _BT_ICON_DEFAULT))


def list_paired_bt_devices():
    try:
        out = subprocess.run(
            ["bluetoothctl", "devices", "Paired"], capture_output=True, text=True, timeout=5
        ).stdout
    except Exception:
        return []
    devices = []
    for line in out.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 3 or parts[0] != "Device":
            continue
        mac, name = parts[1], parts[2]
        info = _bt_info(mac)
        devices.append(dict(mac=mac, name=name, connected=info["connected"], icon=info["icon"]))
    devices.sort(key=lambda d: (not d["connected"], d["name"].lower()))
    return devices


def connect_bt(mac):
    try:
        proc = subprocess.run(
            ["bluetoothctl", "connect", mac], capture_output=True, text=True, timeout=15
        )
    except Exception as e:
        return False, str(e)
    ok = proc.returncode == 0 and "Failed" not in proc.stdout
    lines = (proc.stdout or "").strip().splitlines()
    return ok, ("" if ok else (lines[-1] if lines else "Không kết nối được"))


def disconnect_bt(mac):
    try:
        subprocess.run(["bluetoothctl", "disconnect", mac], capture_output=True, timeout=8)
        return True
    except Exception:
        return False


def scan_new_bt_devices(timeout=8):
    """Quét thiết bị CHƯA ghép — lọc bỏ máy đã có trong danh sách Paired.
    `--timeout` là cờ CHUNG của bluetoothctl (đứng trước lệnh con), tự
    thoát sau N giây thay vì treo REPL chờ nhập tay — xem `man
    bluetoothctl` mục OPTIONS, ví dụ chính thức: `bluetoothctl --timeout
    10 scan on`."""
    try:
        paired_macs = {d["mac"] for d in list_paired_bt_devices()}
    except Exception:
        paired_macs = set()
    try:
        out = subprocess.run(
            ["bluetoothctl", "--timeout", str(timeout), "scan", "on"],
            capture_output=True,
            text=True,
            timeout=timeout + 6,
        ).stdout
    except Exception:
        return []
    found = {}
    for line in out.splitlines():
        m = re.match(r"\[NEW\] Device ([0-9A-Fa-f:]{17}) (.+)", line.strip())
        if m and m.group(1) not in paired_macs:
            found[m.group(1)] = m.group(2).strip()
    return [dict(mac=mac, name=name) for mac, name in found.items()]


def pair_bt(mac):
    """`--agent NoInputNoOutput`: ưu tiên kiểu ghép "Just Works" (đa số
    tai nghe/loa hiện đại) — KHÔNG xử lý được thiết bị cần xác nhận mã
    PIN qua lại (xem giới hạn đã biết ở đầu file)."""
    try:
        proc = subprocess.run(
            ["bluetoothctl", "--agent", "NoInputNoOutput", "--timeout", "15", "pair", mac],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as e:
        return False, str(e)
    ok = proc.returncode == 0 or "Pairing successful" in proc.stdout
    if ok:
        subprocess.run(["bluetoothctl", "trust", mac], capture_output=True, timeout=5)
        connect_bt(mac)
        return True, ""
    return False, "Không ghép được — có thể cần xác nhận mã PIN, thử bluetoothctl trong terminal"


# ───────────────────────── backend: wpctl (volume) ──────────────────────
# Y HỆT lệnh dùng trong .config/hypr/scripts/osd-volume.sh — cùng 1 sink
# mặc định, cùng cách đọc %, để volume trong panel và OSD phím tắt khớp
# nhau tuyệt đối (không phải 2 nguồn số khác nhau).
def get_volume():
    """(percent:int, muted:bool)."""
    try:
        out = subprocess.run(
            ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout
        m = re.search(r"[0-9]+\.[0-9]+", out)
        percent = round(float(m.group(0)) * 100) if m else 0
        return percent, "MUTED" in out
    except Exception:
        return 0, False


def set_volume(percent):
    """`-l 1`: không cho vượt 100% (giống osd-volume.sh) — set-volume nhận
    thẳng số phần trăm TUYỆT ĐỐI, không phải +/- tương đối, xem `man
    wpctl` mục set-volume, ví dụ chính thức: `wpctl set-volume ID 75%`."""
    try:
        subprocess.run(
            ["wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SINK@", "%d%%" % percent],
            capture_output=True,
            timeout=3,
        )
    except Exception:
        pass


def set_volume_muted(muted):
    try:
        subprocess.run(
            ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1" if muted else "0"],
            capture_output=True,
            timeout=3,
        )
    except Exception:
        pass


# ──────────────────────── backend: brightnessctl ────────────────────────
# Y HỆT lệnh dùng trong .config/hypr/scripts/osd-brightness.sh.
def get_brightness():
    try:
        out = subprocess.run(
            ["brightnessctl", "-m"], capture_output=True, text=True, timeout=3
        ).stdout
        return int(out.strip().split(",")[3].rstrip("%"))
    except Exception:
        return 100


def set_brightness(percent):
    try:
        subprocess.run(["brightnessctl", "set", "%d%%" % percent], capture_output=True, timeout=3)
    except Exception:
        pass


# ────────────────────────────────  UI  ──────────────────────────────────
class Panel:
    def __init__(self):
        self.dismissed = False
        self.fully_open = False
        self.content_box = None

        mon_w, mon_h, mon_x, mon_y = get_focused_monitor()

        tray_width = TRAY_OUTER_PADDING + TRAY_ICON_COUNT * TRAY_ICON_WIDTH
        system_pill_width = (
            SYSTEM_PILL_OUTER_PADDING
            + SYSTEM_PILL_ICON_ONLY_COUNT * SYSTEM_PILL_ICON_ONLY_WIDTH
            + SYSTEM_PILL_PERCENT_COUNT * SYSTEM_PILL_PERCENT_WIDTH
        )
        pill_right = mon_x + mon_w - EDGE_MARGIN - tray_width - MODULE_SPACING
        # ĐIỂM XUẤT PHÁT: đúng vị trí/kích thước viên hệ thống thật lúc nghỉ.
        self.orig = dict(
            x=pill_right - system_pill_width, y=mon_y + BAR_TOP, w=system_pill_width, h=BAR_HEIGHT
        )
        # ĐIỂM ĐẾN: bảng cài đặt, giữa màn hình (cả x lẫn y).
        self.merged = dict(
            x=mon_x + mon_w / 2 - PANEL_WIDTH / 2,
            y=mon_y + mon_h / 2 - PANEL_HEIGHT / 2,
            w=PANEL_WIDTH,
            h=PANEL_HEIGHT,
        )

        self.pill = Pill("qs-pill", mon_x, union_bbox(self.orig, self.merged))
        self.pill.move_child(self.orig["x"], self.orig["y"], self.orig["w"], self.orig["h"])
        self.pill.win.connect("key-press-event", self._on_key)
        self.pill.win.show_all()

        GLib.timeout_add(20, lambda: (self._animate_open(), False)[1])

    def _animate_open(self):
        hide_waybar()
        # Đợi buffer TRƯỚC khi phình — lúc này viên overlay vẫn đứng yên
        # đúng khớp vị trí/kích thước viên hệ thống thật nên dù waybar thật
        # ẩn chưa kịp xong cũng không lộ khác biệt (y hệt lý do trong
        # power-menu.py, xem OPEN_HIDE_BUFFER_MS).
        GLib.timeout_add(OPEN_HIDE_BUFFER_MS, lambda: (self._grow(), False)[1])

    def _grow(self):
        def frame(t):
            cur = dict(
                x=lerp(self.orig["x"], self.merged["x"], t),
                y=lerp(self.orig["y"], self.merged["y"], t),
                w=lerp(self.orig["w"], self.merged["w"], t),
                h=lerp(self.orig["h"], self.merged["h"], t),
            )
            self.pill.move_child(cur["x"], cur["y"], cur["w"], cur["h"])

        tween(self.pill.win, frame, ANIM_DURATION_MS, on_done=self._after_grow)

    def _after_grow(self):
        self._build_content()

        def fade_in(t):
            self.content_box.set_opacity(t)

        def done():
            self.fully_open = True
            GLib.idle_add(self._initial_load)

        tween(self.pill.win, fade_in, CONTENT_FADE_DURATION_MS, on_done=done)

    def _build_content(self):
        """Chỉ gọi 1 LẦN, SAU KHI đã phình xong kích thước đầy đủ — nếu
        nhồi hết nội dung (list wifi/bt + 2 thanh trượt) vào self.pill.child
        NGAY TỪ ĐẦU lúc còn nhỏ bằng viên hệ thống, "size request" chỉ là
        mức TỐI THIỂU (không phải mức TRẦN) nên GTK sẽ tự phình cửa sổ to
        hơn kích thước ta đang cố ép trong lúc animation co — y hệt lỗi
        từng gặp và tránh trong power-menu.py."""
        self.pill.child.set_margin_top(12)
        self.pill.child.set_margin_bottom(14)
        self.pill.child.set_margin_start(14)
        self.pill.child.set_margin_end(14)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_opacity(0)

        close_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        close_btn = Gtk.Button(label=ICON_CLOSE)
        close_btn.get_style_context().add_class("qs-close")
        close_btn.connect("clicked", lambda _b: self.dismiss())
        close_row.pack_end(close_btn, False, False, 0)

        self.content_box.pack_start(close_row, False, False, 0)
        self.content_box.pack_start(self._build_wifi_section(), False, False, 0)
        self.content_box.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0
        )
        self.content_box.pack_start(self._build_bt_section(), False, False, 0)
        self.content_box.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0
        )
        self.content_box.pack_start(self._build_volume_section(), False, False, 0)
        self.content_box.pack_start(self._build_brightness_section(), False, False, 0)

        self.pill.child.pack_start(self.content_box, True, True, 0)
        self.pill.child.show_all()
        self.wifi_password_box.hide()

    def _initial_load(self):
        self.refresh_wifi()
        self.refresh_bt()
        self.refresh_volume()
        self.refresh_brightness()
        return GLib.SOURCE_REMOVE

    # ---- Wifi ----
    def _build_wifi_section(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon = Gtk.Label(label=WIFI_BAR_ICONS[-1])
        self.wifi_header_icon = icon
        icon.get_style_context().add_class("qs-header-icon")
        title = Gtk.Label(label="Wi-Fi")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("qs-header-title")
        refresh_btn = Gtk.Button(label=ICON_REFRESH)
        refresh_btn.get_style_context().add_class("qs-icon-btn")
        refresh_btn.connect("clicked", lambda _b: self._on_wifi_refresh_clicked())
        self.wifi_switch = Gtk.Switch()
        self.wifi_switch.set_valign(Gtk.Align.CENTER)
        self._wifi_switch_handler = self.wifi_switch.connect(
            "notify::active", self._on_wifi_switch
        )
        header.pack_start(icon, False, False, 0)
        header.pack_start(title, True, True, 0)
        header.pack_start(refresh_btn, False, False, 0)
        header.pack_start(self.wifi_switch, False, False, 0)
        box.pack_start(header, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_max_content_height(WIFI_LIST_MAX_HEIGHT)
        scroller.set_propagate_natural_height(True)
        self.wifi_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        scroller.add(self.wifi_list_box)
        box.pack_start(scroller, False, False, 0)

        # Ô nhập mật khẩu dùng CHUNG cho cả danh sách (hiện ra khi 1 mạng
        # có khoá cần mật khẩu) thay vì "biến hình" từng dòng — đơn giản
        # và chắc ăn hơn (xem lý do trong docstring đầu file).
        self.wifi_password_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.wifi_password_label = Gtk.Label(label="")
        self.wifi_password_label.set_halign(Gtk.Align.START)
        self.wifi_password_label.get_style_context().add_class("qs-status")
        pw_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.wifi_password_entry = Gtk.Entry()
        self.wifi_password_entry.set_visibility(False)
        self.wifi_password_entry.get_style_context().add_class("qs-password")
        self.wifi_password_entry.set_hexpand(True)
        self.wifi_password_entry.connect("activate", lambda _e: self._on_wifi_password_confirm())
        connect_btn = Gtk.Button(label="Kết nối")
        connect_btn.get_style_context().add_class("qs-primary")
        connect_btn.connect("clicked", lambda _b: self._on_wifi_password_confirm())
        pw_row.pack_start(self.wifi_password_entry, True, True, 0)
        pw_row.pack_start(connect_btn, False, False, 0)
        self.wifi_password_error = Gtk.Label(label="")
        self.wifi_password_error.set_halign(Gtk.Align.START)
        self.wifi_password_error.get_style_context().add_class("qs-error")
        self.wifi_password_box.pack_start(self.wifi_password_label, False, False, 0)
        self.wifi_password_box.pack_start(pw_row, False, False, 0)
        self.wifi_password_box.pack_start(self.wifi_password_error, False, False, 0)
        box.pack_start(self.wifi_password_box, False, False, 0)

        self.wifi_status_label = Gtk.Label(label="")
        self.wifi_status_label.set_halign(Gtk.Align.START)
        self.wifi_status_label.get_style_context().add_class("qs-status")
        box.pack_start(self.wifi_status_label, False, False, 0)

        self._wifi_pending_ssid = None
        return box

    def _set_wifi_switch_silently(self, active):
        self.wifi_switch.handler_block(self._wifi_switch_handler)
        self.wifi_switch.set_active(active)
        self.wifi_switch.handler_unblock(self._wifi_switch_handler)

    def refresh_wifi(self):
        self.wifi_status_label.set_label("Đang tải...")
        run_async(wifi_radio_enabled, self._on_wifi_radio_status)

    def _on_wifi_radio_status(self, enabled):
        if isinstance(enabled, Exception):
            enabled = True
        self._set_wifi_switch_silently(enabled)
        self.wifi_header_icon.set_label(WIFI_BAR_ICONS[-1] if enabled else ICON_WIFI_OFF)
        for child in list(self.wifi_list_box.get_children()):
            self.wifi_list_box.remove(child)
        if not enabled:
            self.wifi_status_label.set_label("Wi-Fi đang tắt")
            return GLib.SOURCE_REMOVE
        self.wifi_status_label.set_label("Đang tải danh sách...")
        run_async(list_wifi_networks, self._on_wifi_list_loaded)
        return GLib.SOURCE_REMOVE

    def _on_wifi_list_loaded(self, networks):
        if isinstance(networks, Exception) or not networks:
            self.wifi_status_label.set_label(
                "Không tìm thấy mạng nào" if not isinstance(networks, Exception) else "Lỗi đọc danh sách wifi"
            )
            return GLib.SOURCE_REMOVE
        self.wifi_status_label.set_label("")
        for net in networks:
            self.wifi_list_box.pack_start(self._make_wifi_row(net), False, False, 0)
        self.wifi_list_box.show_all()
        return GLib.SOURCE_REMOVE

    def _make_wifi_row(self, net):
        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.get_style_context().add_class("qs-row")

        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content.set_margin_top(4)
        content.set_margin_bottom(4)
        content.set_margin_start(8)
        content.set_margin_end(8)

        bar_icon = WIFI_BAR_ICONS[min(3, net["signal"] // 25)]
        icon_lbl = Gtk.Label(label=bar_icon)
        icon_lbl.get_style_context().add_class("qs-row-icon")
        name_lbl = Gtk.Label(label=net["ssid"])
        name_lbl.set_halign(Gtk.Align.START)
        name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        name_lbl.get_style_context().add_class("qs-row-title")

        content.pack_start(icon_lbl, False, False, 0)
        content.pack_start(name_lbl, True, True, 0)
        if net["in_use"]:
            tag = Gtk.Label(label="Đã kết nối")
            tag.get_style_context().add_class("qs-row-connected")
            content.pack_start(tag, False, False, 0)
        elif net["secured"]:
            lock = Gtk.Label(label=ICON_LOCK)
            lock.get_style_context().add_class("qs-row-sub")
            content.pack_start(lock, False, False, 0)
        spinner = Gtk.Spinner()
        content.pack_start(spinner, False, False, 0)
        btn.add(content)

        if net["in_use"]:
            btn.connect("clicked", lambda _b, s=spinner, b=btn: self._on_wifi_disconnect_clicked(s, b))
        else:
            btn.connect(
                "clicked", lambda _b, n=net, s=spinner, b=btn: self._on_wifi_row_clicked(n, s, b)
            )
        return btn

    def _on_wifi_refresh_clicked(self):
        self.wifi_status_label.set_label("Đang quét...")
        run_async(lambda: (rescan_wifi(), list_wifi_networks())[1], self._on_wifi_list_loaded)

    def _on_wifi_switch(self, switch, _pspec):
        enabled = switch.get_active()
        self.wifi_status_label.set_label("Đang bật..." if enabled else "Đang tắt...")
        run_async(lambda: set_wifi_radio(enabled), lambda _r: self.refresh_wifi())

    def _on_wifi_row_clicked(self, net, spinner, btn):
        btn.set_sensitive(False)
        spinner.start()
        run_async(
            lambda: connect_wifi(net["ssid"]),
            lambda result: self._on_wifi_connect_result(net, spinner, btn, result),
        )

    def _on_wifi_connect_result(self, net, spinner, btn, result):
        spinner.stop()
        btn.set_sensitive(True)
        ok, msg = (False, str(result)) if isinstance(result, Exception) else result
        if ok:
            self.refresh_wifi()
            return GLib.SOURCE_REMOVE
        if net["secured"]:
            self._wifi_pending_ssid = net["ssid"]
            self.wifi_password_label.set_label('Nhập mật khẩu cho "%s"' % net["ssid"])
            self.wifi_password_error.set_label("")
            self.wifi_password_entry.set_text("")
            self.wifi_password_box.show_all()
            self.wifi_password_entry.grab_focus()
        else:
            self.wifi_status_label.set_label("Không kết nối được: %s" % msg)
        return GLib.SOURCE_REMOVE

    def _on_wifi_password_confirm(self):
        ssid = self._wifi_pending_ssid
        pw = self.wifi_password_entry.get_text()
        if not ssid or not pw:
            return
        self.wifi_password_entry.set_sensitive(False)
        run_async(
            lambda: connect_wifi(ssid, pw), lambda result: self._on_wifi_password_result(result)
        )

    def _on_wifi_password_result(self, result):
        self.wifi_password_entry.set_sensitive(True)
        ok, msg = (False, str(result)) if isinstance(result, Exception) else result
        if ok:
            self.wifi_password_box.hide()
            self._wifi_pending_ssid = None
            self.refresh_wifi()
        else:
            self.wifi_password_error.set_label("Sai mật khẩu hoặc lỗi kết nối: %s" % msg)
        return GLib.SOURCE_REMOVE

    def _on_wifi_disconnect_clicked(self, spinner, btn):
        btn.set_sensitive(False)
        spinner.start()
        run_async(disconnect_wifi, lambda _r: self.refresh_wifi())

    # ---- Bluetooth ----
    def _build_bt_section(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon = Gtk.Label(label=ICON_BLUETOOTH)
        icon.get_style_context().add_class("qs-header-icon")
        title = Gtk.Label(label="Bluetooth")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("qs-header-title")
        self.bt_scan_btn = Gtk.Button(label=ICON_SCAN)
        self.bt_scan_btn.get_style_context().add_class("qs-icon-btn")
        self.bt_scan_btn.connect("clicked", lambda _b: self._on_bt_scan_clicked())
        self.bt_switch = Gtk.Switch()
        self.bt_switch.set_valign(Gtk.Align.CENTER)
        self._bt_switch_handler = self.bt_switch.connect("notify::active", self._on_bt_switch)
        header.pack_start(icon, False, False, 0)
        header.pack_start(title, True, True, 0)
        header.pack_start(self.bt_scan_btn, False, False, 0)
        header.pack_start(self.bt_switch, False, False, 0)
        box.pack_start(header, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_max_content_height(BT_LIST_MAX_HEIGHT)
        scroller.set_propagate_natural_height(True)
        self.bt_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        scroller.add(self.bt_list_box)
        box.pack_start(scroller, False, False, 0)

        self.bt_status_label = Gtk.Label(label="")
        self.bt_status_label.set_halign(Gtk.Align.START)
        self.bt_status_label.get_style_context().add_class("qs-status")
        box.pack_start(self.bt_status_label, False, False, 0)
        return box

    def _set_bt_switch_silently(self, active):
        self.bt_switch.handler_block(self._bt_switch_handler)
        self.bt_switch.set_active(active)
        self.bt_switch.handler_unblock(self._bt_switch_handler)

    def refresh_bt(self):
        self.bt_status_label.set_label("Đang tải...")
        run_async(bt_powered, self._on_bt_power_status)

    def _on_bt_power_status(self, enabled):
        if isinstance(enabled, Exception):
            enabled = False
        self._set_bt_switch_silently(enabled)
        for child in list(self.bt_list_box.get_children()):
            self.bt_list_box.remove(child)
        if not enabled:
            self.bt_status_label.set_label("Bluetooth đang tắt")
            return GLib.SOURCE_REMOVE
        self.bt_status_label.set_label("Đang tải thiết bị...")
        run_async(list_paired_bt_devices, self._on_bt_list_loaded)
        return GLib.SOURCE_REMOVE

    def _on_bt_list_loaded(self, devices):
        if isinstance(devices, Exception):
            self.bt_status_label.set_label("Lỗi đọc danh sách bluetooth")
            return GLib.SOURCE_REMOVE
        if not devices:
            self.bt_status_label.set_label("Chưa ghép thiết bị nào — bấm biểu tượng quét")
            return GLib.SOURCE_REMOVE
        self.bt_status_label.set_label("")
        for dev in devices:
            self.bt_list_box.pack_start(self._make_bt_row(dev, paired=True), False, False, 0)
        self.bt_list_box.show_all()
        return GLib.SOURCE_REMOVE

    def _make_bt_row(self, dev, paired):
        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.get_style_context().add_class("qs-row")

        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content.set_margin_top(4)
        content.set_margin_bottom(4)
        content.set_margin_start(8)
        content.set_margin_end(8)

        icon_lbl = Gtk.Label(label=dev.get("icon", _BT_ICON_DEFAULT))
        icon_lbl.get_style_context().add_class("qs-row-icon")
        name_lbl = Gtk.Label(label=dev["name"])
        name_lbl.set_halign(Gtk.Align.START)
        name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        name_lbl.get_style_context().add_class("qs-row-title")
        content.pack_start(icon_lbl, False, False, 0)
        content.pack_start(name_lbl, True, True, 0)

        if paired and dev.get("connected"):
            tag = Gtk.Label(label="Đã kết nối")
            tag.get_style_context().add_class("qs-row-connected")
            content.pack_start(tag, False, False, 0)
        elif not paired:
            tag = Gtk.Label(label="Ghép mới")
            tag.get_style_context().add_class("qs-row-sub")
            content.pack_start(tag, False, False, 0)
        spinner = Gtk.Spinner()
        content.pack_start(spinner, False, False, 0)
        btn.add(content)

        if not paired:
            btn.connect(
                "clicked", lambda _b, d=dev, s=spinner, b=btn: self._on_bt_pair_clicked(d, s, b)
            )
        elif dev.get("connected"):
            btn.connect(
                "clicked", lambda _b, d=dev, s=spinner, b=btn: self._on_bt_disconnect_clicked(d, s, b)
            )
        else:
            btn.connect(
                "clicked", lambda _b, d=dev, s=spinner, b=btn: self._on_bt_connect_clicked(d, s, b)
            )
        return btn

    def _on_bt_switch(self, switch, _pspec):
        enabled = switch.get_active()
        self.bt_status_label.set_label("Đang bật..." if enabled else "Đang tắt...")
        run_async(lambda: set_bt_power(enabled), lambda _r: self.refresh_bt())

    def _on_bt_connect_clicked(self, dev, spinner, btn):
        btn.set_sensitive(False)
        spinner.start()
        run_async(
            lambda: connect_bt(dev["mac"]),
            lambda result: self._on_bt_action_result(spinner, btn, result),
        )

    def _on_bt_disconnect_clicked(self, dev, spinner, btn):
        btn.set_sensitive(False)
        spinner.start()
        run_async(lambda: disconnect_bt(dev["mac"]), lambda _r: self.refresh_bt())

    def _on_bt_pair_clicked(self, dev, spinner, btn):
        btn.set_sensitive(False)
        spinner.start()
        run_async(
            lambda: pair_bt(dev["mac"]),
            lambda result: self._on_bt_action_result(spinner, btn, result),
        )

    def _on_bt_action_result(self, spinner, btn, result):
        spinner.stop()
        btn.set_sensitive(True)
        ok, msg = (False, str(result)) if isinstance(result, Exception) else result
        if ok:
            self.refresh_bt()
        else:
            self.bt_status_label.set_label(msg)
        return GLib.SOURCE_REMOVE

    def _on_bt_scan_clicked(self):
        self.bt_scan_btn.set_sensitive(False)
        self.bt_status_label.set_label("Đang quét thiết bị mới (8s)...")
        run_async(scan_new_bt_devices, self._on_bt_scan_result)

    def _on_bt_scan_result(self, found):
        self.bt_scan_btn.set_sensitive(True)
        if isinstance(found, Exception):
            self.bt_status_label.set_label("Lỗi khi quét bluetooth")
            return GLib.SOURCE_REMOVE
        if not found:
            self.bt_status_label.set_label("Không thấy thiết bị mới nào")
            return GLib.SOURCE_REMOVE
        self.bt_status_label.set_label("Tìm thấy %d thiết bị mới" % len(found))
        for dev in found:
            self.bt_list_box.pack_start(self._make_bt_row(dev, paired=False), False, False, 0)
        self.bt_list_box.show_all()
        return GLib.SOURCE_REMOVE

    # ---- Volume + Brightness ----
    def _make_debounced(self, apply_fn, delay_ms=80):
        """Trả về callback(value) gắn vào Gtk.Scale 'value-changed' — kéo
        thanh trượt bắn signal hàng chục lần/giây, gọi subprocess mỗi lần
        như vậy dồn cục và TRỄ THEO SAU vị trí thanh trượt thật (đúng kiểu
        khựng mà power-menu.py từng gặp). Debounce lại: chỉ thực sự chạy
        lệnh sau khi ngưng kéo được `delay_ms` — vẫn thấy số cập nhật tức
        thời (label riêng, không qua debounce), chỉ lệnh hệ thống là hoãn."""
        state = {"timeout_id": None}

        def debounced(value):
            if state["timeout_id"] is not None:
                GLib.source_remove(state["timeout_id"])

            def fire():
                state["timeout_id"] = None
                run_async(lambda: apply_fn(int(value)), lambda _r: None)
                return GLib.SOURCE_REMOVE

            state["timeout_id"] = GLib.timeout_add(delay_ms, fire)

        return debounced

    def _build_volume_section(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.volume_icon_btn = Gtk.Button(label=ICON_VOLUME_HIGH)
        self.volume_icon_btn.get_style_context().add_class("qs-icon-btn")
        self.volume_icon_btn.connect("clicked", self._on_volume_icon_clicked)
        self.volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.volume_scale.set_draw_value(False)
        self.volume_scale.set_hexpand(True)
        self._volume_handler = self.volume_scale.connect("value-changed", self._on_volume_changed)
        self.volume_pct_label = Gtk.Label(label="0%")
        self.volume_pct_label.get_style_context().add_class("qs-row-sub")
        self.volume_pct_label.set_width_chars(4)
        box.pack_start(self.volume_icon_btn, False, False, 0)
        box.pack_start(self.volume_scale, True, True, 0)
        box.pack_start(self.volume_pct_label, False, False, 0)
        self.muted = False
        self._debounced_set_volume = self._make_debounced(set_volume)
        return box

    def _build_brightness_section(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        icon = Gtk.Label(label=ICON_BRIGHTNESS)
        icon.get_style_context().add_class("qs-header-icon")
        self.brightness_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.brightness_scale.set_draw_value(False)
        self.brightness_scale.set_hexpand(True)
        self._brightness_handler = self.brightness_scale.connect(
            "value-changed", self._on_brightness_changed
        )
        self.brightness_pct_label = Gtk.Label(label="0%")
        self.brightness_pct_label.get_style_context().add_class("qs-row-sub")
        self.brightness_pct_label.set_width_chars(4)
        box.pack_start(icon, False, False, 0)
        box.pack_start(self.brightness_scale, True, True, 0)
        box.pack_start(self.brightness_pct_label, False, False, 0)
        self._debounced_set_brightness = self._make_debounced(set_brightness)
        return box

    def _update_volume_icon(self):
        if self.muted:
            self.volume_icon_btn.set_label(ICON_VOLUME_MUTE)
        else:
            val = self.volume_scale.get_value()
            self.volume_icon_btn.set_label(ICON_VOLUME_HIGH if val >= 50 else ICON_VOLUME_LOW)

    def _on_volume_changed(self, scale):
        val = int(scale.get_value())
        self.volume_pct_label.set_label("%d%%" % val)
        if self.muted and val > 0:
            # kéo thanh trượt trong lúc đang tắt tiếng -> tự bật lại tiếng,
            # đúng hành vi quen thuộc trên Windows/điện thoại
            self.muted = False
            run_async(lambda: set_volume_muted(False), lambda _r: None)
        self._update_volume_icon()
        self._debounced_set_volume(val)

    def _on_volume_icon_clicked(self, _btn):
        self.muted = not self.muted
        run_async(lambda: set_volume_muted(self.muted), lambda _r: None)
        self._update_volume_icon()

    def refresh_volume(self):
        run_async(get_volume, self._on_volume_loaded)

    def _on_volume_loaded(self, result):
        percent, muted = (0, False) if isinstance(result, Exception) else result
        self.muted = muted
        self.volume_scale.handler_block(self._volume_handler)
        self.volume_scale.set_value(percent)
        self.volume_scale.handler_unblock(self._volume_handler)
        self.volume_pct_label.set_label("%d%%" % percent)
        self._update_volume_icon()
        return GLib.SOURCE_REMOVE

    def _on_brightness_changed(self, scale):
        val = int(scale.get_value())
        self.brightness_pct_label.set_label("%d%%" % val)
        self._debounced_set_brightness(val)

    def refresh_brightness(self):
        run_async(get_brightness, self._on_brightness_loaded)

    def _on_brightness_loaded(self, percent):
        percent = 100 if isinstance(percent, Exception) else percent
        self.brightness_scale.handler_block(self._brightness_handler)
        self.brightness_scale.set_value(percent)
        self.brightness_scale.handler_unblock(self._brightness_handler)
        self.brightness_pct_label.set_label("%d%%" % percent)
        return GLib.SOURCE_REMOVE

    # ---- đóng/mở ----
    def dismiss(self):
        if self.dismissed or not self.fully_open:
            # Bỏ qua nếu đang giữa chừng lúc MỞ (animation phình/fade chưa
            # xong) — tránh 2 tween cùng gọi move_child() một lúc, giẫm
            # lên nhau gây giật/nhảy vị trí. Bấm lại sau khi mở xong hẳn.
            return
        self.dismissed = True

        def after_fade_out():
            self.pill.child.remove(self.content_box)
            self.content_box = None
            self._shrink_back()

        def fade_out(t):
            self.content_box.set_opacity(1 - t)

        tween(self.pill.win, fade_out, CONTENT_FADE_DURATION_MS, on_done=after_fade_out)

    def _shrink_back(self):
        def frame(t):
            cur = dict(
                x=lerp(self.merged["x"], self.orig["x"], t),
                y=lerp(self.merged["y"], self.orig["y"], t),
                w=lerp(self.merged["w"], self.orig["w"], t),
                h=lerp(self.merged["h"], self.orig["h"], t),
            )
            self.pill.move_child(cur["x"], cur["y"], cur["w"], cur["h"])

        tween(
            self.pill.win, frame, ANIM_DURATION_MS, on_done=self._wait_then_fade, on_ratio=show_waybar
        )

    def _wait_then_fade(self):
        GLib.timeout_add(POST_REVERSE_BUFFER_MS, lambda: (self._fade_out_overlay(), False)[1])

    def _fade_out_overlay(self):
        animate_window_opacity(self.pill.win, 0.0, FINAL_FADE_DURATION_MS, on_done=self._finish)

    def _finish(self):
        cleanup_pidfile()
        Gtk.main_quit()

    def _on_key(self, _widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.dismiss()


def main():
    running_pid = already_running()
    if running_pid:
        os.kill(running_pid, signal.SIGUSR1)  # đang mở -> bấm lần nữa = đóng
        sys.exit(0)

    with open(PIDFILE, "w") as f:
        f.write(str(os.getpid()))

    style_provider = Gtk.CssProvider()
    style_provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    panel = Panel()

    def on_sigusr1():
        panel.dismiss()
        return GLib.SOURCE_CONTINUE

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, on_sigusr1)

    try:
        Gtk.main()
    finally:
        cleanup_pidfile()


if __name__ == "__main__":
    main()
