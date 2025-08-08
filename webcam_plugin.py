from typing import Dict, Optional, List
from .webcam import Webcam
from .camera_identifier import create_camera_identifier

# Add path to import config manager
from managers.config_manager.config_manager import ConfigManager
from utils.logger_util.logger import get_logger


class WebcamPlugin:
    """
    WebcamPlugin provides managed access to multiple webcam devices.
    Integrates with ConfigManager to load camera configurations.
    """
    
    def __init__(self):
        """Initialize WebcamPlugin with configuration from ConfigManager."""
        self.logger = get_logger("WebcamPlugin")
        self.config_manager = ConfigManager()
        self.camera_identifier = create_camera_identifier()
        self.cameras: Dict[str, Webcam] = {}
        # Removed hardware signature based tracking
        self._load_cameras_from_config()
    
    def _load_cameras_from_config(self):
        """Load camera configurations and initialize webcam instances using device_id only."""
        try:
            # Log available devices (ids only) for operator awareness
            try:
                available_devices = self.camera_identifier.get_available_video_devices()
                self.logger.info(f"Found {len(available_devices)} video devices: {available_devices}")
            except Exception as e:
                self.logger.debug(f"Device discovery skipped: {e}")
            
            # Access webcam_plugin configuration (generated typed keys)
            webcam_config = self.config_manager.config.webcam_plugin
            devices_config = (webcam_config.devices or []) if webcam_config else []
            
            loaded_count = 0
            for device in devices_config:
                name = getattr(device, 'name', None) or f"camera_{loaded_count}"
                device_id = getattr(device, 'device_id', None)
                if device_id is None:
                    self.logger.warning(f"Skipping '{name}': missing device_id in config")
                    continue
                try:
                    camera = Webcam(
                        device_id=device_id,
                        width=getattr(device, 'width', None),
                        height=getattr(device, 'height', None),
                        buffer_size=getattr(device, 'buffer_size', None),
                        name=name,
                        orientation=getattr(device, 'orientation', 0.0),
                    )
                    self.cameras[name] = camera
                    loaded_count += 1
                    self.logger.info(f"Loaded camera '{name}' (device_id={device_id})")
                except Exception as cam_err:
                    self.logger.error(f"Failed to create camera '{name}': {cam_err}")

            self.logger.info(f"Successfully loaded {len(self.cameras)} cameras")
                
        except Exception as e:
            self.logger.error(f"Error loading camera configuration: {e}")
            # Fallback: create a default camera
            self.cameras['default'] = Webcam(name="default_camera")

    def get_camera(self, camera_id: str) -> Optional[Webcam]:
        return self.cameras.get(camera_id)
    
    def get_camera_by_name(self, name: str) -> Optional[Webcam]:
        for camera in self.cameras.values():
            if camera.name == name:
                return camera
        return None

    def get_all_cameras(self) -> Dict[str, Webcam]:
        """Return all loaded cameras."""
        return self.cameras
    
    def get_camera_names(self) -> List[str]:
        return [camera.name for camera in self.cameras.values()]

    def get_active_cameras(self) -> Dict[str, Webcam]:
        return {
            cam_id: camera 
            for cam_id, camera in self.cameras.items() 
            if camera.is_opened
        }
    
    def get_camera_info(self, camera_id: str) -> Optional[dict]:
        camera = self.get_camera(camera_id)
        if camera:
            return camera.get_device_info()
        return None
    
    def list_cameras(self) -> None:
        """Log a summary of all configured cameras."""
        self.logger.info(f"\nWebcamPlugin - Available Cameras ({len(self.cameras)}):")
        self.logger.info("-" * 50)
        
        for cam_id, camera in self.cameras.items():
            info = camera.get_device_info()
            self.logger.info(f"{cam_id}: oriented={info['width']}x{info['height']} raw={info['raw_width']}x{info['raw_height']} ori={info['orientation']}° id={info['device_id']}")
    
    def release_all(self):
        """Release all camera resources."""
        for camera in self.cameras.values():
            camera.release()
        self.logger.info("All cameras released")
    
    def __del__(self):
        """Destructor to ensure all cameras are released."""
        self.release_all()


# Singleton instance for easy access
_webcam_plugin_instance = None

def get_webcam_plugin() -> WebcamPlugin:
    """
    Get the singleton WebcamPlugin instance.
    
    Returns:
        WebcamPlugin instance
    """
    global _webcam_plugin_instance
    if _webcam_plugin_instance is None:
        _webcam_plugin_instance = WebcamPlugin()
    return _webcam_plugin_instance