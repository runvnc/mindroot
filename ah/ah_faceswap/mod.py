from facefusionlib import swapper
from facefusionlib.swapper import DeviceProvider
from os import listdir, path
import shutil
import nanoid
from ..services import service


@service()
async def swap_face(input_ref_dir, target_image_path, context=None, skip_nsfw=False, wrap_html=False): 
    print("-------------------- face_swap")
    input_image_paths = [path.join(input_ref_dir, f) for f in listdir(input_ref_dir) if path.isfile(path.join(input_ref_dir, f))]
    print("input_ref_dir:", input_ref_dir)
    print("input_image_paths:", input_image_paths)
    print("target_image_path:", target_image_path)
    result = swapper.swap_face(
            source_paths=input_image_paths,
            target_path=target_image_path,
            provider=DeviceProvider.GPU,
            detector_score=0.65,
            mask_blur=0.6,
            skip_nsfw=True,
            landmarker_score=0.005
        )
    print("face swap result image: ", result)
    new_fname = "imgs/" + nanoid.generate() + ".png"
    result = shutil.copy(result, new_fname)

    if wrap_html:
        result = f'<img src="{result}" style="max-width: 100%; height: auto;" />'
    return result

if __name__ == "__main__":
    face_swap("imgs/faceref/g", "imgs/target.png", skip_nsfw=True)

