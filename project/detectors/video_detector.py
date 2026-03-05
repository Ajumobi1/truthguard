"""Video detector that samples frames and aggregates image detector scores.

This implementation samples one frame every N frames and uses the
`detectors.image_detector.ImageDetector` to produce a per-frame score,
then returns the mean score. Replace with MesoNet or a temporal model for
production deepfake detection.
"""

import cv2
import numpy as np
from typing import Optional
from detectors.image_detector import ImageDetector


class VideoDetector:
    def __init__(self, model_path: Optional[str] = None, sample_rate: int = 15):
        # sample_rate: take every Nth frame
        self.sample_rate = sample_rate
        try:
            self.image_detector = ImageDetector(model_path)
        except Exception:
            # image detector should be robust; but fallback to None
            self.image_detector = None

    def predict(self, video_path: str) -> float:
        cap = cv2.VideoCapture(video_path)
        frame_idx = 0
        scores = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % self.sample_rate == 0:
                # write a temporary image in memory using OpenCV and pass to detector
                success, jpg = cv2.imencode('.jpg', frame)
                if not success:
                    frame_idx += 1
                    continue
                # if image detector exists, use it; otherwise skip
                if self.image_detector is None:
                    frame_idx += 1
                    continue
                # decode to PIL via bytes and write a temp file for the detector
                import tempfile
                import os
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                try:
                    tmp.write(jpg.tobytes())
                    tmp.flush()
                    tmp.close()
                    score = self.image_detector.predict(tmp.name)
                    scores.append(score)
                finally:
                    try:
                        os.unlink(tmp.name)
                    except Exception:
                        pass
            frame_idx += 1
        cap.release()
        return float(np.mean(scores)) if scores else 0.0


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        vd = VideoDetector()
        print(vd.predict(sys.argv[1]))
