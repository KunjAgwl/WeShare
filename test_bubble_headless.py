from app.ui.components.chat_bubble import create_bubble

def test():
    try:
        b = create_bubble("File", False, is_file=True, on_file_click=lambda x: None)
        print(f"Success! {b}")
    except Exception as e:
        print(f"ERROR: {e}")

test()
