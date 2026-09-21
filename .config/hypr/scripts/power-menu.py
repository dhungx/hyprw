#!/usr/bin/env python3
"""
power-menu.py — waybar "biến hình" thành dải nút nguồn (thay wlogout).

BỐI CẢNH: xem README mục "Menu nguồn" để biết lý do KHÔNG dùng wlogout
(hardcode neo 4 cạnh trong chính main.c của nó) và KHÔNG dùng
Quickshell/QML/eww/AGS (đo thực tế tốn RAM/GPU hơn nhiều lần so với GTK3 —
Quickshell ~400MB RAM + GPU trung bình 15%/đỉnh 50%, trong khi bar GTK3 chỉ
vài chục MB gần 0% GPU).

CÁCH HOẠT ĐỘNG — 3 CỬA SỔ LAYER-SHELL RIÊNG, KHÔNG PHẢI 1:
Waybar đọc config.jsonc đúng 1 lần lúc khởi động, không có API để "yêu cầu
nó animate sang layout khác" — nên phải tạo overlay riêng giả lập hình
dáng 3 viên thuốc của nó (trái=workspaces, giữa=đồng hồ, phải=system+tray)
rồi animate CHÍNH overlay đó. Đặt cả 3 ở layer OVERLAY (tầng cao nhất theo
đúng thứ tự wlr-layer-shell: background < bottom < top < overlay) để tự
động đè lên waybar (đang ở layer "top") — KHÔNG cần gửi lệnh ẩn/hiện
waybar thật, tránh mọi race-condition giữa ẩn cái này/hiện cái kia. Waybar
thật không hề bị tắt trong suốt quá trình, số liệu luôn mới khi menu đóng.

CÁCH "GỘP THÀNH 1 VIÊN THUỐC": cửa sổ TRÁI và PHẢI tween nhỏ dần về 0 và
trượt vào đúng vị trí 2 đầu viên thuốc đích (biến mất khi hết animation);
cửa sổ GIỮA (vốn là đồng hồ) mới là cái thật sự phình to ra chiếm trọn
chiều dài viên thuốc cuối cùng và giữ 5 nút bấm bên trong — chỉ 1 cửa sổ
cần chứa widget nút bấm thật, đỡ phải chia 5 nút cắt ngang qua ranh giới
3 cửa sổ khác nhau (phức tạp không cần thiết cho đúng hiệu ứng thị giác
muốn có).

XÁC MINH KỸ THUẬT QUAN TRỌNG (không tự đổi hướng nếu chưa đọc):
- GtkLayerShell.set_margin()/window.resize() là API thật, đã xác nhận qua
  ví dụ chính thức gtk-layer-shell + docs.gtk.org/gtk3/method.Window.resize —
  NHƯNG resize() mặc định KHÔNG cho nhỏ hơn "size request" hiện tại, nên
  bắt buộc gọi set_size_request() ngay trước mỗi lần resize() trong vòng
  tween, không gọi 1 lần lúc đầu là đủ.
- CSS transform (translate/scale) KHÔNG áp dụng được cho widget thường
  trong GTK3 — xác nhận qua mailing list chính thức GNOME (gtk-list,
  05/2017) và docs.gtk.org/gtk3 (chỉ -gtk-icon-transform cho icon, không
  có transform chung). Nên toàn bộ animation "di chuyển/co giãn" ở đây
  tween thẳng x/y/width/height của cửa sổ qua GLib.timeout_add, không
  dùng CSS transition/transform.
- Toạ độ 3 viên thuốc lấy qua `hyprctl monitors -j` (trường width/height/
  x/y/focused — xác nhận từ output thật trong báo lỗi hyprwm/Hyprland
  #2921), CHỌN ĐÚNG monitor có "focused": true để đúng khi nhiều màn hình.
  Kích thước ước lượng theo layout đã biết + height:34/margin:6px 3px thật
  của waybar hiện tại — phần NÀY LÀ ƯỚC LƯỢNG, đánh dấu rõ bên dưới, chỉnh
  tay theo số đo thật sau khi lên máy thật (khó chính xác 100% vì Hyprland
  không biết toạ độ widget bên trong 1 app GTK, chỉ biết toạ độ cả cửa sổ).

TOGGLE: không chạy nền — mỗi lần Super+M spawn mới, dùng PID file để biết
đã mở chưa, gửi SIGUSR1 cho tiến trình đang chạy để nó tự đóng thay vì mở
chồng bản 2. RAM = 0 khi đã đóng.
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
ANIM_STEPS = 20
ANIM_INTERVAL_MS = 12          # ~20 bước x 12ms ≈ 240ms cho phần gộp hình
CONTENT_FADE_STEPS = 12
CONTENT_FADE_INTERVAL_MS = 14  # ~170ms cho phần icon fade riêng, chạy SAU

# ── Vị trí/kích thước ƯỚC LƯỢNG — CHỈNH TAY SAU KHI ĐO TRÊN MÁY THẬT ────
# Khớp với height:34 + margin:6px 3px thật trong waybar/config.jsonc và
# style.css hiện tại. Bề rộng mỗi cụm là suy đoán hợp lý theo nội dung
# (workspaces ~4 chấm, đồng hồ "HH:MM", system-pill gộp cpu/ram/volume/
# network/battery/power + tray) — SAI VÀI CHỤC PX LÀ CHẤP NHẬN ĐƯỢC vì
# nội dung cũ đã ẩn trước khi bay, mắt khó nhận ra lệch nhỏ.
BAR_TOP = 6          # margin-top thật của mỗi pill (từ style.css)
BAR_HEIGHT = 34      # height thật khai trong config.jsonc

WORKSPACES_WIDTH = 120   # TODO: đo lại — phụ thuộc bạn tạo bao nhiêu workspace
CLOCK_WIDTH = 90
SYSTEM_TRAY_WIDTH = 420  # TODO: đo lại — phụ thuộc số icon tray thật hiện có

PILL_GAP = 8  # khoảng cách giữa các viên thuốc hiện tại (khớp waybar)

ACTIONS = [
    ("lock", "\uf023", "Khoá máy", ["hyprlock"]),
    ("logout", "\uf08b", "Đăng xuất", ["hyprctl", "dispatch", "exit"]),
    ("suspend", "\uf4ee", "Ngủ", ["systemctl", "suspend"]),
    ("reboot", "\uf021", "Khởi động lại", ["systemctl", "reboot"]),
    ("shutdown", "\uf011", "Tắt máy", ["systemctl", "poweroff"]),
]

CSS = b"""
window#pm-left, window#pm-right, window#pm-mid {
    background-color: transparent;
}
box.pm-bg {
    background-color: rgba(30, 30, 46, 0.90);
    border: 2px solid rgba(137, 180, 250, 0.35);
}
/* rounded only at outer ends; square where windows touch, see docstring */
box.pm-bg.round-left  { border-radius: 999px 0 0 999px; border-right-width: 0; }
box.pm-bg.round-right { border-radius: 0 999px 999px 0; border-left-width: 0; }
box.pm-bg.round-both  { border-radius: 999px; }
box.pm-bg.round-none  { border-radius: 0; border-left-width: 0; border-right-width: 0; }

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
    """Đọc hyprctl monitors -j, trả về (width, height, x, y) của monitor
    đang focus — KHÔNG mặc định monitor đầu tiên/toạ độ (0,0), vì máy nhiều
    màn hình thì waybar có thể không nằm ở monitor đó."""
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
    return 1920, 1080, 0, 0  # dự phòng nếu lệnh lỗi — 1080p là an toàn nhất


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


