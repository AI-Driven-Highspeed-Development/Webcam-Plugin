from typing import Dict, Optional, List
from webcam import Webcam

# Add path to import config manager
from managers.config_manager.config_manager import ConfigManager


class WebcamPlugin:
    """
    WebcamPlugin provides managed access to multiple webcam devices.
    Integrates with ConfigManager to load camera configurations from .config file.
    """
    
    def __init__(self):
        """Initialize WebcamPlugin with configuration from ConfigManager."""
        self.config_manager = ConfigManager()
        self.cameras: Dict[str, Webcam] = {}
        self._load_cameras_from_config()
    
    def _load_cameras_from_config(self):
        """Load camera configurations and initialize webcam instances."""
        try:
            # Access webcam_plugin configuration
            webcam_config = self.config_manager.config.webcam_plugin
            
            if hasattr(webcam_config, 'devices'):
                devices_config = webcam_config.devices
                
                # Get all camera configurations
                for cam_attr in dir(devices_config):
                    if not cam_attr.startswith('_') and cam_attr != '__class__':
                        cam_config = getattr(devices_config, cam_attr)
                        
                        # Extract camera configuration
                        device_id = getattr(cam_config, 'device_id', 0)
                        width = getattr(cam_config, 'width', 640)
                        height = getattr(cam_config, 'height', 480)
                        buffer_size = getattr(cam_config, 'buffer_size', 1)
                        name = getattr(cam_config, 'name', cam_attr)
                        
                        # Create webcam instance
                        camera = Webcam(
                            device_id=device_id,
                            width=width,
                            height=height,
                            buffer_size=buffer_size,
                            name=name
                        )
                        
                        # Store camera with config key as identifier
                        self.cameras[cam_attr] = camera
                        
                print(f"WebcamPlugin: Loaded {len(self.cameras)} cameras from configuration")
                
        except Exception as e:
            print(f"WebcamPlugin: Error loading camera configuration: {e}")
            # Fallback: create a default camera
            self.cameras['default'] = Webcam(name="default_camera")
    
    def get_camera(self, camera_id: str) -> Optional[Webcam]:
        """
        Get a camera instance by ID.
        
        Args:
            camera_id: Camera identifier from configuration (e.g., 'cam01')
            
        Returns:
            Webcam instance or None if not found
        """
        return self.cameras.get(camera_id)
    
    def get_all_cameras(self) -> Dict[str, Webcam]:
        """
        Get all available camera instances.
        
        Returns:
            Dictionary of camera_id -> Webcam instances
        """
        return self.cameras.copy()
    
    def get_camera_names(self) -> List[str]:
        """
        Get list of all available camera IDs.
        
        Returns:
            List of camera identifiers
        """
        return list(self.cameras.keys())
    
    def get_active_cameras(self) -> Dict[str, Webcam]:
        """
        Get only the cameras that are currently opened and active.
        
        Returns:
            Dictionary of active camera_id -> Webcam instances
        """
        return {
            cam_id: camera 
            for cam_id, camera in self.cameras.items() 
            if camera.is_opened
        }
    
    def get_camera_info(self, camera_id: str) -> Optional[dict]:
        """
        Get detailed information about a specific camera.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Camera information dictionary or None if not found
        """
        camera = self.get_camera(camera_id)
        if camera:
            return camera.get_device_info()
        return None
    
    def list_cameras(self) -> None:
        """Print a summary of all configured cameras."""
        print(f"\nWebcamPlugin - Available Cameras ({len(self.cameras)}):")
        print("-" * 50)
        
        for cam_id, camera in self.cameras.items():
            info = camera.get_device_info()
            status = "🟢 Active" if info['is_opened'] else "🔴 Inactive"
            print(f"{cam_id:8} | {info['name']:15} | {status} | {info['width']}x{info['height']} | Device {info['device_id']}")
    
    def release_all(self):
        """Release all camera resources."""
        for camera in self.cameras.values():
            camera.release()
        print("WebcamPlugin: All cameras released")
    
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