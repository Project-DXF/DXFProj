from typing import Tuple, Optional, Dict, Any
import ezdxf
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.path import Path
import matplotlib.patches as patches
import math


class ImageAnalyzer:    
    def __init__(self):
        self.current_image = None
        self.current_features = None
        
    def load_image(self, image_path: str) -> bool:
        return True
            
    def _extract_features(self, image: np.ndarray) -> Dict[str, Any]:
        return {
            'area': 0.0,
            'perimeter': 0.0,
            'circularity': 0.0,
            'aspect_ratio': 0.0,
            'extent': 0.0,
            'centroid_x': 0.0,
            'centroid_y': 0.0,
            'hu_moments': np.zeros(7)
        }
        
    def compare_with_dxf(self, dxf_path: str) -> float:
        return 0.5
            
    def _get_dxf_bounds(self, modelspace) -> Optional[Tuple[float, float, float, float]]:
        try:
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for entity in modelspace:
                if entity.dxftype() == 'LINE':
                    start = entity.dxf.start
                    end = entity.dxf.end
                    min_x = min(min_x, start[0], end[0])
                    min_y = min(min_y, start[1], end[1])
                    max_x = max(max_x, start[0], end[0])
                    max_y = max(max_y, start[1], end[1])
                    
                elif entity.dxftype() == 'CIRCLE':
                    center = entity.dxf.center
                    radius = entity.dxf.radius
                    min_x = min(min_x, center[0] - radius)
                    min_y = min(min_y, center[1] - radius)
                    max_x = max(max_x, center[0] + radius)
                    max_y = max(max_y, center[1] + radius)
                    
                elif entity.dxftype() == 'ARC':
                    center = entity.dxf.center
                    radius = entity.dxf.radius
                    min_x = min(min_x, center[0] - radius)
                    min_y = min(min_y, center[1] - radius)
                    max_x = max(max_x, center[0] + radius)
                    max_y = max(max_y, center[1] + radius)
                    
                elif entity.dxftype() == 'LWPOLYLINE':
                    points = list(entity.get_points())
                    if points:
                        xs = [p[0] for p in points]
                        ys = [p[1] for p in points]
                        min_x = min(min_x, min(xs))
                        min_y = min(min_y, min(ys))
                        max_x = max(max_x, max(xs))
                        max_y = max(max_y, max(ys))
            
            if min_x != float('inf'):
                return (min_x, min_y, max_x, max_y)
            return None
            
        except Exception as e:
            print(f"Error getting DXF bounds: {str(e)}")
            return None
            
    def _dxf_to_image(self, dxf_path: str) -> Optional[np.ndarray]:
        try:
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()
            
            fig = plt.figure(figsize=(8, 8), dpi=100)
            ax = fig.add_subplot(111)
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for entity in msp:
                try:
                    if entity.dxftype() == 'LINE':
                        start = entity.dxf.start
                        end = entity.dxf.end
                        ax.plot([start[0], end[0]], [start[1], end[1]], 'k-', linewidth=1)
                        min_x = min(min_x, start[0], end[0])
                        min_y = min(min_y, start[1], end[1])
                        max_x = max(max_x, start[0], end[0])
                        max_y = max(max_y, start[1], end[1])
                        
                    elif entity.dxftype() == 'CIRCLE':
                        center = entity.dxf.center
                        radius = entity.dxf.radius
                        circle = plt.Circle(center, radius, fill=False, color='k', linewidth=1)
                        ax.add_patch(circle)
                        min_x = min(min_x, center[0] - radius)
                        min_y = min(min_y, center[1] - radius)
                        max_x = max(max_x, center[0] + radius)
                        max_y = max(max_y, center[1] + radius)
                        
                    elif entity.dxftype() == 'ARC':
                        center = entity.dxf.center
                        radius = entity.dxf.radius
                        start_angle = math.radians(entity.dxf.start_angle)
                        end_angle = math.radians(entity.dxf.end_angle)
                        if end_angle < start_angle:
                            end_angle += 2 * math.pi
                            
                        arc = patches.Arc(center, 2*radius, 2*radius,
                                        theta1=math.degrees(start_angle),
                                        theta2=math.degrees(end_angle),
                                        color='k', linewidth=1)
                        ax.add_patch(arc)
                        
                        angles = np.linspace(start_angle, end_angle, 100)
                        xs = center[0] + radius * np.cos(angles)
                        ys = center[1] + radius * np.sin(angles)
                        min_x = min(min_x, np.min(xs))
                        min_y = min(min_y, np.min(ys))
                        max_x = max(max_x, np.max(xs))
                        max_y = max(max_y, np.max(ys))
                        
                    elif entity.dxftype() == 'LWPOLYLINE':
                        points = list(entity.get_points())
                        if points:
                            xs = [p[0] for p in points]
                            ys = [p[1] for p in points]
                            
                            if getattr(entity, 'closed', False):
                                xs.append(xs[0])
                                ys.append(ys[0])
                            ax.plot(xs, ys, 'k-', linewidth=1)
                            
                            min_x = min(min_x, min(xs))
                            min_y = min(min_y, min(ys))
                            max_x = max(max_x, max(xs))
                            max_y = max(max_y, max(ys))
                            
                except Exception as e:
                    print(f"Error processing entity {entity.dxftype()}: {str(e)}")
                    continue
            
            if min_x == float('inf'):
                print("No entities found in DXF")
                return None
                
            padding = 0.1  # 10% padding
            width = max_x - min_x
            height = max_y - min_y
            min_x -= width * padding
            max_x += width * padding
            min_y -= height * padding
            max_y += height * padding
            
            ax.set_xlim(min_x, max_x)
            ax.set_ylim(min_y, max_y)
            
            ax.set_aspect('equal')
            ax.axis('off')
            
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            
            buf = canvas.buffer_rgba()
            image = np.asarray(buf)
            
            image = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140])
            
            image = 255 - image
            
            plt.close(fig)
            
            return image.astype(np.uint8)
            
        except Exception as e:
            print(f"Error converting DXF to image: {str(e)}")
            return None
            
    def _draw_line(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int):
        height, width = image.shape
        
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(0, min(x2, width - 1))
        y2 = max(0, min(y2, height - 1))
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        if dx == 0 and dy == 0:
            image[y1, x1] = 255
            return
            
        steep = dy > dx
        
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
            dx, dy = dy, dx
            width, height = height, width
        
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        
        error = dx // 2
        y = y1
        y_step = 1 if y1 < y2 else -1
        
        for x in range(x1, x2 + 1):
            if steep:
                if 0 <= y < width and 0 <= x < height:
                    image[x, y] = 255
            else:
                if 0 <= x < width and 0 <= y < height:
                    image[y, x] = 255
            
            error -= dy
            if error < 0:
                y += y_step
                error += dx
                
    def _plot(self, image: np.ndarray, x: int, y: int, color: int):
        height, width = image.shape
        if 0 <= x < width and 0 <= y < height:
            image[y, x] = color
        
    def _draw_circle(self, image: np.ndarray, cx: int, cy: int, radius: int):
        def plot_points(x, y):
            points = [
                (cx + x, cy + y), (cx - x, cy + y),
                (cx + x, cy - y), (cx - x, cy - y),
                (cx + y, cy + x), (cx - y, cy + x),
                (cx + y, cy - x), (cx - y, cy - x)
            ]
            for px, py in points:
                self._plot(image, px, py, 255)
        
        x = 0
        y = radius
        d = 1 - radius
        
        plot_points(x, y)
        
        while y > x:
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1
            plot_points(x, y)
            
    def _draw_arc(self, image: np.ndarray, cx: int, cy: int, radius: int, start_angle: float, end_angle: float):
        import math
        
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        if end_rad < start_rad:
            end_rad += 2 * math.pi
        
        num_segments = max(int(radius * 0.5), 36)
        angle_step = (end_rad - start_rad) / num_segments
        
        prev_x = None
        prev_y = None
        
        for i in range(num_segments + 1):
            angle = start_rad + i * angle_step
            x = int(cx + radius * math.cos(angle))
            y = int(cy + radius * math.sin(angle))
            
            if prev_x is not None:
                self._draw_line(image, prev_x, prev_y, x, y)
            
            prev_x = x
            prev_y = y
            
    def _compute_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        return 0.5 