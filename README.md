# AI Driven Highspeed Development Framework Module — Webcam Plugin

## Overview
Manages multiple webcams configured via the project `.config`. Loads device settings from ConfigManager, opens cameras by device_id (no hardware signatures), and provides a simple API to capture frames, query info, and release resources. Includes a small GUI component for rendering frames with labels.

## Capabilities
- Load camera list from `.config` (via ConfigManager)
- ID-only device matching (device_id); hardware signatures removed
- Multi-camera management with named accessors
- Orientation-aware frames (0/90/180/270 deg rotation)
- Resolution and buffer size configuration (raw/unrotated)
- Device discovery (list available /dev/videoX on Linux, etc.)
- Query device info (raw/oriented resolution, fps, opened state)
- Release-all cleanup
- Optional GUIFrames component to display frames with camera name overlay

## Components
### WebcamPlugin
High-level manager for multiple cameras.
- Source: `plugins/webcam_plugin/webcam_plugin.py`
- Responsibilities:
  - Read `webcam_plugin.devices` from `.config`
  - Create `Webcam` instances using device_id only
  - Provide getters for a camera by name/id and list/summary utilities
  - Log basic discovery info via platform-specific identifier

Key methods:
- `get_webcam_plugin() -> WebcamPlugin` (singleton accessor)
- `get_camera(name: str) -> Optional[Webcam]`
- `get_all_cameras() -> Dict[str, Webcam]`
- `get_active_cameras() -> Dict[str, Webcam]`
- `get_camera_names() -> List[str]`
- `list_cameras() -> None`
- `release_all() -> None`

### Webcam
Thin wrapper around `cv2.VideoCapture` with orientation handling.
- Source: `plugins/webcam_plugin/webcam.py`
- Init args: `device_id=0, width=640, height=480, buffer_size=1, name="default_camera", orientation=0.0`
- Methods: `get_frame()`, `get_resolution()`, `set_resolution()`, `set_property()`, `get_property()`, `get_device_info()`, `release()`
- Properties: `width`, `height` (post-orientation)
- Notes:
  - Orientation normalized to 0/90/180/270; applied to returned frames
  - Raw (unrotated) width/height are used to configure the device

### CameraIdentifier
Platform-specific utilities for device discovery and metadata.
- Source: `plugins/webcam_plugin/camera_identifier.py`
- Implementations: Linux (v4l2/udev), macOS (system_profiler), Windows (basic)
- Used only for discovery/logging; device matching is by device_id

### GUIFrames (optional)
Simple GUI component to render frames with an optional camera name overlay.
- Source: `plugins/webcam_plugin/gui_frames.py`
- Integrates with `cv2_visualization_plugin.GuiComponent`

## Lifecycle (How It Works)
1. On first access, call `get_webcam_plugin()` or instantiate `WebcamPlugin()`
2. The plugin reads `webcam_plugin.devices` from `.config` (via ConfigManager)
3. For each device config, a `Webcam` is created using `device_id` and optional settings
4. You can fetch frames, list cameras, or release resources as needed

## Quick Start
```python
from plugins.webcam_plugin.webcam_plugin import get_webcam_plugin

wp = get_webcam_plugin()
wp.list_cameras()

# Grab a frame from a named camera
cam = wp.get_camera("cam01")
frame = cam.get_frame() if cam else None

# Iterate all active cameras
for name, cam in wp.get_active_cameras().items():
    f = cam.get_frame()
    # process f

# Cleanup
wp.release_all()
```

## Examples
### API Usage (code)
```python
from plugins.webcam_plugin.webcam_plugin import WebcamPlugin

# Initialize explicitly (or use get_webcam_plugin())
wp = WebcamPlugin()

# Names from config
print(wp.get_camera_names())

# Query device info
info = wp.get_camera_info("cam01")
print(info)

# Change resolution (raw/unrotated)
cam = wp.get_camera("cam01")
if cam:
    cam.set_resolution(1280, 720)
    print("Oriented size:", cam.width, cam.height)
```

### Config JSON (data)
```json
{
  "webcam_plugin": {
    "devices": [
      {"name": "cam01", "device_id": 0, "width": 1280, "height": 720, "orientation": 0.0, "buffer_size": 1},
      {"name": "cam02", "device_id": 1, "width": 640, "height": 480, "orientation": 0.0, "buffer_size": 1}
    ]
  }
}
```

## CLI and Regeneration
- To apply manual `.config` edits to generated classes, refresh via Config Manager:
  - Reinitialize in code: `from managers.config_manager.config_manager import ConfigManager; ConfigManager()`
  - Or run: `python adhd_cli.py refresh config_manager`

## Module File Layout
- `plugins/webcam_plugin/webcam_plugin.py` — Multi-camera manager and singleton accessor
- `plugins/webcam_plugin/webcam.py` — `Webcam` device wrapper
- `plugins/webcam_plugin/camera_identifier.py` — Platform-specific discovery
- `plugins/webcam_plugin/gui_frames.py` — Optional GUI component for display
- `plugins/webcam_plugin/.config_template` — Default config seed merged into project `.config`
- `plugins/webcam_plugin/requirements.txt` — Module requirements
- `plugins/webcam_plugin/init.yaml` — Module metadata

## Implementation Notes
- Device matching is by `device_id` only; no hardware signature is stored/used
- Orientation is applied to frames after capture; raw resolution config remains unrotated
- Buffer size is set via `cv2.CAP_PROP_BUFFERSIZE` (driver support may vary)
- `get_resolution()` returns post-orientation dimensions
- On failure to load config or open a camera, a fallback `default_camera` may be created

## Troubleshooting
- Camera fails to open: check permissions (e.g., Linux `/dev/video*`), ensure device_id exists
- Wrong orientation: set `orientation` to 0/90/180/270 in `.config`
- Resolution not applied: some drivers ignore requested sizes; verify with `get_device_info()`
- High latency: try `buffer_size=1` and lower resolution
- No devices found: ensure OpenCV is built with the right backends; on Linux, validate with `v4l2-ctl --list-devices`

## Warnings
- Always call `release_all()` (or let destructors run) to free camera resources
- Avoid creating multiple `WebcamPlugin` instances; prefer the singleton accessor
- Orientation other than multiples of 90° is snapped to nearest 90°

## Related Files
- Project `.config` — consumed by ConfigManager to build typed keys

## Versioning & Maintenance
- Current behavior uses device-id only matching; hardware signature logic was intentionally removed
- Keep this document updated when changing device initialization or configuration schema