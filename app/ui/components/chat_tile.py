import flet as ft
from app.ui.components.avatar import create_avatar
from app.ui.components.colors import (
    TEXT_PRIMARY, TEXT_SECONDARY, GREEN_ACCENT, BG_HOVER, DIVIDER_COLOR,
)


def create_chat_tile(name: str, is_local: bool, is_selected: bool, on_click):
    """Sidebar contact tile with avatar, status badge, and click handler."""
    status_text = "LAN · Online" if is_local else "Cloud"
    status_color = GREEN_ACCENT if is_local else TEXT_SECONDARY

    return ft.Container(
        content=ft.Row(
            [
                create_avatar(name, 48),
                ft.Column(
                    [
                        ft.Text(name, size=16, color=TEXT_PRIMARY, weight=ft.FontWeight.W_500),
                        ft.Text(status_text, size=12, color=status_color),
                    ],
                    spacing=2, expand=True,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        bgcolor=BG_HOVER if is_selected else "transparent",
        on_click=on_click,
        border=ft.Border(bottom=ft.BorderSide(1, DIVIDER_COLOR)),
        ink=True,
    )
