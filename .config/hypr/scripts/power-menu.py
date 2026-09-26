#!/usr/bin/env python3
"""
power-menu.py — waybar "ẩn hiện thật", không còn "che" giả lập (thay wlogout).

BỐI CẢNH: xem README mục "Menu nguồn". Không dùng wlogout (hardcode neo 4
cạnh trong chính main.c của nó). Không dùng Quickshell/QML/eww/AGS/Astal —
đo thực tế 1 bar Quickshell ~400MB RAM, GPU trung bình 15%/đỉnh 50%, trong
khi GTK3 chỉ vài chục MB gần 0% GPU trên cùng máy.

BẢN 2 (bản này) SỬA 2 VẤN ĐỀ CỦA BẢN 1:

1) Bản 1 tạo 3 cửa sổ overlay kích thước ƯỚC LƯỢNG để "che khít" lên đúng
   3 viên thuốc waybar thật bên dưới. Ước lượng sai vài chục px là lộ 1
   phần viên thuốc thật ra ngoài, thấy rõ trong lúc animation chạy.
   FIX: bỏ hẳn ý định "che" — chuyển sang ẨN THẬT waybar qua signal
   SIGUSR1 (waybar tự hỗ trợ qua key "on-sigusr1"/"on-sigusr2" trong
   config.jsonc, xác nhận qua man page chính thức waybar.5). Sau khi ẩn,
   không còn gì thật ở dưới để mà lộ ra nữa — kích thước overlay từ đây
   chỉ ảnh hưởng thẩm mỹ điểm bắt đầu animation, không còn gây lỗi hiển
   thị nếu lệch vài chục px.
   - animate_open(): killall -SIGUSR1 waybar (ẩn) NGAY ĐẦU, trước khi
     hiện overlay.
   - dismiss(): killall -SIGUSR2 waybar (hiện) đúng lúc overlay GẦN như
     đã đóng xong (opacity gần 0) — KHÔNG phải sau khi đã đóng hẳn. Lúc
     đó overlay gần như vô hình nên chồng lấp ngắn với waybar thật không
     ai nhận ra; ngược lại nếu đợi overlay đóng hết rồi mới gửi signal sẽ
     có 1 khoảng trống thấy rõ (không overlay, không waybar) khó chịu hơn.
   - Lưu ý đã biết: waybar không tự báo trạng thái qua signal, nên
     SIGUSR2 làm waybar "show" có thể có chớp/delay/IO nhẹ (ghi nhận từ
     dự án waybar_auto_hide có thật dùng đúng kỹ thuật này) — chấp nhận
     được, không phải lỗi code.

2) Bản 1 gọi lại GtkLayerShell.set_margin()/win.resize() MỖI KHUNG HÌNH
   (~20 khung/animation) — mỗi lần là 1 vòng đàm phán THẬT với Wayland
   compositor, nặng hơn hẳn so với chỉ vẽ lại nội dung trong 1 cửa sổ đã
   có sẵn kích thước cố định.
   FIX: mỗi trong 3 khu vực chỉ tạo ĐÚNG 1 CỬA SỔ layer-shell lúc khởi
   tạo, kích thước = hợp bao (union) của vị trí gốc + vị trí đích (không
   resize lại window này nữa). Bên trong dùng Gtk.Fixed chứa 1 widget con
   (hình viên thuốc/vùng nút) — mỗi khung hình animation chỉ gọi
   Gtk.Fixed.move()+set_size_request() trên WIDGET CON này, là thao tác
   nội bộ GTK, không kích hoạt đàm phán giao thức Wayland như resize cửa
   sổ thật, nên nhẹ/mượt hơn nhiều.

XÁC MINH KỸ THUẬT (không tự đổi hướng nếu chưa đọc):
- GtkLayerShell.set_margin() là lệnh giao thức Wayland thật
  (zwlr_layer_surface_v1::set_margin), không phải CSS property.
- GTK3 không có CSS transform cho widget thường (chỉ -gtk-icon-transform
  cho icon) — xác nhận qua docs.gtk.org + mailing list GNOME 05/2017.
- Gtk.Window.resize() mặc định không cho nhỏ hơn "size request" hiện có —
  xác nhận từ docs.gtk.org. Với cửa sổ THẬT trong bản này, điều này không
  còn quan trọng vì không resize window thật nữa (chỉ resize widget con
  trong Gtk.Fixed, không bị ràng buộc này).
- wlr-layer-shell có 4 tầng: background < bottom < top < overlay. Waybar
  chạy ở tầng "top" mặc định — đặt overlay này ở tầng OVERLAY để tự đè lên.
- waybar hỗ trợ on-sigusr1/on-sigusr2 (show/hide/toggle/reload/noop) —
  xác nhận qua man.archlinux.org/man/waybar.5 + wiki chính thức Alexays/
  Waybar. Dùng giá trị tường minh show/hide (không dùng mặc định toggle/
  reload) vì toggle mặc định được chính người dùng Waybar báo cáo không
  đáng tin cậy khi gửi signal dồn dập (issue #3928).
- Icon suspend sửa từ \\uf4ee (nhầm, thuộc Octicon) sang \\uf186 (nf-fa-moon,
  "Power Sleep Symbol" — xác nhận qua 2 nguồn độc lập đều ghi
  IconData...(0xf186) cho moon).

TOGGLE (không đổi so với bản 1): PID file + SIGUSR1 riêng của chính script
này (khác SIGUSR1 gửi cho waybar ở trên — 2 việc khác nhau). Không chạy
nền thường trực, spawn mới mỗi lần Super+M, RAM = 0 khi đã đóng.
"""
import json
import os
import subprocess
import sys
import signal
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell  # noqa: E402

