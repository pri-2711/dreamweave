from brain.src.extractors.image import extract_text_from_image


def image_ocr_menu():
    image_path = input("\nEnter image path: ").strip()

    try:
        text = extract_text_from_image(image_path)

        print("\n===== EXTRACTED TEXT =====\n")
        print(text)

    except Exception as e:
        print(f"\nError: {e}")


def main():
    while True:

        print("\n===== DREAMWEAVE BRAIN =====")
        print("1. Extract text from image")
        print("2. Exit")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            image_ocr_menu()

        elif choice == "2":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid choice.")


if __name__ == "__main__":
    main()