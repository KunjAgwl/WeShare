import flet as ft
from app.ui.components.colors import (
    BG_SENT, BG_RECEIVED, TEXT_PRIMARY, TEXT_SECONDARY, GREEN_ACCENT,
)


def create_bubble(text: str, is_me: bool, is_file: bool = False,
                  time_str: str = "", max_width: float = 450):
    """WeShare-style chat bubble with tail on the sender's side."""
    bg = BG_SENT if is_me else BG_RECEIVED
    align = ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START
    radius = ft.border_radius.only(
        top_left=12, top_right=12,
        bottom_left=12 if is_me else 0,
        bottom_right=0 if is_me else 12,
    )

    widgets = []
    if is_file:
        widgets.append(ft.Row([
            ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color=GREEN_ACCENT, size=20),
            ft.Text(text, color=TEXT_PRIMARY, size=14, italic=True, expand=True),
        ], spacing=8))
    else:
        widgets.append(ft.Text(text, color=TEXT_PRIMARY, size=14))

    widgets.append(
        ft.Row([ft.Text(time_str, size=10, color=TEXT_SECONDARY)],
               alignment=ft.MainAxisAlignment.END)
    )

    return ft.Row(
        [ft.Container(
            content=ft.Column(widgets, spacing=4, tight=True),
            padding=ft.Padding.only(left=10, right=10, top=8, bottom=6),
            bgcolor=bg,
            border_radius=radius,
            width=max_width,
        )],
        alignment=align,
    )
