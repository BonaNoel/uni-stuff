"""Minimal subdivision demo app.

Runs a small PyQt + OpenGL window that loads `objects/cube.obj` using the
existing `half_edge.Mesh` loader. It shows a wireframe and lets you apply a
simple midpoint subdivision up to 3 levels. This is intentionally minimal for
a quick uni project demo.
"""

import sys
import sys
from mgl_viewer import run


def main():
	mesh_path = 'objects/cube.obj'
	if len(sys.argv) > 1:
		mesh_path = sys.argv[1]
	run(mesh_path)


if __name__ == '__main__':
	main()


