import flet as ft
from app.ui.components.chat_bubble import create_bubble

def main(page: ft.Page):
    try:
        b1 = create_bubble("Hello", True, is_file=False)
        b2 = create_bubble("File", False, is_file=True, on_file_click=lambda x: None)
        page.add(b1, b2)
        print("SUCCESS")
    except Exception as e:
        print(f"ERROR: {repr(e)}")
        import traceback
        traceback.print_exc()
        
ft.app(target=main)
