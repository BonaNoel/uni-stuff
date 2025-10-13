# 1. read in from file (object file), it can be rotated to look around
# wiremesh is enough, surface rendering is extra

# 2. subdivide the mesh, at least 2 types (eg. loop, butterfly)

# 3. iterate with a press of a button, 3 levels is enough

# 4. use half-edge data structure

# use pyglet or moderngl

import pyglet
import moderngl



if __name__ == "__main__":
    window = pyglet.window.Window(800, 600, "3D Subdivision")
    vertices, faces = load_obj("path/to/your.obj")

    @window.event
    def on_draw():
        if not hasattr(window, "mctx"):
            window.mctx = moderngl.create_context()
            print("Created moderngl context:", window.mctx)
        window.clear()

    pyglet.app.run()