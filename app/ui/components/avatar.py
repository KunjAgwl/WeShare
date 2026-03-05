import flet as ft
from app.ui.components.colors import GREEN_ACCENT


def create_avatar(name: str, size: int = 40):
    """Circular letter avatar with WeShare-green background."""
    letter = name[0].upper() if name else "?"
    return ft.Container(
        content=ft.Text(letter, size=size * 0.45, weight=ft.FontWeight.BOLD, color="white"),
        width=size,
        height=size,
        border_radius=size / 2,
        bgcolor=GREEN_ACCENT,
        alignment=ft.Alignment(0, 0),
    )
