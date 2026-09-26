#!/usr/bin/env python3
"""
dock.py — Dock kiểu macOS, neo GIỮA - DƯỚI màn hình. Tự khởi động cùng
Hyprland (xem modules/Startup_Apps.lua) và CHẠY NỀN LIÊN TỤC — khác hẳn
power-menu.py/quick-settings.py (2 cái đó bật lên rồi THOÁT HẲN tiến
trình khi đóng). Dock phải sống xuyên suốt phiên làm việc để theo dõi
app nào đang mở liên tục qua Hyprland IPC (socket2, xem hàm
listen_hypr_events), không phải poll định kỳ.

BẬT/TẮT HIỂN THỊ lúc đang chạy: Super+D, hoặc gửi SIGUSR1 cho chính tiến
trình này — CHỈ ẩn/hiện (fade), KHÔNG thoát tiến trình, KHÔNG mất trạng
thái theo dõi app đang mở.

TẮT HẲN DOCK (không muốn dùng luôn): comment dòng gọi dock.py trong
Startup_Apps.lua rồi khởi động lại Hyprland — không cần sửa gì trong file
này. Dock chỉ là 1 dòng exec_cmd độc lập, không đụng gì tới phần còn lại
của dotfile nếu tắt.

SỬA DANH SÁCH APP GHIM: sửa mảng PINNED_APPS phía dưới. Mỗi app cần:
- "desktop": tên file .desktop (không có đuôi) trong /usr/share/applications
  hoặc ~/.local/share/applications — dùng để tra icon thật + tên hiển thị.
- "exec": lệnh chạy khi bấm mà app CHƯA mở.
- "class": window class thật để biết app ĐANG MỞ hay chưa (khớp cột CLASS
  trong `hyprctl clients -j` — mở app đó lên rồi chạy lệnh này để tra
  đúng chữ, không đoán).

VÌ SAO ẨN/HIỆN DÙNG FADE (KHÔNG TRƯỢT QUA MÉP MÀN HÌNH): đã cân nhắc kéo
cửa sổ trượt xuống dưới mép màn hình qua margin GtkLayerShell (animate
margin mỗi khung hình), nhưng bỏ vì 2 lý do: (1) đây là REAL Wayland
renegotiation mỗi frame, đúng cái mà power-menu.py/quick-settings.py cố
tránh triệt để; (2) opacity=0 thôi KHÔNG unmap cửa sổ — vùng đó vẫn nhận
click chuột dù mắt không thấy gì (bug thật, không phải lý thuyết suông).
Nên dùng: fade opacity xong mới win.hide() hẳn (unmap thật, hết nhận
input); lúc bật lại thì win.show() trước rồi mới fade opacity vào. Vừa
mượt vừa đúng.

Icon dùng ẢNH THẬT (Gtk.IconTheme + field Icon= trong .desktop) — CHỦ Ý
khác power-menu.py/quick-settings.py (toàn bộ dùng glyph Nerd Font chữ),
vì cả cái dock CHỈ để hiện icon app, dùng ảnh thật mới ra hồn "dock", còn
2 script kia mượn glyph chữ cho các nút hành động/trạng thái nhỏ.

GIỚI HẠN ĐÃ BIẾT:
- Hiệu ứng hover chỉ phóng to ĐÚNG icon đang trỏ vào — KHÔNG có hiệu ứng
  "gợn sóng" lan sang icon bên cạnh như macOS thật (fisheye) — phần đó
  phức tạp hơn nhiều (phải tính khoảng cách chuột tới TỪNG icon mỗi
  frame), cắt bớt cho gọn.
- App KHÔNG có file .desktop hoặc icon theme không có ảnh sẽ hiện icon
  chữ dự phòng (không phóng to lúc hover, vì icon chữ khó scale đẹp).
"""
import configparser
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, GtkLayerShell

PIDFILE = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "hyprw-dock.pid")

# ── Sửa ở đây để thêm/bớt app ghim (xem hướng dẫn tra "class" ở docstring
# đầu file) ──────────────────────────────────────────────────────────────
PINNED_APPS = [
    dict(name="Terminal", desktop="foot", exec="foot", class_="foot"),
    dict(name="Tệp tin", desktop="thunar", exec="thunar", class_="thunar"),
    dict(name="Firefox", desktop="firefox", exec="firefox", class_="firefox"),
]

ICON_REST_SIZE = 44
ICON_HOVER_SIZE = 58
HOVER_ANIM_MS = 120
TOGGLE_FADE_MS = 200
DOCK_BOTTOM_MARGIN = 10
ICON_FALLBACK = "\uf2d0"  # nf-fa-window-restore — dùng khi không tra được icon thật

