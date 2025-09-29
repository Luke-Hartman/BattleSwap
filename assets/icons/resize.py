from PIL import Image

filenames = [
    'ExplodeOnDeathIcon',
    'ExtraHealthIcon',
    'UpgradeArmorIcon',
    'DamageAuraIcon',
    'MeteorShowerIcon',
    'ExtraMovementSpeedIcon',
    'HealOnKillIcon',
    'InfectOnHitIcon',
    'HunterIcon'
]
original_size = 16
for filename in filenames:
    # Load the 32x32 image
    icon = Image.open(f'assets/icons/{filename}.png')
    icon = icon.convert('RGBA')  # Ensure it's in RGBA format
    print(icon.size)
    if icon.size != (original_size, original_size):
        print(f'{filename} is not {original_size}x{original_size}')
        continue

    # Get the pixel data from the image
    pixels = icon.load()

    # Create a new 64x64 blank image
    resized_icon = Image.new('RGBA', (64, 64))
    resized_pixels = resized_icon.load()

    # Loop through each pixel in the 32x32 image
    for x in range(original_size):
        for y in range(original_size):
            # Get the pixel from the original image
            pixel = pixels[x, y]

            n = 64 // original_size
            # Set the corresponding nxn block in the new image
            for i in range(n):
                for j in range(n):
                    resized_pixels[x*n+i, y*n+j] = pixel

    # Save the resized image
    resized_icon.save(f'assets/icons/{filename}.png')
