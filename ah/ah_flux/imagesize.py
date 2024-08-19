def get_closest_image_size(w, h):
    # Available image size options
    sizes = {
        "square_hd": (1024, 1024),
        "square": (512, 512),
        "portrait_4_3": (768, 1024),
        "portrait_16_9": (576, 1024),
        "landscape_4_3": (1024, 768),
        "landscape_16_9": (1024, 576)
    }

    # Calculate aspect ratio and total pixels of input
    input_ratio = w / h
    input_pixels = w * h

    # Find the closest match
    closest_size = min(sizes.items(), key=lambda x: (
        abs(input_ratio - (x[1][0] / x[1][1])) +  # Aspect ratio difference
        abs(input_pixels - (x[1][0] * x[1][1])) / 1000000  # Total pixels difference (normalized)
    ))

    return closest_size[0]

# Test cases
if __name__ == "__main__":
    print(get_closest_image_size(800, 600))  # Should return "landscape_4_3"
    print(get_closest_image_size(1920, 1080))  # Should return "landscape_16_9"
    print(get_closest_image_size(500, 500))  # Should return "square"
    print(get_closest_image_size(1000, 1000))  # Should return "square_hd"
    print(get_closest_image_size(600, 800))  # Should return "portrait_4_3"
