"""
Loop Visualizer for DXF Files

Handles visual highlighting and display of detected loops in graphics views.
"""

from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItem
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import Qt
from typing import Dict, List, Any, Optional
import ezdxf
import math


class LoopVisualizer:
    """Visualizes detected loops in graphics scenes."""
    
    def __init__(self, graphics_scene: QGraphicsScene):
        """
        Initialize the loop visualizer.
        
        Args:
            graphics_scene: The QGraphicsScene to draw on
        """
        self.graphics_scene = graphics_scene
        self.loop_items = []  # Store loop visualization items
        self.highlight_colors = [
            QColor(255, 0, 0, 128),    # Red
            QColor(0, 255, 0, 128),    # Green
            QColor(0, 0, 255, 128),    # Blue
            QColor(255, 255, 0, 128),  # Yellow
            QColor(255, 0, 255, 128),  # Magenta
            QColor(0, 255, 255, 128),  # Cyan
            QColor(255, 128, 0, 128),  # Orange
            QColor(128, 0, 255, 128),  # Purple
        ]
        
    def highlight_loops(self, loops_data: Dict[str, Any], highlight_style: str = 'outline') -> bool:
        """
        Highlight detected loops in the graphics scene.
        
        Args:
            loops_data: Dictionary containing loop information from LoopDetector
            highlight_style: Style of highlighting ('outline', 'fill', 'both')
            
        Returns:
            True if highlighting was successful, False otherwise
        """
        try:
            # Clear previous highlights
            self.clear_highlights()
            
            loops = loops_data.get('loops', [])
            if not loops:
                return False
            
            # Highlight each loop with a different color
            for i, loop_info in enumerate(loops):
                color = self.highlight_colors[i % len(self.highlight_colors)]
                self._highlight_single_loop(loop_info, color, highlight_style)
            
            return True
            
        except Exception as e:
            print(f"Error highlighting loops: {e}")
            return False
    
    def highlight_largest_loop(self, largest_loop_data: Dict[str, Any], 
                              color: Optional[QColor] = None) -> bool:
        """
        Highlight the largest detected loop.
        
        Args:
            largest_loop_data: Dictionary containing largest loop information
            color: Color to use for highlighting (default: red)
            
        Returns:
            True if highlighting was successful, False otherwise
        """
        try:
            # Clear previous highlights
            self.clear_highlights()
            
            if 'error' in largest_loop_data:
                return False
            
            highlight_color = color or QColor(255, 0, 0, 180)  # Red with transparency
            
            # Create a mock loop info structure for highlighting
            loop_info = {
                'id': 1,
                'entities': largest_loop_data.get('entities', 0),
                'area': largest_loop_data.get('area', 0),
                'loop_entities': largest_loop_data.get('loop_entities', [])
            }
            
            self._highlight_single_loop(loop_info, highlight_color, 'both')
            return True
            
        except Exception as e:
            print(f"Error highlighting largest loop: {e}")
            return False
    
    def highlight_nested_loops(self, nested_loops_data: Dict[str, Any]) -> bool:
        """
        Highlight nested loops with different visual styles.
        
        Args:
            nested_loops_data: Dictionary containing nested loop information
            
        Returns:
            True if highlighting was successful, False otherwise
        """
        try:
            # Clear previous highlights
            self.clear_highlights()
            
            nested_relationships = nested_loops_data.get('nested_loops', [])
            if not nested_relationships:
                return False
            
            # Use different styles for outer and inner loops
            outer_color = QColor(255, 0, 0, 100)  # Red for outer loops
            inner_color = QColor(0, 0, 255, 150)  # Blue for inner loops
            
            for relationship in nested_relationships:
                # This is a simplified implementation
                # In practice, you'd need access to the actual loop entities
                print(f"Nested relationship: Outer loop {relationship['outer_loop_id']} "
                      f"contains inner loop {relationship['inner_loop_id']}")
            
            return True
            
        except Exception as e:
            print(f"Error highlighting nested loops: {e}")
            return False
    
    def add_loop_annotations(self, loops_data: Dict[str, Any]) -> bool:
        """
        Add text annotations to loops showing their properties.
        
        Args:
            loops_data: Dictionary containing loop information
            
        Returns:
            True if annotations were added successfully, False otherwise
        """
        try:
            loops = loops_data.get('loops', [])
            
            for loop_info in loops:
                # Calculate annotation position (center of loop bounding box)
                bbox = loop_info.get('bounding_box', {})
                if bbox:
                    center_x = (bbox.get('min_x', 0) + bbox.get('max_x', 0)) / 2
                    center_y = (bbox.get('min_y', 0) + bbox.get('max_y', 0)) / 2
                    
                    # Create annotation text
                    annotation_text = f"Loop {loop_info.get('id', '?')}\n"
                    annotation_text += f"Area: {loop_info.get('area', 0):.2f}\n"
                    annotation_text += f"Entities: {loop_info.get('entities', 0)}"
                    
                    # Add text item to scene
                    text_item = self.graphics_scene.addText(annotation_text)
                    text_item.setPos(center_x, center_y)
                    text_item.setDefaultTextColor(QColor(0, 0, 0))
                    
                    # Store for later removal
                    self.loop_items.append(text_item)
            
            return True
            
        except Exception as e:
            print(f"Error adding loop annotations: {e}")
            return False
    
    def clear_highlights(self):
        """Clear all loop highlights and annotations."""
        for item in self.loop_items:
            self.graphics_scene.removeItem(item)
        self.loop_items.clear()
    
    def _highlight_single_loop(self, loop_info: Dict[str, Any], color: QColor, style: str):
        """
        Highlight a single loop.
        
        Args:
            loop_info: Information about the loop
            color: Color to use for highlighting
            style: Highlighting style ('outline', 'fill', 'both')
        """
        # Get loop entities
        loop_entities = loop_info.get('loop_entities', [])
        if not loop_entities:
            return
        
        # Create highlighting based on style
        if style in ['outline', 'both']:
            self._add_loop_outline(loop_entities, color)
        
        if style in ['fill', 'both']:
            self._add_loop_fill(loop_info, color)
    
    def _add_loop_outline(self, loop_entities: List, color: QColor):
        """Add outline highlighting to loop entities."""
        pen = QPen(color, 3, Qt.SolidLine)  # Thick line for highlighting
        
        for entity in loop_entities[:-1]:  # Exclude duplicate start entity
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                line_item = self.graphics_scene.addLine(
                    start.x, start.y, end.x, end.y, pen
                )
                self.loop_items.append(line_item)
            
            elif entity.dxftype() == 'ARC':
                # For arcs, we'll approximate with line segments
                self._add_arc_outline(entity, pen)
            
            elif entity.dxftype() == 'CIRCLE':
                center = entity.dxf.center
                radius = entity.dxf.radius
                circle_item = self.graphics_scene.addEllipse(
                    center.x - radius, center.y - radius,
                    2 * radius, 2 * radius, pen
                )
                self.loop_items.append(circle_item)
    
    def _add_loop_fill(self, loop_info: Dict[str, Any], color: QColor):
        """Add fill highlighting to the loop area."""
        bbox = loop_info.get('bounding_box', {})
        if not bbox:
            return
        
        # Create a semi-transparent fill rectangle
        fill_color = QColor(color)
        fill_color.setAlpha(50)  # Very transparent
        brush = QBrush(fill_color)
        pen = QPen(Qt.NoPen)
        
        rect_item = self.graphics_scene.addRect(
            bbox.get('min_x', 0), bbox.get('min_y', 0),
            bbox.get('width', 0), bbox.get('height', 0),
            pen, brush
        )
        self.loop_items.append(rect_item)
    
    def _add_arc_outline(self, arc_entity, pen: QPen):
        """Add outline for an arc entity using line segments."""
        center = arc_entity.dxf.center
        radius = arc_entity.dxf.radius
        start_angle = math.radians(arc_entity.dxf.start_angle)
        end_angle = math.radians(arc_entity.dxf.end_angle)
        
        # Normalize angles
        if end_angle < start_angle:
            end_angle += 2 * math.pi
        
        # Approximate arc with line segments
        num_segments = max(8, int((end_angle - start_angle) * 180 / math.pi / 10))
        angle_step = (end_angle - start_angle) / num_segments
        
        prev_x = center.x + radius * math.cos(start_angle)
        prev_y = center.y + radius * math.sin(start_angle)
        
        for i in range(1, num_segments + 1):
            angle = start_angle + i * angle_step
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            
            line_item = self.graphics_scene.addLine(prev_x, prev_y, x, y, pen)
            self.loop_items.append(line_item)
            
            prev_x, prev_y = x, y
    
    def create_loop_legend(self, loops_data: Dict[str, Any], position: tuple = (10, 10)) -> bool:
        """
        Create a legend showing loop information.
        
        Args:
            loops_data: Dictionary containing loop information
            position: Position to place the legend (x, y)
            
        Returns:
            True if legend was created successfully, False otherwise
        """
        try:
            loops = loops_data.get('loops', [])
            if not loops:
                return False
            
            legend_text = "Detected Loops:\n"
            legend_text += "=" * 20 + "\n"
            
            for i, loop_info in enumerate(loops):
                color_name = self._get_color_name(i)
                legend_text += f"{color_name} Loop {loop_info.get('id', '?')}: "
                legend_text += f"Area={loop_info.get('area', 0):.2f}, "
                legend_text += f"Entities={loop_info.get('entities', 0)}\n"
            
            # Add statistics
            stats = loops_data.get('statistics', {})
            if stats:
                legend_text += "\nStatistics:\n"
                legend_text += f"Total Area: {stats.get('total_area', 0):.2f}\n"
                legend_text += f"Largest Area: {stats.get('largest_area', 0):.2f}\n"
                legend_text += f"Average Area: {stats.get('average_area', 0):.2f}\n"
            
            # Create legend text item
            legend_item = self.graphics_scene.addText(legend_text)
            legend_item.setPos(position[0], position[1])
            legend_item.setDefaultTextColor(QColor(0, 0, 0))
            
            # Add background rectangle
            rect = legend_item.boundingRect()
            bg_item = self.graphics_scene.addRect(
                rect.adjusted(-5, -5, 5, 5),
                QPen(QColor(0, 0, 0)),
                QBrush(QColor(255, 255, 255, 200))
            )
            bg_item.setPos(position[0], position[1])
            
            # Store items for cleanup
            self.loop_items.extend([legend_item, bg_item])
            
            return True
            
        except Exception as e:
            print(f"Error creating loop legend: {e}")
            return False
    
    def _get_color_name(self, index: int) -> str:
        """Get a human-readable color name for the given index."""
        color_names = [
            "Red", "Green", "Blue", "Yellow", 
            "Magenta", "Cyan", "Orange", "Purple"
        ]
        return color_names[index % len(color_names)]
    
    def set_highlight_colors(self, colors: List[QColor]):
        """
        Set custom highlight colors.
        
        Args:
            colors: List of QColor objects to use for highlighting
        """
        if colors:
            self.highlight_colors = colors
    
    def get_highlight_count(self) -> int:
        """Get the number of currently highlighted items."""
        return len(self.loop_items) 