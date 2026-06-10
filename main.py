from brain.src.extractors.image import extract_text_from_image

image_path = "brain/uploads/test.png"

text = extract_text_from_image(image_path)

print("\n===== EXTRACTED TEXT =====\n")
print(text)