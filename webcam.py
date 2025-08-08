import cv2
import numpy as np
from typing import Optional, Tuple
from utils.logger_util.logger import get_logger

class Webcam:
    def __init__(self, device_id: int = 0, width: int = 640, height: int = 480, buffer_size: int = 1, name: str = "default_camera", orientation: float = 0.0):
        """
        Initialize webcam with configurable properties.
        
        Args:
            device_id: Camera device ID (usually 0 for default camera)
            width: Frame width in pixels (UNROTATED/raw)
            height: Frame height in pixels (UNROTATED/raw)
            buffer_size: Camera buffer size (1 for minimal latency)
            name: Human-readable name for the camera device
            orientation: Rotation to apply to frames (deg). Allowed: 0, 90, 180, 270.
        """
        self.logger = get_logger("Webcam")
        self.device_id = device_id
        # Raw unrotated dimensions from config
        self.raw_width = width
        self.raw_height = height
        self.buffer_size = buffer_size
        self.name = name
        self.cap = None
        self.is_opened = False
        
        # Normalize orientation to one of 0, 90, 180, 270 (clockwise)
        allowed = {0.0, 90.0, 180.0, 270.0}
        try:
            ori = float(orientation)
        except Exception:
            ori = 0.0
        if ori not in allowed:
            # Snap to nearest 90 and mod 360
            ori = (round(ori / 90.0) * 90.0) % 360.0
            if ori == 360.0:
                ori = 0.0
        self.orientation = ori
        
        self._initialize_camera()
    
    def _initialize_camera(self) -> bool:
        """Initialize the camera with specified properties."""
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera with device ID: {self.device_id}")
            
            # Set camera properties using RAW (unrotated) dimensions
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.raw_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.raw_height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            
            # Verify actual raw resolution
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.logger.info(f"Camera '{self.name}' initialized (raw): {actual_width}x{actual_height} (device_id: {self.device_id}, orientation: {int(self.orientation)}°)")
            self.is_opened = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing camera '{self.name}': {e}")
            self.is_opened = False
            return False
    
    def _apply_orientation(self, frame: np.ndarray) -> np.ndarray:
        """Rotate frame according to configured orientation (clockwise degrees)."""
        if frame is None:
            return frame
        if self.orientation == 0.0:
            return frame
        if self.orientation == 90.0:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        if self.orientation == 180.0:
            return cv2.rotate(frame, cv2.ROTATE_180)
        if self.orientation == 270.0:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        # Fallback no-op
        return frame
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture and return a frame from the webcam, rotated per orientation.
        
        Returns:
            np.ndarray: BGR image frame (after orientation), or None if capture failed
        """
        if not self.is_opened or self.cap is None:
            return None
        
        ret, frame = self.cap.read()
        
        if not ret:
            self.logger.error(f"Failed to capture frame from camera '{self.name}'")
            return None
        
        # Apply orientation so downstream sees correctly oriented frames
        frame = self._apply_orientation(frame)
        return frame
    
    def set_property(self, prop_id: int, value: float) -> bool:
        """
        Set a camera property.
        
        Args:
            prop_id: OpenCV property ID (e.g., cv2.CAP_PROP_FPS)
            value: Property value
            
        Returns:
            bool: True if property was set successfully
        """
        if not self.is_opened or self.cap is None:
            return False
        
        return self.cap.set(prop_id, value)
    
    def get_property(self, prop_id: int) -> float:
        """
        Get a camera property value.
        
        Args:
            prop_id: OpenCV property ID
            
        Returns:
            float: Property value, or -1 if failed
        """
        if not self.is_opened or self.cap is None:
            return -1
        
        return self.cap.get(prop_id)
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get current camera resolution after applying orientation.
        
        Returns:
            Tuple[int, int]: (width, height) of oriented frames
        """
        if not self.is_opened or self.cap is None:
            # Return oriented dimensions based on config/raw
            if self.orientation in (90.0, 270.0):
                return (self.raw_height, self.raw_width)
            return (self.raw_width, self.raw_height)
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if self.orientation in (90.0, 270.0):
            return (height, width)
        return (width, height)
    
    def set_resolution(self, width: int, height: int) -> bool:
        """
        Set camera resolution (RAW/unrotated).
        
        Args:
            width: Frame width in pixels (unrotated)
            height: Frame height in pixels (unrotated)
            
        Returns:
            bool: True if resolution was set successfully
        """
        if not self.is_opened or self.cap is None:
            return False
        
        success_width = self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        success_height = self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if success_width and success_height:
            self.raw_width = width
            self.raw_height = height
            return True
        
        return False
    
    def get_device_info(self) -> dict:
        """
        Get comprehensive device information.
        
        Returns:
            dict: Device information including name, ID, oriented/raw resolution, etc.
        """
        oriented_w, oriented_h = self.get_resolution()
        return {
            "name": self.name,
            "device_id": self.device_id,
            "width": oriented_w,
            "height": oriented_h,
            "raw_width": self.raw_width,
            "raw_height": self.raw_height,
            "orientation": int(self.orientation),
            "buffer_size": self.buffer_size,
            "is_opened": self.is_opened,
            "fps": self.get_property(cv2.CAP_PROP_FPS) if self.is_opened else -1
        }
    
    def release(self):
        """Release the camera resource."""
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False
            self.logger.info(f"Camera '{self.name}' released")
    
    def __del__(self):
        """Destructor to ensure camera is released."""
        self.release()
    
    @property
    def width(self) -> int:
        w, _ = self.get_resolution()
        return w
    
    @property
    def height(self) -> int:
        _, h = self.get_resolution()
        return h