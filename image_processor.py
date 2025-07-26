from PIL import Image

def process_image(image_path):
    img = Image.open(image_path)
    img = img.resize((500, 500))    # Force square size
    img.save(image_path)
