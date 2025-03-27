import keyboard
import time

def test_keyboard_special_characters(test_string="!@#$%^&*()_+=-`~[]{};':\",./<>?"):
    """
    Tests if the keyboard library can correctly write special characters
    to the currently active window.

    Args:
        test_string: The string of special characters to test.
    """

    print("Starting keyboard special character test...")
    print(f"Test string: {test_string}")
    print("Please make sure a text editor or a suitable input field is focused.")
    print("The test will start in 5 seconds...")
    time.sleep(5)

    try:
        keyboard.write(test_string)
        print("Test string written successfully.")
        print("Please check the focused window to verify that all characters were typed correctly.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure you have the necessary permissions (e.g., root/administrator).")

if __name__ == "__main__":
    test_keyboard_special_characters()