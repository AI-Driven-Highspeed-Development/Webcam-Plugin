import cv2
import numpy as np
from typing import Tuple, Optional, Union, Callable
from plugins.cv2_visualization_plugin.gui_component import GuiComponent

class GUIFrames(GuiComponent):
    """A component to display a video frame."""
    def __init__(
        self, 
        name: str, 
        parent: Optional[GuiComponent] = None, 
        position: Tuple[int, int] = (0, 0), 
        width: Union[int, Callable[[int], int], str] = 640, 
        height: Union[int, Callable[[int], int], str] = 480
    ):
        """Initializes the component without a frame."""
        super().__init__(name, width, height, parent, position)

    def set_frame(self, frame: np.ndarray):
        """Sets the video frame and scales it to fit the component dimensions."""
        # Scale frame to fit the component's width and height
        scaled_frame = cv2.resize(frame, (self.width, self.height))
        self.canvas = scaled_frame

    def draw(self):
        """Draws the stored frame onto the surface at its absolute position."""
        if self.canvas is None:
            self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)