class Pill:
    """1 cửa sổ layer-shell — dùng chung cho cả 3 viên thuốc."""

    def __init__(self, name, round_class, monitor_x):
        self.win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.win.set_name(name)
        self.win.set_decorated(False)
        self.monitor_x = monitor_x  # để tính margin-left tuyệt đối trên đúng monitor

        GtkLayerShell.init_for_window(self.win)
        GtkLayerShell.set_layer(self.win, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_namespace(self.win, "hyprw-power-menu")
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_keyboard_mode(self.win, GtkLayerShell.KeyboardMode.NONE)

        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.box.get_style_context().add_class("pm-bg")
        self.box.get_style_context().add_class(round_class)
        self.win.add(self.box)

    def set_geometry(self, x, y, w, h):
        """x/y tuyệt đối trên monitor -> margin left/top cho layer-shell."""
        left_margin = x - self.monitor_x
        GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.LEFT, int(left_margin))
        GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.TOP, int(y))
        # PHẢI set_size_request trước resize — resize() mặc định không cho
        # nhỏ hơn size request hiện có (xác nhận qua docs.gtk.org)
        w, h = max(1, int(w)), max(1, int(h))
        self.win.set_size_request(w, h)
        self.win.resize(w, h)


def tween(get_frames, duration_steps, interval_ms, on_done=None):
    """Chạy 1 vòng tween chung — get_frames(t_eased) trả list hàm áp dụng
    khung hình thứ i, gọi 1 lần mỗi tick cho tới khi xong."""
    step = {"i": 0}

    def tick():
        step["i"] += 1
        t = step["i"] / duration_steps
        eased = ease_out_cubic(t)
        get_frames(eased)
        if step["i"] >= duration_steps:
            if on_done:
                on_done()
            return False
        return True

    GLib.timeout_add(interval_ms, tick)


