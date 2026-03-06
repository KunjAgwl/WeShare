import flet as ft
import os
import asyncio
import threading
import logging
from datetime import datetime
from app.ui.components.colors import (
    BG_DEEP, BG_SIDEBAR, BG_HEADER, BG_INPUT,
    GREEN_ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, DIVIDER_COLOR,
)
from app.ui.components.avatar import create_avatar
from app.ui.components.chat_bubble import create_bubble
from app.ui.components.chat_tile import create_chat_tile
from app.discovery.discovery import DeviceDiscovery
from app.connection.server import LocalFileServer
from app.connection.client import LocalClient

logger = logging.getLogger(__name__)


def chat_page(page: ft.Page, db, username: str, display_name: str,
              loop, on_open_profile):
    """Main chat view with sidebar, message area, add‑contact dialog."""

    discovered = {}       # name → {ip,port} | {type:"cloud"}
    active_chat = [None]
    messages = {}         # contact → [{text, is_me, is_file, time}]
    file_server = LocalFileServer(port=5001)
    file_client = LocalClient()

    def _now():
        return datetime.now().strftime("%H:%M")

    # ── UI refs ──
    chat_list_col = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)
    message_col   = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=2)
    header_avatar = create_avatar("?", 40)
    header_name   = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    header_status = ft.Text("", size=12, color=TEXT_SECONDARY)

    msg_input = ft.TextField(
        hint_text="Type a message",
        hint_style=ft.TextStyle(color=TEXT_SECONDARY),
        expand=True, border=ft.InputBorder.NONE,
        bgcolor=BG_INPUT, color=TEXT_PRIMARY, border_radius=8,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=10),
        on_submit=lambda e: _send_click(e),
    )

    # ── Add Contact dialog ──
    add_field = ft.TextField(hint_text="Enter username…", expand=True,
                              border_color=TEXT_SECONDARY, color=TEXT_PRIMARY)
    add_error = ft.Text("", color="#F15C6D", size=12)

    async def _do_add_contact():
        target = add_field.value.strip()
        if not target:
            return
        ok = await db.add_contact(username, target)
        if ok:
            add_dialog.open = False
            add_error.value = ""
            await _refresh_contacts()
            page.update()
        else:
            add_error.value = "User not found"
            page.update()

    add_dialog = ft.AlertDialog(
        title=ft.Text("Add Contact"),
        content=ft.Column([add_field, add_error], tight=True, spacing=6),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: _close_add()),
            ft.TextButton("Add", on_click=lambda e: asyncio.run_coroutine_threadsafe(_do_add_contact(), loop)),
        ],
    )

    def _close_add():
        add_dialog.open = False
        page.update()

    def _open_add(e):
        add_field.value = ""
        add_error.value = ""
        add_dialog.open = True
        page.overlay.append(add_dialog)
        page.update()

    # ── File send dialog ──
    file_field = ft.TextField(hint_text="Paste file path…", expand=True,
                               border_color=TEXT_SECONDARY, color=TEXT_PRIMARY)

    def _send_file(e):
        fpath = file_field.value.strip()
        file_dlg.open = False
        page.update()
        if not fpath or not active_chat[0]:
            return
        
        target = active_chat[0]
        fname = os.path.basename(fpath)
        info = discovered.get(target, {})
        
        # Instantly update local UI
        messages.setdefault(target, []).append({
            "text": f"📎 {fname}", 
            "is_me": True, 
            "is_file": True, 
            "time": _now()
        })
        _refresh_msg_view(scroll=True)
        
        # If on LAN, send via local P2P HTTP server
        if "ip" in info:
            def xfer():
                if file_client.send_file(info["ip"], 5001, fpath):
                    # Record the file transfer in the DB to sync it
                    asyncio.run_coroutine_threadsafe(
                        db.send_message(username, target, f"📎 {fname}", is_file=True), loop)
            threading.Thread(target=xfer, daemon=True).start()
        else:
            # If not on LAN, currently we just record a placeholder in DB
            asyncio.run_coroutine_threadsafe(
                db.send_message(username, target, f"📎 {fname}", is_file=True), loop)

    file_dlg = ft.AlertDialog(
        title=ft.Text("Send a file"),
        content=file_field,
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: _close_file()),
            ft.TextButton("Send", on_click=_send_file),
        ],
    )

    def _close_file():
        file_dlg.open = False
        page.update()

    def _open_file(e):
        if not active_chat[0]:
            return
        file_field.value = ""
        file_dlg.open = True
        page.overlay.append(file_dlg)
        page.update()

    # ── Refresh helpers ──
    def _refresh_chat_list():
        chat_list_col.controls.clear()
        for name, info in discovered.items():
            is_local = "ip" in info
            chat_list_col.controls.append(
                create_chat_tile(name, is_local, active_chat[0] == name,
                                 lambda e, n=name: _select_chat(n))
            )
        page.update()

    def _handle_file_click(text):
        # text is like "📎 filename.ext"
        fname = text.replace("📎 ", "")
        import os
        import platform
        import subprocess

        # Priority 1: Check if File exists in uploads dir (if received)
        path = os.path.join(os.getcwd(), "uploads", fname)
        # Priority 2: In case it's a file sent by me, the text might be the name.
        # But we only track name in DB, so we can't reliably open sent files if they moved,
        # but received files will be in uploads/.
        
        if not os.path.exists(path):
            page.snack_bar = ft.SnackBar(ft.Text(f"File not found locally: {fname}"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception as e:
            logger.error(f"Failed to open file: {e}")

    def _refresh_msg_view(scroll=False):
        message_col.controls.clear()
        t = active_chat[0]
        if t and t in messages:
            for m in messages[t]:
                message_col.controls.append(
                    create_bubble(m["text"], m.get("is_me", False),
                                  m.get("is_file", False), m.get("time", ""),
                                  on_file_click=_handle_file_click))
        page.update()
        if scroll and message_col.controls:
            message_col.scroll_to(offset=-1, duration=100)

    def _select_chat(name):
        active_chat[0] = name
        header_avatar.content = ft.Text(name[0].upper(), size=18,
                                         weight=ft.FontWeight.BOLD, color="white")
        header_name.value = name
        info = discovered.get(name, {})
        header_status.value = "LAN · Online" if "ip" in info else "Cloud"
        _refresh_msg_view()
        _refresh_chat_list()
        chat_area_holder.content = chat_area
        page.update()

    def _send_click(e):
        t = active_chat[0]
        text = msg_input.value.strip()
        if not t or not text:
            return
        # Instantly update local UI
        messages.setdefault(t, []).append({
            "text": text, 
            "is_me": True, 
            "is_file": False, 
            "time": _now()
        })
        _refresh_msg_view(scroll=True)
        
        # Clear input on UI thread
        msg_input.value = ""
        msg_input.focus()
        page.update()

        async def _do_send():
            try:
                await db.send_message(username, t, text)
            except Exception as ex:
                logger.error(f"Send Error: {ex}")
                
        # Run DB save in background without blocking UI
        asyncio.run_coroutine_threadsafe(_do_send(), loop)

    async def _refresh_contacts():
        rows = await db.get_contacts(username)
        for row in rows:
            cname = row[0]
            if cname not in discovered:
                discovered[cname] = {"type": "cloud"}
        _refresh_chat_list()

    # ── Background sync ──
    async def _sync():
        while True:
            try:
                await db.update_last_seen(username)
                await _refresh_contacts()
                t = active_chat[0]
                if t:
                    rows = await db.get_messages(username, t)
                    new = [{"text": r[1], "is_me": r[0] == username,
                            "is_file": bool(r[2]),
                            "time": str(r[3])[-8:-3] if r[3] else ""} for r in rows]
                    
                    old_len = len(messages.get(t) or [])
                    if messages.get(t) != new:
                        messages[t] = new
                        _refresh_msg_view(scroll=(len(new) > old_len))
            except Exception as ex:
                logger.error(f"Sync: {ex}")
            await asyncio.sleep(0.5)

    # ── Discovery ──
    def on_found(name, ip, port):
        discovered[name] = {"ip": ip, "port": port}
        _refresh_chat_list()

    def on_lost(name):
        if name in discovered and "ip" in discovered[name]:
            discovered[name] = {"type": "cloud"}
            _refresh_chat_list()

    # ══════════════════════════════════
    #  LAYOUT
    # ══════════════════════════════════

    empty_state = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CHAT_ROUNDED, size=48, color=TEXT_SECONDARY),
            ft.Text("Select a chat or add a contact", size=16, color=TEXT_SECONDARY),
        ], alignment=ft.MainAxisAlignment.CENTER,
           horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
        expand=True, alignment=ft.Alignment(0, 0), bgcolor=BG_DEEP,
    )

    sidebar_header = ft.Container(
        content=ft.Row([
            ft.Container(
                content=create_avatar(display_name, 36),
                on_click=lambda _: on_open_profile(),
                ink=True,
            ),
            ft.Text("Chats", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, expand=True),
            ft.IconButton(ft.Icons.PERSON_ADD_ALT_1, icon_color=TEXT_SECONDARY, icon_size=20,
                          on_click=_open_add, tooltip="Add Contact"),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        bgcolor=BG_HEADER,
    )

    sidebar = ft.Container(
        content=ft.Column([sidebar_header, chat_list_col], spacing=0),
        width=340, bgcolor=BG_SIDEBAR,
        border=ft.Border(right=ft.BorderSide(1, DIVIDER_COLOR)),
    )

    chat_top = ft.Container(
        content=ft.Row([
            header_avatar,
            ft.Column([header_name, header_status], spacing=1, expand=True),
            ft.IconButton(ft.Icons.MORE_VERT, icon_color=TEXT_SECONDARY, icon_size=20),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(horizontal=16, vertical=8), bgcolor=BG_HEADER,
    )

    input_bar = ft.Container(
        content=ft.Row([
            ft.IconButton(ft.Icons.ATTACH_FILE, icon_color=TEXT_SECONDARY, icon_size=22,
                          on_click=_open_file),
            msg_input,
            ft.Container(
                content=ft.IconButton(ft.Icons.SEND_ROUNDED, icon_color="white", icon_size=20,
                                      on_click=_send_click),
                width=42, height=42, border_radius=21, bgcolor=GREEN_ACCENT,
                alignment=ft.Alignment(0, 0),
            ),
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(horizontal=10, vertical=6), bgcolor=BG_HEADER,
    )

    msg_container = ft.Container(content=message_col, expand=True, bgcolor=BG_DEEP,
                                  padding=ft.Padding.symmetric(horizontal=60, vertical=12))

    chat_area = ft.Column([chat_top, msg_container, input_bar], spacing=0, expand=True)
    chat_area_holder = ft.Container(content=empty_state, expand=True)

    layout = ft.Row([sidebar, chat_area_holder], spacing=0, expand=True)

    # ── Start services ──
    def _start_services():
        asyncio.run_coroutine_threadsafe(_sync(), loop)
        file_server.start()
        disc = DeviceDiscovery(device_name=username, port=5000,
                               on_device_found=on_found, on_device_lost=on_lost)
        threading.Thread(target=disc.start, daemon=True).start()

    threading.Thread(target=_start_services, daemon=True).start()

    def build():
        return layout

    return build
