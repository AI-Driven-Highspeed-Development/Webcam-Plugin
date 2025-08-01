import cv2
import os
import subprocess
import json
from typing import Dict, List, Optional, Tuple
import platform
from abc import ABC, abstractmethod

class CameraIdentifier(ABC):
    """
    Base class for camera identification system that uses multiple methods 
    to create persistent camera identities beyond simple device IDs.
    """
    
    def __init__(self):
        self.system = platform.system().lower()
        
    def get_camera_info(self, device_id: int) -> Dict[str, str]:
        """
        Get comprehensive camera information for identification.
        
        Args:
            device_id: OpenCV device ID
            
        Returns:
            Dictionary with camera identification information
        """
        info = {
            'device_id': str(device_id),
            'hardware_id': '',
            'vendor_id': '',
            'product_id': '',
            'serial_number': '',
            'device_path': '',
            'name': '',
            'resolution_signature': '',
            'unique_signature': ''
        }
        
        # Get basic OpenCV properties
        cap = cv2.VideoCapture(device_id)
        if cap.isOpened():
            # Create a resolution signature
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            info['resolution_signature'] = f"{width}x{height}@{fps}"
            cap.release()
        
        # Platform-specific hardware identification
        self._get_platform_camera_info(device_id, info)
            
        # Create a unique signature combining available identifiers
        signature_parts = [
            info.get('vendor_id', ''),
            info.get('product_id', ''),
            info.get('serial_number', ''),
            info.get('resolution_signature', ''),
            info.get('name', '').replace(' ', '_')
        ]
        info['unique_signature'] = '_'.join([part for part in signature_parts if part])
        
        return info
    
    @abstractmethod
    def _get_platform_camera_info(self, device_id: int, info: Dict[str, str]):
        """Platform-specific camera information retrieval."""
        pass
    
    @abstractmethod
    def get_available_video_devices(self) -> List[int]:
        """Get a list of all available video device IDs."""
        pass
    
    def get_all_cameras(self) -> Dict[str, Dict[str, str]]:
        """
        Scan for all available cameras and return their identification info.
        
        Returns:
            Dictionary mapping unique signatures to camera info
        """
        cameras = {}
        
        # Get available video devices first
        available_devices = self.get_available_video_devices()
        print(f"Found video devices: {available_devices}")
        
        # Test each available device
        for device_id in available_devices:
            cap = cv2.VideoCapture(device_id)
            if cap.isOpened():
                info = self.get_camera_info(device_id)
                cap.release()
                
                # Use unique signature as key, fallback to device_id
                key = info['unique_signature'] if info['unique_signature'] else f"device_{device_id}"
                cameras[key] = info
                
        return cameras
    
    def find_camera_by_signature(self, target_signature: str) -> Optional[int]:
        """
        Find a camera by its unique signature and return the current device ID.
        
        Args:
            target_signature: The unique signature to search for
            
        Returns:
            Current device ID if found, None otherwise
        """
        cameras = self.get_all_cameras()
        for signature, info in cameras.items():
            if signature == target_signature:
                return int(info['device_id'])
        return None


class LinuxCameraIdentifier(CameraIdentifier):
    """Linux-specific camera identification using v4l2 and udev."""
    
    def _get_platform_camera_info(self, device_id: int, info: Dict[str, str]):
        """Get camera info on Linux using v4l2 and udev."""
        try:
            # Map OpenCV device ID to video device
            video_device = f"/dev/video{device_id}"
            
            # Get device info using v4l2-ctl if available
            try:
                result = subprocess.run(['v4l2-ctl', '--device', video_device, '--info'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Card type' in line:
                            info['name'] = line.split(':')[1].strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Get hardware info using udevadm
            try:
                result = subprocess.run(['udevadm', 'info', '--name', video_device], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'ID_VENDOR_ID=' in line:
                            info['vendor_id'] = line.split('=')[1].strip()
                        elif 'ID_MODEL_ID=' in line:
                            info['product_id'] = line.split('=')[1].strip()
                        elif 'ID_SERIAL_SHORT=' in line:
                            info['serial_number'] = line.split('=')[1].strip()
                        elif 'DEVPATH=' in line:
                            info['device_path'] = line.split('=')[1].strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
                
        except Exception as e:
            print(f"Error getting Linux camera info: {e}")
    
    def get_available_video_devices(self) -> List[int]:
        """Get a list of all available /dev/video[x] device IDs."""
        available_devices = []
        
        # Check /dev/video* devices
        import glob
        video_devices = glob.glob('/dev/video*')
        for device_path in video_devices:
            try:
                # Extract device number from /dev/video[x]
                device_num = int(device_path.replace('/dev/video', ''))
                available_devices.append(device_num)
            except ValueError:
                continue
        
        return sorted(available_devices)


class MacOSCameraIdentifier(CameraIdentifier):
    """macOS-specific camera identification using system_profiler."""
    
    def _get_platform_camera_info(self, device_id: int, info: Dict[str, str]):
        """Get camera info on macOS using system_profiler."""
        try:
            result = subprocess.run(['system_profiler', 'SPCameraDataType', '-json'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                cameras = data.get('SPCameraDataType', [])
                
                # Try to match by index (not perfect but better than nothing)
                if device_id < len(cameras):
                    camera = cameras[device_id]
                    info['name'] = camera.get('_name', '')
                    info['vendor_id'] = camera.get('vendor_id', '')
                    info['product_id'] = camera.get('product_id', '')
                    info['serial_number'] = camera.get('serial_num', '')
                    
        except Exception as e:
            print(f"Error getting macOS camera info: {e}")
    
    def get_available_video_devices(self) -> List[int]:
        """Get available video devices by testing OpenCV device IDs."""
        available_devices = []
        
        # For macOS, test OpenCV device IDs
        for device_id in range(10):
            cap = cv2.VideoCapture(device_id)
            if cap.isOpened():
                available_devices.append(device_id)
                cap.release()
            else:
                break
        
        return available_devices


class WindowsCameraIdentifier(CameraIdentifier):
    """Windows-specific camera identification using WMI or DirectShow."""
    
    def _get_platform_camera_info(self, device_id: int, info: Dict[str, str]):
        """Get camera info on Windows using available methods."""
        try:
            # Basic implementation - could be enhanced with wmi or pywin32
            # For now, just set a basic name
            info['name'] = f"Camera_{device_id}"
            
            # TODO: Implement Windows-specific hardware detection
            # This would require additional dependencies like:
            # - wmi: for Windows Management Instrumentation
            # - pywin32: for Windows API access
            # - or DirectShow API access
            
        except Exception as e:
            print(f"Error getting Windows camera info: {e}")
    
    def get_available_video_devices(self) -> List[int]:
        """Get available video devices by testing OpenCV device IDs."""
        available_devices = []
        
        # For Windows, test OpenCV device IDs
        for device_id in range(10):
            cap = cv2.VideoCapture(device_id)
            if cap.isOpened():
                available_devices.append(device_id)
                cap.release()
            else:
                break
        
        return available_devices


def create_camera_identifier() -> CameraIdentifier:
    """
    Factory function to create the appropriate CameraIdentifier for the current platform.
    
    Returns:
        Platform-specific CameraIdentifier instance
    """
    system = platform.system().lower()
    
    if system == 'linux':
        return LinuxCameraIdentifier()
    elif system == 'darwin':  # macOS
        return MacOSCameraIdentifier()
    elif system == 'windows':
        return WindowsCameraIdentifier()
    else:
        # Fallback to Linux implementation for unknown systems
        print(f"Unknown system '{system}', using Linux camera identifier")
        return LinuxCameraIdentifier()