def lerp(a, b, t):
    return a + (b - a) * t


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

    # ── Vị trí GỐC (đúng như 3 viên thuốc waybar thật đang đứng) ────────
    orig_left = dict(x=mon_x + 9, y=mon_y + BAR_TOP, w=WORKSPACES_WIDTH, h=BAR_HEIGHT)
    orig_mid = dict(
        x=mon_x + mon_w / 2 - CLOCK_WIDTH / 2, y=mon_y + BAR_TOP, w=CLOCK_WIDTH, h=BAR_HEIGHT
    )
    orig_right = dict(
        x=mon_x + mon_w - SYSTEM_TRAY_WIDTH - 9, y=mon_y + BAR_TOP, w=SYSTEM_TRAY_WIDTH, h=BAR_HEIGHT
    )

    # ── Vị trí ĐÍCH khi đã gộp — 1 viên thuốc dài, canh giữa màn hình ───
    merged_width = min(560, mon_w - 40)
    merged_x = mon_x + mon_w / 2 - merged_width / 2
    merged_mid = dict(x=merged_x, y=mon_y + BAR_TOP, w=merged_width, h=BAR_HEIGHT)
    # trái/phải co về đúng 2 mép của merged_mid rồi biến mất (width -> 0)
    merged_left = dict(x=merged_x, y=mon_y + BAR_TOP, w=0, h=BAR_HEIGHT)
    merged_right = dict(x=merged_x + merged_width, y=mon_y + BAR_TOP, w=0, h=BAR_HEIGHT)

    left_pill = Pill("pm-left", "round-left", mon_x)
    mid_pill = Pill("pm-mid", "round-both", mon_x)   # round-both vì lúc đầu là 1 viên riêng (đồng hồ)
    right_pill = Pill("pm-right", "round-right", mon_x)

    clock_label = Gtk.Label(label=GLib.DateTime.new_now_local().format("%H:%M"))
    clock_label.get_style_context().add_class("pm-clock")
    mid_pill.box.set_center_widget(clock_label)

    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    for p, geo in ((left_pill, orig_left), (mid_pill, orig_mid), (right_pill, orig_right)):
        p.set_geometry(geo["x"], geo["y"], geo["w"], geo["h"])
        p.win.show_all()

    state = {
        "dismissed": False,
        "buttons_shown": False,
        # Vị trí THẬT đang đứng — cập nhật mỗi khung hình animation, để
        # nếu bấm đóng giữa lúc đang mở dở thì tween ngược từ đây, không
        # phải từ toạ độ "đã gộp xong" cứng — tránh giật hình nhảy cóc khi
        # bấm Super+M liên tục nhanh (đúng điều cần test theo yêu cầu).
        "current": {"left": dict(orig_left), "mid": dict(orig_mid), "right": dict(orig_right)},
    }

    # ── Mở: gộp hình -> đổi bo góc thành phẳng ở giữa -> fade icon vào ──
    def animate_open():
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
                p.set_geometry(cur["x"], cur["y"], cur["w"], cur["h"])

        def after_merge():
            left_pill.win.hide()
            right_pill.win.hide()
            # Giữa lúc này đã phình to full-width — chuyển bo góc sang "cả
            # 2 đầu tròn" (đã là round-both từ đầu nên không cần đổi class)
            swap_content_to_buttons()

        tween(frame, ANIM_STEPS, ANIM_INTERVAL_MS, on_done=after_merge)

    def swap_content_to_buttons():
        clock_label.set_opacity(0)
        for child in list(mid_pill.box.get_children()):
            mid_pill.box.remove(child)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        row.set_opacity(0)
        for name, icon, label, cmd in ACTIONS:
            row.pack_start(make_button(name, icon, label, cmd), True, True, 0)
        mid_pill.box.pack_start(row, True, True, 0)
        mid_pill.box.show_all()
        state["buttons_shown"] = True

        def fade(t):
            row.set_opacity(t)

        tween(fade, CONTENT_FADE_STEPS, CONTENT_FADE_INTERVAL_MS)

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

    # ── Đóng: fade icon ra -> tách hình về vị trí gốc -> đóng hẳn ───────
    def dismiss(after_cmd=None):
        if state["dismissed"]:
            return
        state["dismissed"] = True

        def do_geometry_reverse():
            left_pill.win.show_all()
            right_pill.win.show_all()

            # Bắt đầu tween ngược từ vị trí THẬT đang đứng (state["current"]),
            # không phải từ merged_* hardcode — nếu bấm đóng giữa lúc animation
            # mở chưa xong (buttons_shown vẫn False), current lúc này là 1
            # điểm dở dang bất kỳ, không phải merged_*, tween từ merged_* sẽ
            # làm cửa sổ nhảy cóc tới đó trước rồi mới lùi lại, giật hình.
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
                    p.set_geometry(cur["x"], cur["y"], cur["w"], cur["h"])

            tween(frame, ANIM_STEPS, ANIM_INTERVAL_MS, on_done=finish)

        def finish():
            cleanup_pidfile()
            if after_cmd:
                subprocess.Popen(after_cmd)
            Gtk.main_quit()

        if state["buttons_shown"]:
            row = mid_pill.box.get_children()[0]

            def fade_out(t):
                row.set_opacity(1 - t)

            def after_fade():
                for child in list(mid_pill.box.get_children()):
                    mid_pill.box.remove(child)
                mid_pill.box.set_center_widget(clock_label)
                clock_label.set_opacity(1)
                mid_pill.box.show_all()
                do_geometry_reverse()

            tween(fade_out, CONTENT_FADE_STEPS, CONTENT_FADE_INTERVAL_MS, on_done=after_fade)
        else:
            # Đóng ngay lúc đang animate mở dở, chưa kịp hiện nút -> bỏ
            # qua bước fade nút, tách hình về luôn
            do_geometry_reverse()

    def on_key(_widget, event):
        if event.keyval == Gdk.KEY_Escape:
            dismiss()

    for p in (left_pill, mid_pill, right_pill):
        p.win.connect("key-press-event", on_key)
        p.win.connect("destroy", lambda *_a: None)  # dọn dẹp thật nằm ở finish()

    def on_sigusr1():
        dismiss()
        return GLib.SOURCE_CONTINUE

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, on_sigusr1)

    GLib.timeout_add(20, lambda: (animate_open(), False)[1])

    Gtk.main()
    cleanup_pidfile()


if __name__ == "__main__":
    main()
