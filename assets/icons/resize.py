from PIL import Image

filenames = [
    'WerebearIcon',
]
for filename in filenames:
    # Load the 32x32 image
    icon = Image.open(f'assets\icons\{filename}.png')
    icon = icon.convert('RGBA')  # Ensure it's in RGBA format
    print(icon.size)

    # Get the pixel data from the image
    pixels = icon.load()

    # Create a new 64x64 blank image
    resized_icon = Image.new('RGBA', (64, 64))
    resized_pixels = resized_icon.load()

    # Loop through each pixel in the 32x32 image
    for x in range(32):
        for y in range(32):
            # Get the pixel from the original image
            pixel = pixels[x, y]

            # Set the corresponding 2x2 block in the new image
            resized_pixels[x*2, y*2] = pixel
            resized_pixels[x*2+1, y*2] = pixel
            resized_pixels[x*2, y*2+1] = pixel
            resized_pixels[x*2+1, y*2+1] = pixel

    # Save the resized image
    resized_icon.save(f'assets\icons\{filename}64.png')
