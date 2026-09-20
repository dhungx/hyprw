#!/usr/bin/env python3
"""
power-menu.py — dải nút nguồn tích hợp kiểu bar (thay wlogout).

LÝ DO VIẾT RIÊNG (không dùng wlogout): mã nguồn thật của wlogout
(ArtsyMacaw/wlogout/main.c, hàm set_fullscreen) hardcode neo cả 4 cạnh màn
hình bằng vòng lặp `for (j=0; j<GTK_LAYER_SHELL_EDGE_ENTRY_NUMBER; j++)
gtk_layer_set_anchor(win, j, TRUE)` — không có config nào đổi được việc
này, đây là giới hạn ở code gốc, không phải thiếu tuỳ chọn. Waybar cũng
không đọc lại layout khi nhận phím tắt (chỉ đọc config.jsonc 1 lần lúc
khởi động). Nên phần này phải là 1 layer-shell surface riêng, viết bằng
Python + PyGObject + gtk-layer-shell (dùng lại đúng thư viện waybar đã
tải sẵn — nhẹ hơn hẳn so với thêm cả 1 framework mới như eww/AGS/Astal).

CƠ CHẾ HIỆN/ẨN: đặt layer OVERLAY (trên cả waybar) — không cần gửi tín
hiệu tắt waybar thật, cứ đè lên là đủ, tránh rủi ro waybar không tự hiện
lại nếu có gì đó lỗi.

CƠ CHẾ ANIMATION: GtkLayerShell.set_margin() là thuộc tính Wayland, KHÔNG
phải CSS — CSS transition không áp dụng được. Phải tự tween bằng
GLib.timeout_add, đổi margin + opacity dần qua nhiều bước.

CƠ CHẾ TOGGLE: script này KHÔNG chạy nền thường trực — mỗi lần Super+M là
spawn mới hoàn toàn (giống cách wlogout hoạt động), dùng file PID trong
XDG_RUNTIME_DIR để biết đã có 1 phiên bản đang mở hay chưa. Nếu đang mở,
gửi SIGUSR1 để nó tự chạy animation đóng rồi thoát — không spawn thêm bản
thứ 2. Nhờ vậy RAM = 0 khi không dùng, chỉ tốn trong đúng lúc menu hiện.
"""
import os
import sys
import signal
import subprocess
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell  # noqa: E402

PIDFILE = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "hyprw-powermenu.pid")

SHOWN_MARGIN = 10
HIDDEN_MARGIN = -90
ANIM_STEPS = 16
ANIM_INTERVAL_MS = 14

# (tên css, icon Nerd Font, nhãn hover, lệnh chạy)
# Mã icon giống hệt wlogout/layout cũ — đã xác minh trước đó với
# github.com/ryanoasis/nerd-fonts + go-nf, không đổi lại từ đầu.
ACTIONS = [
    ("lock", "\uf023", "Khoá máy", ["hyprlock"]),
    ("logout", "\uf08b", "Đăng xuất", ["hyprctl", "dispatch", "exit"]),
    ("suspend", "\uf4ee", "Ngủ", ["systemctl", "suspend"]),
    ("reboot", "\uf021", "Khởi động lại", ["systemctl", "reboot"]),
    ("shutdown", "\uf011", "Tắt máy", ["systemctl", "poweroff"]),
]

CSS = b"""
window#power-menu { background-color: transparent; }
box.power-pill {
    background-color: rgba(30, 30, 46, 0.90);
    border-radius: 999px;
    padding: 6px 10px;
    border: 2px solid rgba(137, 180, 250, 0.35);
}
button {
    background: transparent;
    border: none;
    box-shadow: none;
    border-radius: 999px;
    padding: 8px 18px;
    transition: background-color 150ms ease;
}
button:hover { background-color: rgba(255, 255, 255, 0.10); }
label.pm-icon {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 20px;
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
    """Trả về PID nếu có 1 phiên bản đang thật sự sống, None nếu không."""
    if not os.path.exists(PIDFILE):
        return None
    try:
        with open(PIDFILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)  # 0 = chỉ kiểm tra tồn tại, không gửi tín hiệu thật
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        return None


def main():
    running_pid = already_running()
    if running_pid:
        # Đã có 1 bản đang mở -> báo nó tự đóng, KHÔNG mở thêm bản thứ 2
        os.kill(running_pid, signal.SIGUSR1)
        sys.exit(0)

    with open(PIDFILE, "w") as f:
        f.write(str(os.getpid()))

    def cleanup_pidfile():
        try:
            os.remove(PIDFILE)
        except FileNotFoundError:
            pass

    win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    win.set_name("power-menu")
    win.set_decorated(False)

    GtkLayerShell.init_for_window(win)
    GtkLayerShell.set_layer(win, GtkLayerShell.Layer.OVERLAY)
    GtkLayerShell.set_namespace(win, "hyprw-power-menu")
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, HIDDEN_MARGIN)
    GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.ON_DEMAND)

    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
    box.get_style_context().add_class("power-pill")

    state = {"dismissed": False}

    def dismiss(after_cmd=None):
        if state["dismissed"]:
            return
        state["dismissed"] = True
        animate(SHOWN_MARGIN, HIDDEN_MARGIN, on_done=lambda: finish(after_cmd))

    def finish(after_cmd):
        cleanup_pidfile()
        if after_cmd:
            subprocess.Popen(after_cmd)
        Gtk.main_quit()

    def animate(start, end, on_done=None):
        step = {"i": 0}

        def tick():
            step["i"] += 1
            t = step["i"] / ANIM_STEPS
            eased = 1 - (1 - t) ** 3  # ease-out cubic — mượt hơn tuyến tính thô
            margin = int(start + (end - start) * eased)
            GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, margin)
            opacity = eased if end == SHOWN_MARGIN else 1 - eased
            win.set_opacity(opacity)
            if step["i"] >= ANIM_STEPS:
                if on_done:
                    on_done()
                return False
            return True

        GLib.timeout_add(ANIM_INTERVAL_MS, tick)

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

    for name, icon, label, cmd in ACTIONS:
        box.pack_start(make_button(name, icon, label, cmd), False, False, 0)

    win.add(box)

    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    def on_key(_widget, event):
        if event.keyval == Gdk.KEY_Escape:
            dismiss()

    win.connect("key-press-event", on_key)
    win.connect("destroy", lambda *_a: (cleanup_pidfile(), Gtk.main_quit()))

    def on_sigusr1():
        dismiss()
        return GLib.SOURCE_CONTINUE  # an toàn nếu lỡ nhận tín hiệu 2 lần

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, on_sigusr1)

    win.set_opacity(0)
    win.show_all()
    # Đợi 1 nhịp cho window map xong rồi mới trượt xuống — trượt ngay lúc
    # chưa map xong dễ bị giật ở lần hiện đầu tiên
    GLib.timeout_add(20, lambda: (animate(HIDDEN_MARGIN, SHOWN_MARGIN), False)[1])

    Gtk.main()


if __name__ == "__main__":
    main()
