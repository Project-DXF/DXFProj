import math
from ezdxf.entities import Line, Arc
from ezdxf.math import Vec2

def connect_segments(entities, tolerance=1e-3):
    """
    Connects broken or disconnected line and arc segments by adding lines between endpoints that are within a given tolerance.
    Args:
        entities: List of DXF entities (Line, Arc)
        tolerance: Maximum distance to consider two endpoints as connected
    Returns:
        List of original and new connecting Line entities
    """
    # Collect all endpoints
    endpoints = []  # (Vec2, entity, is_start)
    for ent in entities:
        if ent.dxftype() == 'LINE':
            start = Vec2(ent.dxf.start.x, ent.dxf.start.y)
            end = Vec2(ent.dxf.end.x, ent.dxf.end.y)
            endpoints.append((start, ent, True))
            endpoints.append((end, ent, False))
        elif ent.dxftype() == 'ARC':
            # For arcs, use start and end points
            arc = ent
            start_angle = math.radians(arc.dxf.start_angle)
            end_angle = math.radians(arc.dxf.end_angle)
            center = Vec2(arc.dxf.center.x, arc.dxf.center.y)
            radius = arc.dxf.radius
            start = center + Vec2(math.cos(start_angle), math.sin(start_angle)) * radius
            end = center + Vec2(math.cos(end_angle), math.sin(end_angle)) * radius
            endpoints.append((start, ent, True))
            endpoints.append((end, ent, False))
    # Find unconnected endpoints
    used = set()
    connections = []
    for i, (pt1, ent1, is_start1) in enumerate(endpoints):
        if i in used:
            continue
        min_dist = float('inf')
        min_j = None
        for j, (pt2, ent2, is_start2) in enumerate(endpoints):
            if i == j or j in used:
                continue
            dist = (pt1 - pt2).magnitude
            if dist < min_dist:
                min_dist = dist
                min_j = j
        if min_j is not None and min_dist < tolerance:
            used.add(i)
            used.add(min_j)
        else:
            # This endpoint is unconnected, try to find another unconnected endpoint to connect
            for j, (pt2, ent2, is_start2) in enumerate(endpoints):
                if i == j or j in used:
                    continue
                dist = (pt1 - pt2).magnitude
                if dist < 10 * tolerance:  # Allow a bit more for connecting
                    # Create a new line entity between pt1 and pt2
                    line = Line.new(dxfattribs={
                        'start': (pt1.x, pt1.y, 0),
                        'end': (pt2.x, pt2.y, 0),
                        'layer': ent1.dxf.layer if hasattr(ent1.dxf, 'layer') else '0',
                    })
                    connections.append(line)
                    used.add(i)
                    used.add(j)
                    break
    return list(entities) + connections
