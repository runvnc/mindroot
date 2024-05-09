from facefusionlib import swapper
from facefusionlib.swapper import DeviceProvider
from os import listdir

def face_swap(input_ref_dir, target_image_path, skip_nsfw=False): 
    input_image_paths = [f for f in listdir(input_ref_dir) if isfile(join (input_image_path, f))]

    result = swapper.swap_face(
            source_paths=input_image_paths,
            target_path=target_image_path,
            provider=DeviceProvider.GPU,
            detector_score=0.65,
            mask_blur=0.4,
            skip_nsfw=skip_nsfw,
            landmarker_score=0.5
        )

    return result

if __name__ == "__main__":
    face_swap("imgs/input.png", "imgs/target.png", skip_nsfw=True)

