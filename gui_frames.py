import cv2
import numpy as np
from typing import Tuple, Optional, Union, Callable
from plugins.cv2_visualization_plugin.gui_component import GuiComponent

class GUIFrames(GuiComponent):
    """A component to display a video frame with optional camera name label."""
    def __init__(
        self, 
        name: str, 
        parent: Optional[GuiComponent] = None, 
        position: Tuple[int, int] = (0, 0), 
        width: Union[int, Callable[[int], int], str] = 640, 
        height: Union[int, Callable[[int], int], str] = 480,
        show_camera_name: bool = True
    ):
        """Initializes the component without a frame."""
        super().__init__(name, width, height, parent, position)
        self.show_camera_name = show_camera_name
        self.camera_name = name  # Store the camera name for display

    def set_frame(self, frame: np.ndarray):
        """Sets the video frame and scales it to fit the component dimensions."""
        # Scale frame to fit the component's width and height
        scaled_frame = cv2.resize(frame, (self.width, self.height))
        self.canvas = scaled_frame.copy()  # Copy to avoid modifying original
        
        # Add camera name overlay if enabled
        if self.show_camera_name:
            self._add_camera_name_overlay()

    def _add_camera_name_overlay(self):
        """Add camera name text overlay to the frame."""
        if self.canvas is not None:
            # Add semi-transparent background for text
            overlay = self.canvas.copy()
            text_height = 30
            cv2.rectangle(overlay, (0, 0), (self.width, text_height), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, self.canvas, 0.3, 0, self.canvas)
            
            # Add camera name text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            font_color = (255, 255, 255)  # White text
            thickness = 2
            
            # Calculate text position (centered)
            text_size = cv2.getTextSize(self.camera_name, font, font_scale, thickness)[0]
            text_x = (self.width - text_size[0]) // 2
            text_y = 20
            
            cv2.putText(self.canvas, self.camera_name, (text_x, text_y), 
                       font, font_scale, font_color, thickness)

    def draw(self):
        """Draws the stored frame onto the surface at its absolute position."""
        if self.canvas is None:
            self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)