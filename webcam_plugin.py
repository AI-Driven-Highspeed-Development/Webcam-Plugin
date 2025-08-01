from typing import Dict, Optional, List
from .webcam import Webcam
from .camera_identifier import create_camera_identifier

# Add path to import config manager
from managers.config_manager.config_manager import ConfigManager


class WebcamPlugin:
    """
    WebcamPlugin provides managed access to multiple webcam devices.
    Integrates with ConfigManager to load camera configurations and uses
    CameraIdentifier for persistent camera recognition.
    """
    
    def __init__(self):
        """Initialize WebcamPlugin with configuration from ConfigManager."""
        self.config_manager = ConfigManager()
        self.camera_identifier = create_camera_identifier()
        self.cameras: Dict[str, Webcam] = {}
        self.camera_signatures: Dict[str, str] = {}  # Map config names to signatures
        self._load_cameras_from_config()
    
    def _load_cameras_from_config(self):
        """Load camera configurations and initialize webcam instances with persistent identification."""
        try:
            # Get available cameras with their hardware signatures
            available_cameras = self.camera_identifier.get_all_cameras()
            print(f"WebcamPlugin: Found {len(available_cameras)} cameras")
            
            # Debug: Print available camera signatures
            for signature, info in available_cameras.items():
                print(f"  - {signature}: {info.get('name', 'Unknown')} (device_id: {info['device_id']})")
            
            # Access webcam_plugin configuration
            webcam_config = self.config_manager.config.webcam_plugin
            devices_config = webcam_config.devices
            config_updated = False
                
            # Process each device configuration
            updated_devices = []
            for i, device in enumerate(devices_config):
                
                if self._has_hardware_signature(device):
                    # Device has signature - find by signature and update device_id
                    updated_device, changed = self._load_camera_by_signature(device)
                    config_updated |= changed
                else:
                    # No signature - generate one and save it
                    updated_device, changed = self._generate_camera_signature(device)
                    config_updated |= changed
                
                updated_devices.append(updated_device)

            # Update the raw config with the modified devices
            if config_updated:
                self.config_manager.raw_config['webcam_plugin']['devices'] = updated_devices
                self.config_manager.save_config(self.config_manager.raw_config)
                print("WebcamPlugin: Updated configuration saved")

            print(f"WebcamPlugin: Successfully loaded {len(self.cameras)} cameras")
                
        except Exception as e:
            print(f"WebcamPlugin: Error loading camera configuration: {e}")
            # Fallback: create a default camera
            self.cameras['default'] = Webcam(name="default_camera")
    
    def _has_hardware_signature(self, device: dict) -> bool:
        """Check if device configuration has a valid hardware signature."""
        return 'hardware_signature' in device and device['hardware_signature']
    
    def _load_camera_by_signature(self, device: dict) -> tuple[dict, bool]:
        """Load camera by hardware signature and update device_id if needed."""
        device_name = device['name']
        configured_device_id = device['device_id']
        target_signature = device['hardware_signature']
        
        # Create a copy of the device config to modify
        updated_device = device.copy()
        
        actual_device_id = self.camera_identifier.find_camera_by_signature(target_signature)
        
        if actual_device_id is None:
            print(f"WebcamPlugin: Camera '{device_name}' with signature '{target_signature}' not found")
            return updated_device, False
        
        # Update device_id in config if it changed
        config_changed = False
        if actual_device_id != configured_device_id:
            updated_device['device_id'] = actual_device_id
            config_changed = True
            print(f"WebcamPlugin: Updated device_id for '{device_name}' from {configured_device_id} to {actual_device_id}")
        
        # Create camera instance
        if self._create_camera_instance(updated_device, actual_device_id, target_signature):
            print(f"WebcamPlugin: Found camera '{device_name}' by signature at device_id {actual_device_id}")
        
        return updated_device, config_changed
    
    def _generate_camera_signature(self, device: dict) -> tuple[dict, bool]:
        """Generate hardware signature for device and save it."""
        device_name = device['name']
        configured_device_id = device['device_id']
        
        # Create a copy of the device config to modify
        updated_device = device.copy()
        
        try:
            # Create camera instance first
            camera = Webcam(
                device_id=configured_device_id,
                width=device['width'],
                height=device['height'],
                buffer_size=device['buffer_size'],
                name=device_name
            )
            
            # Generate signature for this camera
            camera_info = self.camera_identifier.get_camera_info(configured_device_id)
            signature = camera_info['unique_signature']
            
            # Update config and store camera
            updated_device['hardware_signature'] = signature
            self.cameras[device_name] = camera
            self.camera_signatures[device_name] = signature
            
            print(f"WebcamPlugin: Generated signature for '{device_name}' at device_id {configured_device_id}")
            print(f"  Hardware signature: {signature}")
            
            return updated_device, True  # Config was updated
            
        except Exception as e:
            print(f"WebcamPlugin: Failed to create camera '{device_name}': {e}")
            return updated_device, False
    
    def _create_camera_instance(self, device: dict, device_id: int, signature: str) -> bool:
        """Create camera instance and store it."""
        device_name = device['name']
        
        try:
            camera = Webcam(
                device_id=device_id,
                width=device['width'],
                height=device['height'],
                buffer_size=device['buffer_size'],
                name=device_name
            )
            
            self.cameras[device_name] = camera
            self.camera_signatures[device_name] = signature
            return True
            
        except Exception as e:
            print(f"WebcamPlugin: Failed to create camera '{device_name}': {e}")
            return False
    
    def get_camera(self, camera_id: str) -> Optional[Webcam]:
        return self.cameras.get(camera_id)
    
    def get_camera_by_name(self, name: str) -> Optional[Webcam]:
        for camera in self.cameras.values():
            if camera.name == name:
                return camera
        return None

    def get_camera_signatures(self) -> Dict[str, str]:
        """
        Get hardware signatures for all loaded cameras.
        
        Returns:
            Dictionary mapping camera names to their hardware signatures
        """
        return self.camera_signatures.copy()
    
    def save_camera_signatures_to_config(self):
        """
        Save the current camera signatures back to the configuration for persistence.
        This allows the system to remember camera hardware signatures.
        """
        try:
            # Update the configuration with hardware signatures
            webcam_config = self.config_manager.config.webcam_plugin
            devices_config = webcam_config.devices
            
            for device in devices_config:
                device_name = device['name']
                if device_name in self.camera_signatures:
                    device['hardware_signature'] = self.camera_signatures[device_name]
            
            # Save the updated configuration
            self.config_manager.save_config(self.config_manager.raw_config)
            print("WebcamPlugin: Saved camera hardware signatures to configuration")
            
        except Exception as e:
            print(f"WebcamPlugin: Error saving camera signatures: {e}")
    
    def discover_and_update_cameras(self):
        """
        Discover all available cameras and update the configuration with their signatures.
        This is useful for initial setup or when cameras change.
        """
        try:
            available_cameras = self.camera_identifier.get_all_cameras()
            
            print("WebcamPlugin: Discovered cameras:")
            for signature, info in available_cameras.items():
                print(f"  - Signature: {signature}")
                print(f"    Name: {info.get('name', 'Unknown')}")
                print(f"    Device ID: {info['device_id']}")
                print(f"    Resolution: {info.get('resolution_signature', 'Unknown')}")
                print(f"    Vendor/Product: {info.get('vendor_id', '')}/{info.get('product_id', '')}")
                print(f"    Serial: {info.get('serial_number', 'N/A')}")
                print()
                
        except Exception as e:
            print(f"WebcamPlugin: Error discovering cameras: {e}")
    
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