"""NoWebcamPlugin: virtual camera provider for debug mode.

Creates virtual cameras based on config entries (webcam_plugin.devices) but instead of
opening real hardware it produces frames from a static image path specified by each
device's `no_cam_image_path`. If the path is missing or load fails, a blank frame is used.

Frames are returned via a lightweight VirtualWebcam shim exposing get_frame()/release().
Images are resized to requested width/height if necessary.
"""

from typing import Dict, Optional, List
import cv2
import numpy as np

from managers.config_manager.config_manager import ConfigManager
from utils.logger_util.logger import get_logger
from .webcam_plugin import WebcamPlugin  # for structural similarity / potential reuse


class VirtualWebcam:
    def __init__(self, name: str, source_img: np.ndarray, width: int, height: int, orientation: float = 0.0):
        self.name = name
        self._frame = self._prepare_frame(source_img, width, height, orientation)
        self.is_opened = True
        self.device_id = -1
        self.width = width
        self.height = height
        self.orientation = orientation

    def _prepare_frame(self, img: np.ndarray, w: int, h: int, orientation: float) -> np.ndarray:
        if img is None or img.size == 0:
            return np.zeros((h, w, 3), dtype=np.uint8)
        # Resize if different
        if img.shape[0] != h or img.shape[1] != w:
            img = cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)
        # Basic orientation rotate (multiples of 90)
        rot = int(orientation) % 360
        if rot == 90:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif rot == 180:
            img = cv2.rotate(img, cv2.ROTATE_180)
        elif rot == 270:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return img

    def get_frame(self):
        return self._frame.copy()

    def get_device_info(self):
        return {
            'width': self.width,
            'height': self.height,
            'raw_width': self.width,
            'raw_height': self.height,
            'orientation': self.orientation,
            'device_id': self.device_id,
        }

    def release(self):
        self.is_opened = False


class NoWebcamPlugin(WebcamPlugin):  # Inherit for API similarity; override init logic
    def __init__(self):
        self.logger = get_logger("NoWebcamPlugin")
        self.config_manager = ConfigManager()
        self.cameras: Dict[str, VirtualWebcam] = {}
        self._load_virtual_cameras()

    def _load_virtual_cameras(self):
        cfg = self.config_manager.config.webcam_plugin
        devices = (cfg.devices or []) if cfg else []
        loaded = 0
        for dev in devices:
            name = getattr(dev, 'name', f'virt_{loaded}')
            width = int(getattr(dev, 'width', 640) or 640)
            height = int(getattr(dev, 'height', 480) or 480)
            orientation = float(getattr(dev, 'orientation', 0.0) or 0.0)
            img_path = getattr(dev, 'no_cam_image_path', None)
            frame = None
            if img_path:
                try:
                    frame = cv2.imread(img_path, cv2.IMREAD_COLOR)
                    if frame is None:
                        self.logger.warning(f"Failed to load image for {name}: {img_path}; using blank frame")
                except Exception as e:
                    self.logger.warning(f"Exception loading image {img_path} for {name}: {e}")
            if frame is None:
                frame = np.zeros((height, width, 3), dtype=np.uint8)
            virt = VirtualWebcam(name=name, source_img=frame, width=width, height=height, orientation=orientation)
            self.cameras[name] = virt
            loaded += 1
            self.logger.info(f"Virtual camera '{name}' loaded from {img_path or 'blank'}")
        self.logger.info(f"Initialized {loaded} virtual cameras (debug mode)")

    # Override getters for clarity
    def get_all_cameras(self) -> Dict[str, VirtualWebcam]:
        return self.cameras

    def get_camera(self, camera_id: str):
        return self.cameras.get(camera_id)

    def list_cameras(self):
        self.logger.info(f"NoWebcamPlugin - Virtual Cameras ({len(self.cameras)}):")
        for name, cam in self.cameras.items():
            self.logger.info(f"{name}: {cam.width}x{cam.height} orient={cam.orientation}")

    def release_all(self):
        for cam in self.cameras.values():
            cam.release()
        self.logger.info("All virtual cameras released")


# Helper to mirror webcam plugin singleton style (optional)
_no_webcam_plugin_instance: Optional[NoWebcamPlugin] = None

def get_no_webcam_plugin() -> NoWebcamPlugin:
    global _no_webcam_plugin_instance
    if _no_webcam_plugin_instance is None:
        _no_webcam_plugin_instance = NoWebcamPlugin()
    return _no_webcam_plugin_instance