PIDFILE = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "hyprw-powermenu.pid")

# ── Animation ──────────────────────────────────────────────────────────
# Thời lượng tính bằng ms — KHÔNG còn tách STEPS/INTERVAL_MS như bản trước.
# tween() giờ chạy theo frame clock thật của compositor (xem docstring hàm
# tween), không đếm số bước cố định nữa, nên chỉ cần biết chạy bao lâu.
ANIM_DURATION_MS = 240
CONTENT_FADE_DURATION_MS = 168
# Gửi SIGUSR2 (hiện waybar thật) khi animation đóng đã chạy tới tỉ lệ này
# trong tổng thời lượng — KHÔNG đợi đến 100% (xem lý do trong docstring).
SHOW_WAYBAR_AT_RATIO = 0.80
# Sau khi animation hình dạng đã về xong vị trí gốc, waybar thật CHƯA CHẮC
# đã kịp redraw xong (SIGUSR2 không tức thời — có "chớp/delay nhẹ" như ghi ở
# trên) và bản thân waybar KHÔNG có animation tự hiện lại (chỉ "bật phắt").
# Thay vì đóng overlay ngay, đợi thêm 1 khoảng đệm rồi tự FADE OPACITY cả 3
# cửa sổ overlay (không phải nội dung, mà toàn bộ cửa sổ) — việc này che
# được khoảng bất định "chưa biết waybar redraw xong lúc nào", biến cú
# "bật phắt" của waybar thành 1 cú tan biến mượt của overlay, dù waybar bên
# dưới có xuất hiện sớm hay muộn hơn dự kiến vài chục ms cũng không lộ ra.
POST_REVERSE_BUFFER_MS = 120
FINAL_FADE_DURATION_MS = 150
# Đối xứng với POST_REVERSE_BUFFER_MS ở trên nhưng cho chiều MỞ: SIGUSR1
# cũng không ẩn waybar tức thời. Nếu animation đổi hình dạng bắt đầu ngay
# khi vừa gửi SIGUSR1, overlay có thể đã đổi hình dạng (rời khỏi đúng vị
# trí khớp ban đầu) trong khi waybar thật CHƯA kịp ẩn xong — lộ ra 1 phần
# waybar thật trong khoảnh khắc đó. Đợi buffer này TRƯỚC khi bắt đầu animate
# hình dạng — lúc này overlay vẫn đứng yên đúng khớp vị trí gốc nên dù có
# đợi thêm cũng không ai thấy khác biệt gì, an toàn hơn hẳn bắt đầu ngay.
OPEN_HIDE_BUFFER_MS = 120

# ── Vị trí/kích thước 3 viên thuốc gốc — tính từ SỐ THẬT trong
# .config/waybar/config.jsonc + style.css (không còn đoán từ đầu như bản
# trước). Vẫn là ước lượng vì waybar không có IPC trả toạ độ pixel thật
# của từng module — nhưng giờ bám theo đúng padding/font-size/số workspace
# thật thay vì số ngẫu nhiên. Chỉ còn TRAY_ICON_COUNT là phải đoán tay
# (số icon khay hệ thống tuỳ app đang chạy, không có cách truy vấn trước).
BAR_TOP = 6
BAR_HEIGHT = 34
FONT_SIZE = 13  # style.css: `* { font-size: 13px }`
MONO_CHAR_WIDTH = FONT_SIZE * 0.6  # quy ước chung font monospace ≈ 0.6em/ký tự
EDGE_MARGIN = 3  # style.css: `margin: 6px 3px` (3px = mép ngoài cùng trái/phải)

