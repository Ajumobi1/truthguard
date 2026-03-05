"""Lightweight image detector using a pretrained ResNet feature extractor.

This is NOT a production-grade fake detector; it demonstrates integrating
an actual model for inference and computing a heuristic score combining
feature-space statistics and image sharpness. Replace with a trained
fake-detection network (e.g., UniversalFakeDetect) for real accuracy.
"""

from typing import Optional
try:
    import torch
    from torchvision import models, transforms
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False
try:
    from PIL import Image
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False
import numpy as np
import cv2


class ImageDetector:
    def __init__(self, model_path: Optional[str] = None, device: str = 'cpu'):
        self.device = device
        if TORCH_AVAILABLE:
            # feature extractor (ResNet18 without the final classifier)
            self.backbone = models.resnet18(pretrained=True)
            self.backbone.fc = torch.nn.Identity()
            self.backbone.eval().to(self.device)
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406],
                                     [0.229, 0.224, 0.225])
            ])
        else:
            self.backbone = None
            self.transform = None

    def _feature_vector(self, pil_image: Image.Image) -> np.ndarray:
        x = self.transform(pil_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            feats = self.backbone(x).cpu().numpy().squeeze()
        return feats

    def _sharpness(self, img_path: str) -> float:
        # variance of Laplacian (higher = sharper)
        im = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if im is None:
            return 0.0
        return float(cv2.Laplacian(im, cv2.CV_64F).var())

    def predict(self, image_path: str) -> float:
        """Return a heuristic score in [0,1] where higher means more likely AI-generated.

        The heuristic combines feature-vector statistics and image sharpness.
        This is a stopgap until a proper trained classifier is integrated.
        """

        sharp = self._sharpness(image_path)

        # try to load PIL image if available; otherwise fall back to cv2
        pil = None
        if HAVE_PIL:
            try:
                pil = Image.open(image_path).convert('RGB')
            except Exception:
                pil = None

        if self.backbone is not None and TORCH_AVAILABLE and pil is not None:
            feats = self._feature_vector(pil)
            # simple statistics on feature vector
            norm = float(np.linalg.norm(feats))
            std = float(np.std(feats))

            # map metrics to 0..1
            norm_score = 1.0 / (1.0 + np.exp(-(norm - 100)))
            std_score = 1.0 / (1.0 + np.exp(-(std - 50)))
            sharp_score = 1.0 - 1.0 / (1.0 + np.exp(-(sharp - 100)))

            # combine
            score = 0.5 * std_score + 0.35 * (1.0 - sharp_score) + 0.15 * (1.0 - norm_score)
            score = max(0.0, min(1.0, score))
            return score
        else:
            # fallback heuristic without torch: use sharpness, color statistics
            if pil is not None:
                arr = np.array(pil).astype(np.float32) / 255.0
            else:
                # try cv2 load
                im = cv2.imread(image_path)
                if im is None:
                    return 0.0
                arr = cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            # colorfulness metric
            rg = arr[..., 0] - arr[..., 1]
            yb = 0.5 * (arr[..., 0] + arr[..., 1]) - arr[..., 2]
            colorfulness = np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
            entropy = -np.sum(np.histogram(arr.flatten(), bins=64, range=(0, 1), density=True)[0] * np.log1p(np.histogram(arr.flatten(), bins=64, range=(0, 1), density=True)[0]))
            # normalize heuristics
            sharp_norm = 1.0 / (1.0 + np.exp(-(sharp - 100)))
            color_norm = 1.0 / (1.0 + np.exp(-(colorfulness * 10 - 1)))
            entropy_norm = 1.0 / (1.0 + np.exp(-(entropy - 3)))
            # AI images may have lower sharpness and lower colorfulness/entropy
            score = 0.5 * (1.0 - sharp_norm) + 0.3 * (1.0 - color_norm) + 0.2 * (1.0 - entropy_norm)
            return float(max(0.0, min(1.0, score)))


if __name__ == '__main__':
    # quick smoke test (requires an image path)
    import sys
    if len(sys.argv) > 1:
        det = ImageDetector()
        print(det.predict(sys.argv[1]))
