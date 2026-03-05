import flet as ft
import asyncio
import threading
import logging
from app.config.database import Database
from app.ui.components.colors import BG_DEEP
from app.ui.pages.login_page import login_page
from app.ui.pages.chat_page import chat_page
from app.ui.pages.profile_page import profile_page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(page: ft.Page):
    page.title = "WeShare"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_DEEP
    page.padding = 0
    page.spacing = 0
    page.window.width = 1100
    page.window.height = 750

    db = Database()

    # Shared asyncio loop for all DB operations
    loop = asyncio.new_event_loop()

    def _run_loop(lp):
        asyncio.set_event_loop(lp)
        try:
            lp.run_until_complete(db.init_db())
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"DB init failed (will retry on first action): {e}")
        lp.run_forever()                    # keep loop alive for futures

    threading.Thread(target=_run_loop, args=(loop,), daemon=True).start()

    # ── State ──
    current_user = [None]     # (username, display_name)

    # ── Page switcher ──
    def _show(control):
        page.controls.clear()
        page.controls.append(control)
        page.update()

    def _on_login_success(username, display_name):
        current_user[0] = (username, display_name)
        _show_chat()

    def _show_chat():
        u, d = current_user[0]
        builder = chat_page(page, db, u, d, loop, on_open_profile=_show_profile)
        _show(builder())

    def _show_profile():
        u, d = current_user[0]
        builder = profile_page(page, db, u, d, loop, on_back=_show_chat)
        _show(builder())

    # ── Start at login ──
    login_builder = login_page(page, db, _on_login_success)
    _show(login_builder(loop))


ft.app(target=main)