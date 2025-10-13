# test_gl.py
import pyglet
import moderngl

window = pyglet.window.Window(640, 480, "pyglet + moderngl test")

@window.event
def on_draw():
    # create moderngl context the first time we draw (after GL context exists)
    if not hasattr(window, "mctx"):
        window.mctx = moderngl.create_context()
        print("Created moderngl context:", window.mctx)
    window.clear()

pyglet.app.run()