# #workspaces { padding: 0 4px } + mỗi button { padding: 0 6px } + 1 glyph
WORKSPACES_OUTER_PADDING = 8
WORKSPACE_BUTTON_WIDTH = 12 + FONT_SIZE

# group-clock-drawer dùng padding mặc định 0 10px; nội dung luôn hiện chỉ
# có "#clock" (format "{:%H:%M}" = 5 ký tự, "clock#detail" ẩn khi không hover)
CLOCK_OUTER_PADDING = 20
CLOCK_CHARS = 5

# #group-system-pill { padding: 0 4px } + 7 phần con. PHÁT HIỆN LẠI khi
# thêm quick-settings.py: cpu/memory/battery KHÔNG chỉ-icon như tưởng ban
# đầu — format thật là "icon {usage}%"/"icon {percentage}%"/"icon
# {capacity}%" (xem config.jsonc), tức có thêm 2-3 ký tự số + dấu %. Chỉ
# pulseaudio/network/bluetooth/custom-power mới thật sự chỉ-icon (detail
# dạng số nằm trong module #detail riêng, ẩn tới khi hover).
SYSTEM_PILL_OUTER_PADDING = 8
SYSTEM_PILL_ICON_ONLY_COUNT = 4  # pulseaudio, network, bluetooth, custom/power
SYSTEM_PILL_ICON_ONLY_WIDTH = 12 + FONT_SIZE
SYSTEM_PILL_PERCENT_COUNT = 3  # cpu, memory, battery — "icon NN%"
# icon + 1 khoảng trắng + tối đa 3 chữ số + "%" ~ 4-5 ký tự, lấy dư 1 chút
SYSTEM_PILL_PERCENT_WIDTH = 12 + FONT_SIZE + 4 * MONO_CHAR_WIDTH
# waybar "spacing": 4 → khoảng cách giữa #group-system-pill và #tray (2
# module riêng trong modules-right, xem config.jsonc)
MODULE_SPACING = 4
# #tray { padding: 0 8px } + N icon tray thật — TRAY_ICON_COUNT là số duy
# nhất trong file này không lấy được từ config, tuỳ app đang chạy (Discord/
# Telegram/...). Sửa số này nếu viên phải vẫn lệch nhiều so với tray thật.
TRAY_OUTER_PADDING = 16
TRAY_ICON_COUNT = 2
TRAY_ICON_WIDTH = 20

ACTIONS = [
    ("lock", "\uf023", "Khoá máy", ["hyprlock"]),
    ("logout", "\uf08b", "Đăng xuất", ["hyprctl", "dispatch", "exit"]),
    ("suspend", "\uf186", "Ngủ", ["systemctl", "suspend"]),
    ("reboot", "\uf021", "Khởi động lại", ["systemctl", "reboot"]),
    ("shutdown", "\uf011", "Tắt máy", ["systemctl", "poweroff"]),
]

CSS = b"""
window#pm-left, window#pm-right, window#pm-mid {
    background-color: transparent;
}
fixed { background-color: transparent; }
box.pm-bg {
    background-color: rgba(30, 30, 46, 0.90);
    border: 2px solid rgba(137, 180, 250, 0.35);
}
/* every pill (left/mid/right) is fully rounded at all times now, no more
   "square where they touch" hack, since left/right now fade out as they
   shrink (see comments in start_geometry_forward/do_geometry_reverse) and
   no longer assume they stay flush against the mid pill the whole time */
box.pm-bg.round-both  { border-radius: 999px; }
label.pm-clock {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 13px;
    color: #cdd6f4;
}
button {
    background: transparent;
    border: none;
    box-shadow: none;
    border-radius: 999px;
    padding: 8px 16px;
    transition: background-color 150ms ease;
}
button:hover { background-color: rgba(255, 255, 255, 0.10); }
label.pm-icon {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 19px;
    color: #cdd6f4;
}
label.pm-text {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 9px;
    color: #a6adc8;
}
button.pm-lock:hover label.pm-icon     { color: #a6e3a1; }
button.pm-logout:hover label.pm-icon   { color: #89b4fa; }
button.pm-suspend:hover label.pm-icon  { color: #cba6f7; }
button.pm-reboot:hover label.pm-icon   { color: #f9e2af; }
button.pm-shutdown:hover label.pm-icon { color: #f38ba8; }
"""


