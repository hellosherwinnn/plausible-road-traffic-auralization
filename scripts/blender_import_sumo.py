"""Import SUMO road lanes and polygons into Blender as simple mesh geometry.

Run inside Blender's Python environment:
blender --python scripts/blender_import_sumo.py -- path/to/osm.net.xml path/to/osm.poly.xml
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET

import bpy


def import_lanes(net_xml: str) -> None:
    root = ET.parse(net_xml).getroot()
    for edge in root.findall("edge"):
        edge_id = edge.get("id", "edge")
        for lane in edge.findall("lane"):
            shape = lane.get("shape")
            if not shape:
                continue
            vertices = [(*map(float, point.split(",")), 0.0) for point in shape.split()]
            mesh = bpy.data.meshes.new(edge_id)
            obj = bpy.data.objects.new(edge_id, mesh)
            bpy.context.collection.objects.link(obj)
            mesh.from_pydata(vertices, [(i, i + 1) for i in range(len(vertices) - 1)], [])
            mesh.update()


def import_polygons(poly_xml: str, limit: int | None = None) -> None:
    root = ET.parse(poly_xml).getroot()
    polygons = root.findall("poly")
    for polygon in polygons[:limit]:
        shape = polygon.get("shape")
        if not shape:
            continue
        vertices = [(*map(float, point.split(",")), 0.0) for point in shape.split()]
        mesh = bpy.data.meshes.new(polygon.get("id", "poly"))
        obj = bpy.data.objects.new(polygon.get("id", "poly"), mesh)
        bpy.context.collection.objects.link(obj)
        mesh.from_pydata(vertices, [(i, (i + 1) % len(vertices)) for i in range(len(vertices))], [list(range(len(vertices)))])
        mesh.update()


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) < 1:
        raise SystemExit("Usage: blender --python scripts/blender_import_sumo.py -- osm.net.xml [osm.poly.xml]")
    import_lanes(args[0])
    if len(args) > 1:
        import_polygons(args[1])
    bpy.context.view_layer.update()


if __name__ == "__main__":
    main()