CSS = b"""
window#dock { background-color: transparent; }
box.dock-card {
    background-color: rgba(30, 30, 46, 0.90);
    border: 2px solid rgba(137, 180, 250, 0.35);
    border-radius: 22px;
}
button.dock-icon-btn {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 4px 6px;
    border-radius: 14px;
}
button.dock-icon-btn:hover { background-color: rgba(255, 255, 255, 0.10); }
label.dock-fallback {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 26px;
    color: #cdd6f4;
}
label.dock-dot {
    font-family: "JetBrainsMono Nerd Font";
    font-size: 6px;
    color: #89b4fa;
}
"""


def already_running():
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


def find_desktop_file(desktop_id):
    for d in (
        os.path.expanduser("~/.local/share/applications"),
        "/usr/local/share/applications",
        "/usr/share/applications",
    ):
        p = os.path.join(d, desktop_id + ".desktop")
        if os.path.isfile(p):
            return p
    return None


def load_app_pixbuf(desktop_id, size):
    """Đọc Icon= trong .desktop rồi nhờ Gtk.IconTheme tra ảnh thật theo
    icon theme đang dùng — cách CHUẨN mọi dock/launcher Linux làm, không
    tự vẽ icon. Trả None nếu không tra được (nơi gọi tự dùng chữ dự
    phòng)."""
    icon_name = desktop_id
    try:
        path = find_desktop_file(desktop_id)
        if path:
            cp = configparser.ConfigParser(interpolation=None)
            cp.read(path, encoding="utf-8")
            icon_name = cp.get("Desktop Entry", "Icon", fallback=desktop_id)
    except Exception:
        pass
    try:
        if os.path.isabs(icon_name) and os.path.isfile(icon_name):
            return GdkPixbuf.Pixbuf.new_from_file_at_size(icon_name, size, size)
        theme = Gtk.IconTheme.get_default()
        info = theme.lookup_icon(icon_name, size, Gtk.IconLookupFlags.FORCE_SIZE)
        if info:
            return info.load_icon()
    except Exception:
        pass
    return None


def get_running_classes():
    """{class chữ thường} — tập hợp class của mọi cửa sổ đang mở."""
    try:
        out = subprocess.run(
            ["hyprctl", "clients", "-j"], capture_output=True, text=True, timeout=3
        ).stdout
        clients = json.loads(out)
    except Exception:
        return set()
    return {(c.get("class") or "").lower() for c in clients}