def already_running():
    if not os.path.exists(PIDFILE):
        return None
    try:
        with open(PIDFILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        return None


def get_focused_monitor():
    """Đọc hyprctl monitors -j, chọn ĐÚNG monitor đang focus (không mặc
    định monitor đầu/toạ độ (0,0) — quan trọng nếu dùng nhiều màn hình)."""
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


def get_workspace_count():
    """Số workspace ĐANG TỒN TẠI thật qua hyprctl — config.jsonc không bật
    persistent-workspaces nên waybar mặc định chỉ hiện đúng số này, không
    phải đoán như WORKSPACES_WIDTH ở bản trước."""
    try:
        out = subprocess.run(
            ["hyprctl", "workspaces", "-j"], capture_output=True, text=True, timeout=2
        ).stdout
        return max(1, len(json.loads(out)))
    except Exception:
        return 5


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def union_bbox(a, b):
    """Hợp bao 2 hình chữ nhật {x,y,w,h} — dùng làm kích thước CỬA SỔ
    THẬT cố định (tạo 1 lần, không resize lại). Widget con bên trong
    không bao giờ vượt ra ngoài phạm vi này trong suốt animation."""
    x0, y0 = min(a["x"], b["x"]), min(a["y"], b["y"])
    x1 = max(a["x"] + a["w"], b["x"] + b["w"])
    y1 = max(a["y"] + a["h"], b["y"] + b["h"])
    return dict(x=x0, y=y0, w=x1 - x0, h=y1 - y0)


def hide_waybar():
    subprocess.run(["killall", "-SIGUSR1", "waybar"], stderr=subprocess.DEVNULL)


def show_waybar():
    subprocess.run(["killall", "-SIGUSR2", "waybar"], stderr=subprocess.DEVNULL)


class Pill:
    """1 cửa sổ layer-shell — tạo 1 LẦN duy nhất ở kích thước union_bbox,
    không resize lại. Chứa 1 Gtk.Fixed + 1 widget con được di chuyển/đổi
    kích thước nội bộ (không đàm phán Wayland) qua move_child()."""

    def __init__(self, name, round_class, monitor_x, window_bbox):
        self.monitor_x = monitor_x
        self.bbox = window_bbox

        self.win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.win.set_name(name)
        self.win.set_decorated(False)

        GtkLayerShell.init_for_window(self.win)
        GtkLayerShell.set_layer(self.win, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_namespace(self.win, "hyprw-power-menu")
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.LEFT, True)

        left_margin = window_bbox["x"] - monitor_x
        GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.LEFT, int(left_margin))
        GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.TOP, int(window_bbox["y"]))
        self.win.set_size_request(int(window_bbox["w"]), int(window_bbox["h"]))

        self.fixed = Gtk.Fixed()
        self.win.add(self.fixed)

        self.child = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.child.get_style_context().add_class("pm-bg")
        self.child.get_style_context().add_class(round_class)
        self.fixed.put(self.child, 0, 0)

    def move_child(self, x, y, w, h):
        """x/y tuyệt đối trên monitor -> toạ độ TƯƠNG ĐỐI trong window cố
        định của chính nó (không đụng đến kích thước/vị trí window thật)."""
        rel_x = x - self.bbox["x"]
        rel_y = y - self.bbox["y"]
        self.fixed.move(self.child, int(rel_x), int(rel_y))
        self.child.set_size_request(max(1, int(w)), max(1, int(h)))


