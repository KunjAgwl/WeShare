import flet as ft
import os
import io
import base64
import qrcode
from app.ui.components.avatar import create_avatar
from app.ui.components.colors import (
    BG_DEEP, BG_HEADER, GREEN_ACCENT, TEXT_PRIMARY, TEXT_SECONDARY,
)


def profile_page(page: ft.Page, db, username: str, display_name: str,
                 loop, on_back):
    """User profile page with QR code and edit display name."""

    # ── QR code generation ──
    def _generate_qr_base64(data: str) -> str:
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#00A884", back_color="#111B21")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    qr_b64 = _generate_qr_base64(username)

    name_field = ft.TextField(
        value=display_name, label="Display Name",
        border_color=TEXT_SECONDARY, color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY), width=300,
    )
    status_text = ft.Text("", color=GREEN_ACCENT, size=13)

    import asyncio

    async def _save_name():
        new_name = name_field.value.strip()
        if new_name:
            await db.update_display_name(username, new_name)
            status_text.value = "Display name updated!"
            page.update()

    def save_click(e):
        asyncio.run_coroutine_threadsafe(_save_name(), loop)

    def build():
        return ft.Container(
            content=ft.Column(
                [
                    # Top bar
                    ft.Container(
                        content=ft.Row([
                            ft.IconButton(ft.Icons.ARROW_BACK, icon_color=TEXT_PRIMARY,
                                          on_click=lambda _: on_back()),
                            ft.Text("Profile", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ], spacing=8),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                        bgcolor=BG_HEADER,
                    ),
                    # Content
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Container(height=20),
                                create_avatar(display_name, 100),
                                ft.Container(height=12),
                                ft.Text(display_name, size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ft.Text(f"@{username}", size=14, color=TEXT_SECONDARY),
                                ft.Container(height=24),
                                # QR Code
                                ft.Text("Your QR Code", size=16, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                                ft.Text("Others can scan this to add you", size=12, color=TEXT_SECONDARY),
                                ft.Container(height=8),
                                ft.Container(
                                    content=ft.Image(src_base64=qr_b64, width=180, height=180),
                                    padding=16,
                                    border_radius=12,
                                    bgcolor=BG_HEADER,
                                ),
                                ft.Container(height=24),
                                # Edit name
                                ft.Text("Edit Display Name", size=16, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                                name_field,
                                ft.ElevatedButton("Save", bgcolor=GREEN_ACCENT, color="white",
                                                  width=300, on_click=save_click),
                                status_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        expand=True,
                        padding=ft.Padding.symmetric(horizontal=40, vertical=10),
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            bgcolor=BG_DEEP,
        )

    return build
