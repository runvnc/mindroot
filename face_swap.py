from facefusionlib import swapper
from facefusionlib.swapper import DeviceProvider

def face_swap(input_image_path, target_image_path, skip_nsfw=False): 
    result = swapper.swap_face(
            source_paths=[input_image_path],
            target_path=target_image_path,
            provider=DeviceProvider.GPU,
            detector_score=0.65,
            mask_blur=0.7,
            skip_nsfw=skip_nsfw,
            landmarker_score=0.5
        )

    print(result)

if __name__ == "__main__":
    face_swap("imgs/input.png", "imgs/target.png", skip_nsfw=True)