def tween(widget, get_frames, duration_ms, on_done=None, on_ratio=None):
    """Animate qua Gtk.Widget.add_tick_callback — đồng bộ FRAME CLOCK thật
    của compositor, thay vì GLib.timeout_add (hẹn giờ đồng hồ tường, không
    biết gì về nhịp làm mới màn hình thật). Đây là cách GTK chính thức
    khuyến nghị cho animation (docs.gtk.org, "Frame clocks").

    Bản trước dùng timeout 12ms cố định (~83 lần/giây) — trên màn 144Hz
    thật của máy này, chu kỳ khung hình thật là ~6.94ms, không chia hết
    cho 12ms, nên 2 nhịp liên tục lệch pha nhau: có khung timeout rơi vào
    giữa 2 lần vsync (phải đợi khung sau mới lên hình, tự nhiên khựng 1
    nhịp), có khung lại trùng gần sát vsync kế tiếp. Timeout càng ngắn để
    né vấn đề này càng vô nghĩa vì bản chất 2 đồng hồ (wall-clock timer và
    vsync) không đồng bộ với nhau. add_tick_callback do compositor tự gọi
    ĐÚNG mỗi lần thật sự có 1 khung hình mới để vẽ, nên luôn khớp bất kể
    màn hình 60Hz/144Hz/bất kỳ Hz nào — không còn khái niệm "bước" cố định,
    chỉ còn "đã trôi qua bao nhiêu ms thật" tại mỗi lần gọi.
    """
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


