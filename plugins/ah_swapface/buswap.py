import sys
from pathlib import Path
from typing import List, Optional, Set, Union

import cv2
import insightface
import numpy as np
import onnxruntime
import torch
from insightface.model_zoo.inswapper import INSwapper
from PIL import Image
from utils import pil2tensor, tensor2pil
from download import download_and_extract

swapper = None

class FaceSwap:

    def __init__(self):
        self.check_for_models()
 
        self.face_analyser = insightface.app.FaceAnalysis(
            name="buffalo_l",
            root="models/face"
        )
        self.swap_model = INSwapper(
            "models/face",
            onnxruntime.InferenceSession(
                path_or_bytes='models/face/inswapper_128.onnx'
                providers=onnxruntime.get_available_providers(),
            ),
        )

    def check_for_models(self):
        model_path = Path("models/face/inswapper_128.onnx")
        if not model_path.exists():
            log.info("Models not found, downloading them")
            self.download_models()
        else:
            log.info("Models found, skipping download")

    def download_models(self):
        download_and_extract("https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip", "models/face")
        download_and_extract("https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx?download=true", "models/face")

    def get_face_single(
        self,
        img_data: np.ndarray, face_index=0, det_size=(640, 640)
    ):
        self.face_analyser.prepare(ctx_id=0, det_size=det_size)
        face = self.face_analyser.get(img_data)

        if len(face) == 0 and det_size[0] > 320 and det_size[1] > 320:
            log.debug("No face detected, trying again with smaller image")
            det_size_half = (det_size[0] // 2, det_size[1] // 2)
            return self.get_face_single(
                img_data,
                face_index=face_index,
                det_size=det_size_half,
            )

        try:
            return sorted(face, key=lambda x: x.bbox[0])[face_index]
        except IndexError:
            return None


    def swap_face(
        self,
        source_img: Union[Image.Image, List[Image.Image]],
        target_img: Union[Image.Image, List[Image.Image]],
        faces_index: Optional[Set[int]] = None,
    ) -> Image.Image:
        if faces_index is None:
            faces_index = {0}
        log.debug(f"Swapping faces: {faces_index}")
        result_image = target_img

        if face_swapper_model is not None:
            cv_source_img = cv2.cvtColor(np.array(source_img), cv2.COLOR_RGB2BGR)
            cv_target_img = cv2.cvtColor(np.array(target_img), cv2.COLOR_RGB2BGR)
            source_face = get_face_single(
                face_analyser, cv_source_img, face_index=0
            )
            if source_face is not None:
                result = cv_target_img

                for face_num in faces_index:
                    target_face = get_face_single(
                        face_analyser, cv_target_img, face_index=face_num
                    )
                    if target_face is not None:
                        sys.stdout = NullWriter()
                        result = face_swapper_model.get(
                            result, target_face, source_face
                        )
                        sys.stdout = sys.__stdout__
                    else:
                        log.warning(f"No target face found for {face_num}")

                result_image = Image.fromarray(
                    cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
                )
            else:
                log.warning("No source face found")
        else:
            log.error("No face swap model provided")
        return result_image

def __init__():
    global swapper = FaceSwap()



