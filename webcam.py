import cv2
import numpy as np
from typing import Optional, Tuple

class Webcam:
    def __init__(self, device_id: int = 0, width: int = 640, height: int = 480, buffer_size: int = 1, name: str = "default_camera"):
        """
        Initialize webcam with configurable properties.
        
        Args:
            device_id: Camera device ID (usually 0 for default camera)
            width: Frame width in pixels
            height: Frame height in pixels
            buffer_size: Camera buffer size (1 for minimal latency)
            name: Human-readable name for the camera device
        """
        self.device_id = device_id
        self.width = width
        self.height = height
        self.buffer_size = buffer_size
        self.name = name
        self.cap = None
        self.is_opened = False
        
        self._initialize_camera()
    
    def _initialize_camera(self) -> bool:
        """Initialize the camera with specified properties."""
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera with device ID: {self.device_id}")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            
            # Verify actual resolution
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"Camera '{self.name}' initialized: {actual_width}x{actual_height} (device_id: {self.device_id})")
            self.is_opened = True
            return True
            
        except Exception as e:
            print(f"Error initializing camera '{self.name}': {e}")
            self.is_opened = False
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture and return a frame from the webcam.
        
        Returns:
            np.ndarray: BGR image frame, or None if capture failed
        """
        if not self.is_opened or self.cap is None:
            return None
        
        ret, frame = self.cap.read()
        
        if not ret:
            print(f"Failed to capture frame from camera '{self.name}'")
            return None
        
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
        Get current camera resolution.
        
        Returns:
            Tuple[int, int]: (width, height)
        """
        if not self.is_opened or self.cap is None:
            return (0, 0)
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)
    
    def set_resolution(self, width: int, height: int) -> bool:
        """
        Set camera resolution.
        
        Args:
            width: Frame width in pixels
            height: Frame height in pixels
            
        Returns:
            bool: True if resolution was set successfully
        """
        if not self.is_opened or self.cap is None:
            return False
        
        success_width = self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        success_height = self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if success_width and success_height:
            self.width = width
            self.height = height
            return True
        
        return False
    
    def get_device_info(self) -> dict:
        """
        Get comprehensive device information.
        
        Returns:
            dict: Device information including name, ID, resolution, etc.
        """
        width, height = self.get_resolution()
        return {
            "name": self.name,
            "device_id": self.device_id,
            "width": width,
            "height": height,
            "buffer_size": self.buffer_size,
            "is_opened": self.is_opened,
            "fps": self.get_property(cv2.CAP_PROP_FPS) if self.is_opened else -1
        }
    
    def release(self):
        """Release the camera resource."""
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False
            print(f"Camera '{self.name}' released")
    
    def __del__(self):
        """Destructor to ensure camera is released."""
        self.release()