def main():
    running_pid = already_running()
    if running_pid:
        os.kill(running_pid, signal.SIGUSR1)
        sys.exit(0)

    with open(PIDFILE, "w") as f:
        f.write(str(os.getpid()))

    def cleanup_pidfile():
        try:
            os.remove(PIDFILE)
        except FileNotFoundError:
            pass

    mon_w, mon_h, mon_x, mon_y = get_focused_monitor()

    workspaces_width = WORKSPACES_OUTER_PADDING + get_workspace_count() * WORKSPACE_BUTTON_WIDTH
    clock_width = CLOCK_OUTER_PADDING + CLOCK_CHARS * MONO_CHAR_WIDTH
    tray_width = (
        SYSTEM_PILL_OUTER_PADDING
        + SYSTEM_PILL_ICON_ONLY_COUNT * SYSTEM_PILL_ICON_ONLY_WIDTH
        + SYSTEM_PILL_PERCENT_COUNT * SYSTEM_PILL_PERCENT_WIDTH
        + MODULE_SPACING
        + TRAY_OUTER_PADDING
        + TRAY_ICON_COUNT * TRAY_ICON_WIDTH
    )

    orig_left = dict(x=mon_x + EDGE_MARGIN, y=mon_y + BAR_TOP, w=workspaces_width, h=BAR_HEIGHT)
    orig_mid = dict(
        x=mon_x + mon_w / 2 - clock_width / 2, y=mon_y + BAR_TOP, w=clock_width, h=BAR_HEIGHT
    )
    orig_right = dict(
        x=mon_x + mon_w - tray_width - EDGE_MARGIN, y=mon_y + BAR_TOP, w=tray_width, h=BAR_HEIGHT
    )

    merged_width = min(560, mon_w - 40)
    merged_x = mon_x + mon_w / 2 - merged_width / 2
    merged_mid = dict(x=merged_x, y=mon_y + BAR_TOP, w=merged_width, h=BAR_HEIGHT)
    merged_left = dict(x=merged_x, y=mon_y + BAR_TOP, w=0, h=BAR_HEIGHT)
    merged_right = dict(x=merged_x + merged_width, y=mon_y + BAR_TOP, w=0, h=BAR_HEIGHT)

    left_pill = Pill("pm-left", "round-both", mon_x, union_bbox(orig_left, merged_left))
    mid_pill = Pill("pm-mid", "round-both", mon_x, union_bbox(orig_mid, merged_mid))
    right_pill = Pill("pm-right", "round-both", mon_x, union_bbox(orig_right, merged_right))

    # Chỉ cửa sổ GIỮA nhận keyboard (ON_DEMAND — chỉ nhận khi đang focus,
    # không chiếm keyboard toàn cục) để phím Esc hoạt động. Bản 1 vô tình
    # đặt NONE cho cả 3, khiến Esc không bao giờ nhận được sự kiện — sửa
    # luôn trong bản này.
    GtkLayerShell.set_keyboard_mode(mid_pill.win, GtkLayerShell.KeyboardMode.ON_DEMAND)
    GtkLayerShell.set_keyboard_mode(left_pill.win, GtkLayerShell.KeyboardMode.NONE)
    GtkLayerShell.set_keyboard_mode(right_pill.win, GtkLayerShell.KeyboardMode.NONE)

    clock_label = Gtk.Label(label=GLib.DateTime.new_now_local().format("%H:%M"))
    clock_label.get_style_context().add_class("pm-clock")
    mid_pill.child.set_center_widget(clock_label)

    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    for p, geo in ((left_pill, orig_left), (mid_pill, orig_mid), (right_pill, orig_right)):
        p.move_child(geo["x"], geo["y"], geo["w"], geo["h"])
        p.win.show_all()

    state = {
        "dismissed": False,
        "buttons_shown": False,
        "current": {"left": dict(orig_left), "mid": dict(orig_mid), "right": dict(orig_right)},
    }

    def animate_open():
        hide_waybar()  # ẨN THẬT waybar NGAY ĐẦU — bỏ hẳn ý định "che" giả lập
        # Đợi OPEN_HIDE_BUFFER_MS trước khi bắt đầu đổi hình dạng — cho
        # waybar thật kịp ẩn xong (xem giải thích ở khai báo hằng số phía trên)
        GLib.timeout_add(OPEN_HIDE_BUFFER_MS, lambda: (start_geometry_forward(), False)[1])

    def start_geometry_forward():
        def frame(t):
            for key, p, a, b in (
                ("left", left_pill, orig_left, merged_left),
                ("mid", mid_pill, orig_mid, merged_mid),
                ("right", right_pill, orig_right, merged_right),
            ):
                cur = dict(
                    x=lerp(a["x"], b["x"], t), y=lerp(a["y"], b["y"], t),
                    w=lerp(a["w"], b["w"], t), h=lerp(a["h"], b["h"], t),
                )
                state["current"][key] = cur
                p.move_child(cur["x"], cur["y"], cur["w"], cur["h"])
            # Viên trái/phải MỜ DẦN cùng nhịp t với việc co kích thước.
            # Trước đây: co xong (t=1) mới hide() đột ngột — lúc đó w đã
            # kẹp về tối thiểu 1px (do max(1, int(w)) trong move_child) mà
            # viền 2px của box vẫn còn màu, nên bị "chớp/khựng" đúng 1 cái
            # ngay lúc hide(). Giờ opacity giảm đều 1→0 theo cùng t nên biến
            # mất hẳn ĐÚNG lúc w chạm 0 — không còn cạnh/viền sót lại để lộ.
            left_pill.child.set_opacity(1 - t)
            right_pill.child.set_opacity(1 - t)

        def after_merge():
            left_pill.child.hide()
            right_pill.child.hide()
            swap_content_to_buttons()

        tween(mid_pill.win, frame, ANIM_DURATION_MS, on_done=after_merge)

    def swap_content_to_buttons():
        # Trước đây: clock_label.set_opacity(0) tắt NGAY không animation,
        # trong khi nút bấm lại fade vào có animation — 1 bên cắt cứng, 1
        # bên mượt, nhìn lệch pha giống bị khựng. Giờ tách 2 pha nối tiếp,
        # PHA NÀO CŨNG có animation: mờ đồng hồ trước, đợi mờ hẳn (opacity
        # 0) mới đổi nội dung — lúc này đổi con không ai thấy vì đã vô hình
        # — rồi mới fade nút bấm hiện ra.
        def fade_out_clock(t):
            clock_label.set_opacity(1 - t)

        def after_clock_fade():
            for child in list(mid_pill.child.get_children()):
                mid_pill.child.remove(child)

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            row.set_opacity(0)
            for name, icon, label, cmd in ACTIONS:
                row.pack_start(make_button(name, icon, label, cmd), True, True, 0)
            mid_pill.child.pack_start(row, True, True, 0)
            mid_pill.child.show_all()
            state["buttons_shown"] = True

            def fade_in_row(t):
                row.set_opacity(t)

            tween(mid_pill.win, fade_in_row, CONTENT_FADE_DURATION_MS)

        tween(mid_pill.win, fade_out_clock, CONTENT_FADE_DURATION_MS, on_done=after_clock_fade)

    def make_button(name, icon, label, cmd):
        btn = Gtk.Button()
        btn.get_style_context().add_class(f"pm-{name}")
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        icon_lbl = Gtk.Label(label=icon)
        icon_lbl.get_style_context().add_class("pm-icon")
        text_lbl = Gtk.Label(label=label)
        text_lbl.get_style_context().add_class("pm-text")
        inner.pack_start(icon_lbl, False, False, 0)
        inner.pack_start(text_lbl, False, False, 0)
        btn.add(inner)
        btn.connect("clicked", lambda _b: dismiss(after_cmd=cmd))
        return btn

    def dismiss(after_cmd=None):
        if state["dismissed"]:
            return
        state["dismissed"] = True

        def do_geometry_reverse():
            # opacity 0 TRƯỚC khi show() — không set thì widget hiện full-
            # opacity ngay ở kích thước gần 0px rồi mới phình ra, thấy 1 cú
            # loé/khựng ngay lúc bắt đầu tách (đối xứng lỗi cũ bên fade khi
            # gộp: xem comment trong start_geometry_forward()).
            left_pill.child.set_opacity(0)
            right_pill.child.set_opacity(0)
            left_pill.child.show()
            right_pill.child.show()

            start = {
                "left": dict(state["current"]["left"]),
                "mid": dict(state["current"]["mid"]),
                "right": dict(state["current"]["right"]),
            }

            def frame(t):
                for key, p, a, b in (
                    ("left", left_pill, start["left"], orig_left),
                    ("mid", mid_pill, start["mid"], orig_mid),
                    ("right", right_pill, start["right"], orig_right),
                ):
                    cur = dict(
                        x=lerp(a["x"], b["x"], t), y=lerp(a["y"], b["y"], t),
                        w=lerp(a["w"], b["w"], t), h=lerp(a["h"], b["h"], t),
                    )
                    state["current"][key] = cur
                    p.move_child(cur["x"], cur["y"], cur["w"], cur["h"])
                # Hiện dần cùng nhịp t với việc phình kích thước — mirror
                # của fade-out trong start_geometry_forward().
                left_pill.child.set_opacity(t)
                right_pill.child.set_opacity(t)

            # show_waybar() tự gọi qua on_ratio khi animation đóng đã chạy
            # tới SHOW_WAYBAR_AT_RATIO (gần xong nhưng chưa hết hoàn toàn).
            # on_done giờ là wait_then_fade (không phải finish trực tiếp) —
            # xem giải thích ở khai báo POST_REVERSE_BUFFER_MS phía trên.
            tween(mid_pill.win, frame, ANIM_DURATION_MS, on_done=wait_then_fade, on_ratio=show_waybar)

        def wait_then_fade():
            GLib.timeout_add(POST_REVERSE_BUFFER_MS, lambda: (fade_out_overlay(), False)[1])

        def fade_out_overlay():
            def fade(t):
                opacity = 1 - t
                for p in (left_pill, mid_pill, right_pill):
                    p.win.set_opacity(opacity)

            tween(mid_pill.win, fade, FINAL_FADE_DURATION_MS, on_done=finish)

        def finish():
            cleanup_pidfile()
            if after_cmd:
                subprocess.Popen(after_cmd)
            Gtk.main_quit()

        if state["buttons_shown"]:
            row = mid_pill.child.get_children()[0]

            def fade_out(t):
                row.set_opacity(1 - t)

            def after_fade():
                for child in list(mid_pill.child.get_children()):
                    mid_pill.child.remove(child)
                mid_pill.child.set_center_widget(clock_label)
                clock_label.set_opacity(0)
                mid_pill.child.show_all()

                # Cập nhật giờ:phút mới nhất — tránh đứng hình giờ cũ nếu
                # người dùng mở menu và để lâu rồi mới đóng lại.
                clock_label.set_label(GLib.DateTime.new_now_local().format("%H:%M"))

                def fade_in_clock(t):
                    clock_label.set_opacity(t)

                # Đồng hồ fade hiện ra XONG rồi mới bắt đầu animation hình
                # dạng (do_geometry_reverse) — mirror đúng thứ tự bên mở
                # (hình dạng xong mới tới fade nội dung), thay vì trước đây
                # đồng hồ bật full-opacity đột ngột không animation.
                tween(mid_pill.win, fade_in_clock, CONTENT_FADE_DURATION_MS, on_done=do_geometry_reverse)

            tween(mid_pill.win, fade_out, CONTENT_FADE_DURATION_MS, on_done=after_fade)
        else:
            do_geometry_reverse()

    def on_key(_widget, event):
        if event.keyval == Gdk.KEY_Escape:
            dismiss()

    mid_pill.win.connect("key-press-event", on_key)
    for p in (left_pill, mid_pill, right_pill):
        p.win.connect("destroy", lambda *_a: None)

    def on_sigusr1():
        dismiss()
        return GLib.SOURCE_CONTINUE

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, on_sigusr1)

    GLib.timeout_add(20, lambda: (animate_open(), False)[1])

    Gtk.main()
    cleanup_pidfile()


if __name__ == "__main__":
    main()
