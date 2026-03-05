import flet as ft
import asyncio
from app.ui.components.colors import (
    BG_DEEP, BG_HEADER, BG_INPUT,
    GREEN_ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, ERROR_COLOR,
)


def login_page(page: ft.Page, db, on_login_success):
    """Login / Register screen with WeShare styling."""

    error_text = ft.Text("", color=ERROR_COLOR, size=13)
    mode = [0]  # 0 = login, 1 = register

    # ── Fields ──
    username_field = ft.TextField(label="Username", border_color=TEXT_SECONDARY,
                                  color=TEXT_PRIMARY, label_style=ft.TextStyle(color=TEXT_SECONDARY),
                                  width=300)
    password_field = ft.TextField(label="Password", password=True, can_reveal_password=True,
                                  border_color=TEXT_SECONDARY, color=TEXT_PRIMARY,
                                  label_style=ft.TextStyle(color=TEXT_SECONDARY), width=300)
    display_field = ft.TextField(label="Display Name", border_color=TEXT_SECONDARY,
                                 color=TEXT_PRIMARY, label_style=ft.TextStyle(color=TEXT_SECONDARY),
                                 width=300, visible=False)

    action_btn = ft.ElevatedButton("Login", bgcolor=GREEN_ACCENT, color="white", width=300)
    toggle_text = ft.TextButton("Don't have an account? Register",
                                 on_click=lambda e: _toggle())

    form_col = ft.Column(spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _toggle():
        mode[0] = 1 - mode[0]
        if mode[0] == 1:
            display_field.visible = True
            action_btn.text = "Create Account"
            toggle_text.text = "Already have an account? Login"
        else:
            display_field.visible = False
            action_btn.text = "Login"
            toggle_text.text = "Don't have an account? Register"
        error_text.value = ""
        page.update()

    async def _do_action():
        u = username_field.value.strip()
        p = password_field.value.strip()
        if not u or not p:
            error_text.value = "Please fill in all fields"
            page.update()
            return

        if mode[0] == 0:  # Login
            result = await db.login_user(u, p)
            if result:
                on_login_success(result[0], result[1])
            else:
                error_text.value = "Invalid username or password"
                page.update()
        else:  # Register
            d = display_field.value.strip()
            if not d:
                error_text.value = "Please enter a display name"
                page.update()
                return
            ok = await db.register_user(u, p, d)
            if ok:
                on_login_success(u, d)
            else:
                error_text.value = "Username already taken"
                page.update()

    def _handle_action(e, loop):
        asyncio.run_coroutine_threadsafe(_do_action(), loop)

    def build(loop):
        action_btn.on_click = lambda e: _handle_action(e, loop)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=60),
                    ft.Icon(ft.Icons.CHAT_ROUNDED, size=64, color=GREEN_ACCENT),
                    ft.Text("WeShare", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text("Sign in to start messaging", size=14, color=TEXT_SECONDARY),
                    ft.Container(height=30),
                    ft.Container(
                        content=ft.Column([
                            username_field,
                            display_field,
                            password_field,
                            ft.Container(height=4),
                            action_btn,
                            error_text,
                            toggle_text,
                        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=380,
                        padding=30,
                        border_radius=16,
                        bgcolor=BG_HEADER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.START,
                spacing=8,
            ),
            expand=True,
            bgcolor=BG_DEEP,
            alignment=ft.Alignment(0, 0),
        )

    return build