def focus_or_launch(app):
    running = get_running_classes()
    if app["class_"].lower() in running:
        subprocess.run(
            ["hyprctl", "dispatch", "focuswindow", "class:%s" % app["class_"]],
            capture_output=True,
        )
    else:
        subprocess.Popen(
            ["sh", "-c", app["exec"]],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def get_hypr_socket2_path():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    return os.path.join(runtime_dir, "hypr", sig, ".socket2.sock")


def listen_hypr_events(on_change):
    """Chạy trong thread nền — đọc socket2 (IPC event thật của Hyprland,
    format `EVENT>>DATA\\n`, xem wiki.hypr.land/IPC) để biết NGAY LẬP TỨC
    lúc nào có cửa sổ mở/đóng, thay vì poll định kỳ (vừa tốn, vừa trễ vài
    trăm ms). Tự kết nối lại nếu mất kết nối (Hyprland restart?)."""
    path = get_hypr_socket2_path()
    while True:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(path)
            buf = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    text = line.decode("utf-8", "ignore")
                    if text.startswith("openwindow>>") or text.startswith("closewindow>>"):
                        GLib.idle_add(on_change)
        except Exception:
            pass
        time.sleep(2)


class Dock:
    def __init__(self):
        self.visible = True

        self.win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.win.set_name("dock")
        self.win.set_decorated(False)

        GtkLayerShell.init_for_window(self.win)
        GtkLayerShell.set_layer(self.win, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_namespace(self.win, "hyprw-dock")
        # CHỈ neo BOTTOM (không neo LEFT/RIGHT) -> gtk-layer-shell tự canh
        # giữa theo chiều ngang, đúng "giữa - dưới màn hình" cần, khỏi
        # phải tự tính bề rộng màn hình/dock như 2 script kia.
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.BOTTOM, DOCK_BOTTOM_MARGIN)
        GtkLayerShell.set_keyboard_mode(self.win, GtkLayerShell.KeyboardMode.NONE)
        # Không giữ chỗ riêng -> cửa sổ khác tile full màn hình bình
        # thường, dock chỉ nổi đè lên trên chứ không chiếm không gian tile.
        GtkLayerShell.set_exclusive_zone(self.win, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        card.get_style_context().add_class("dock-card")
        card.set_margin_top(8)
        card.set_margin_bottom(8)
        card.set_margin_start(12)
        card.set_margin_end(12)
        self.win.add(card)

        self.rows = []
        for app in PINNED_APPS:
            btn, img, dot, pixbuf = self._make_icon(app)
            card.pack_start(btn, False, False, 0)
            self.rows.append(dict(app=app, img=img, dot=dot, pixbuf=pixbuf, hover_size=ICON_REST_SIZE))

        self.win.show_all()
        self._refresh_running()

        threading.Thread(
            target=listen_hypr_events,
            args=(lambda: (self._refresh_running(), GLib.SOURCE_REMOVE)[1],),
            daemon=True,
        ).start()

    def _make_icon(self, app):
        pixbuf = load_app_pixbuf(app["desktop"], ICON_HOVER_SIZE)

        img = Gtk.Image()
        if pixbuf:
            img.set_from_pixbuf(pixbuf.scale_simple(ICON_REST_SIZE, ICON_REST_SIZE, GdkPixbuf.InterpType.BILINEAR))
        else:
            img.set_from_pixbuf(None)
            fallback = Gtk.Label(label=ICON_FALLBACK)
            fallback.get_style_context().add_class("dock-fallback")

        dot = Gtk.Label(label="\u25cf")
        dot.get_style_context().add_class("dock-dot")
        dot.set_opacity(0)

        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        col.set_halign(Gtk.Align.CENTER)
        if pixbuf:
            col.pack_start(img, False, False, 0)
        else:
            col.pack_start(fallback, False, False, 0)
        col.pack_start(dot, False, False, 0)

        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.get_style_context().add_class("dock-icon-btn")
        btn.set_tooltip_text(app["name"])
        btn.add(col)
        btn.connect("clicked", lambda _b, a=app: focus_or_launch(a))
        if pixbuf:
            btn.connect("enter-notify-event", lambda w, e, a=app: self._on_hover(a, True))
            btn.connect("leave-notify-event", lambda w, e, a=app: self._on_hover(a, False))
        return btn, img, dot, pixbuf

    def _row_for(self, app):
        for r in self.rows:
            if r["app"] is app:
                return r
        return None

    def _on_hover(self, app, entering):
        row = self._row_for(app)
        if row is None or row["pixbuf"] is None:
            return False
        target = ICON_HOVER_SIZE if entering else ICON_REST_SIZE
        start = row["hover_size"]
        state = {"start_us": None}

        def tick(_widget, frame_clock):
            now_us = frame_clock.get_frame_time()
            if state["start_us"] is None:
                state["start_us"] = now_us
            t = min(1.0, (now_us - state["start_us"]) / 1000 / HOVER_ANIM_MS)
            size = max(1, int(lerp(start, target, ease_out_cubic(t))))
            row["hover_size"] = size
            scaled = row["pixbuf"].scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
            row["img"].set_from_pixbuf(scaled)
            if t >= 1.0:
                return GLib.SOURCE_REMOVE
            return GLib.SOURCE_CONTINUE

        row["img"].add_tick_callback(tick)
        return False

    def _refresh_running(self):
        running = get_running_classes()
        for row in self.rows:
            is_running = row["app"]["class_"].lower() in running
            row["dot"].set_opacity(1 if is_running else 0)

    # ---- bật/tắt hiển thị (KHÔNG thoát tiến trình) ----
    def toggle(self):
        if self.visible:
            self.visible = False

            def tick_hide(t):
                self.win.set_opacity(1 - t)

            def done_hide():
                self.win.hide()  # unmap thật -> hết nhận input, không chỉ vô hình

            self._animate_opacity(tick_hide, done_hide)
        else:
            self.visible = True
            self.win.set_opacity(0)
            self.win.show()

            def tick_show(t):
                self.win.set_opacity(t)

            self._animate_opacity(tick_show, None)

    def _animate_opacity(self, set_fn, on_done):
        state = {"start_us": None}

        def tick(_widget, frame_clock):
            now_us = frame_clock.get_frame_time()
            if state["start_us"] is None:
                state["start_us"] = now_us
            t = min(1.0, (now_us - state["start_us"]) / 1000 / TOGGLE_FADE_MS)
            set_fn(ease_out_cubic(t))
            if t >= 1.0:
                if on_done:
                    on_done()
                return GLib.SOURCE_REMOVE
            return GLib.SOURCE_CONTINUE

        self.win.add_tick_callback(tick)


def main():
    running_pid = already_running()
    if running_pid:
        # Đã có 1 tiến trình dock chạy nền -> gửi SIGUSR1 để BẬT/TẮT HIỂN
        # THỊ của tiến trình đó, KHÔNG spawn thêm tiến trình thứ 2 (khác
        # hẳn power-menu.py/quick-settings.py — dock phải sống liên tục).
        os.kill(running_pid, signal.SIGUSR1)
        sys.exit(0)

    with open(PIDFILE, "w") as f:
        f.write(str(os.getpid()))

    style_provider = Gtk.CssProvider()
    style_provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    dock = Dock()

    def on_sigusr1():
        dock.toggle()
        return GLib.SOURCE_CONTINUE

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, on_sigusr1)

    try:
        Gtk.main()
    finally:
        cleanup_pidfile()


if __name__ == "__main__":
    main()
