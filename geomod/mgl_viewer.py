import math
import numpy as np
import moderngl
import moderngl_window as mglw
from pyrr import Matrix44, Vector3
from half_edge import Mesh
from subdivisions import midpoint_subdivide
import logging
import os

logger = logging.getLogger("mgl_viewer")
from queue import Queue
import threading
import sys


VERTEX_SHADER = """
#version 330
in vec3 in_position;
uniform mat4 mvp;
void main() {
    gl_Position = mvp * vec4(in_position, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330
out vec4 f_color;
void main() {
    f_color = vec4(1.0, 1.0, 1.0, 1.0);
}
"""


class SubdivWindow(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Subdivision (moderngl)"
    resource_dir = '.'

    def __init__(self, **kwargs):
        # WindowConfig will instantiate this class and provide window kwargs.
        # The moderngl context is created by the framework, so we must not
        # require external ctx at construction. Read mesh_path from a class
        # attribute if provided by the caller via `run()` below.
        super().__init__(**kwargs)
        self.mesh_path = getattr(self.__class__, 'mesh_path', kwargs.get('mesh_path', 'objects/cube.obj'))
        self.original_mesh = Mesh.load_obj(self.mesh_path)
        self.mesh = self.original_mesh
        self.level = 0
        self.method = getattr(self.__class__, 'method', 'midpoint')

        self.prog = self.ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)
        self.mvp = self.prog['mvp']

        self.vbo = None
        self.vao = None
        self._build_buffers()

        self.camera_distance = 4.0
        self.pitch = 0.0
        self.yaw = 0.0
        # target point the camera orbits around (mesh centroid)
        self.target = Vector3([0.0, 0.0, 0.0])
        # rotation/zoom sensitivities
        self.rotate_sensitivity = 0.3
        self.zoom_sensitivity = 0.25
        # min/max distance to avoid going through the object or too far away
        self.min_distance = 0.5
        self.max_distance = 200.0
        # initialize target and camera distance based on mesh
        self._update_camera_for_mesh()
        # orbiting (automatic rotation) state
        self.orbiting = False
        # degrees per second
        self.orbit_speed = 25.0
        self.mouse_last = None
        logger.info(f"SubdivWindow initialized. mesh_path={self.mesh_path} tris={len(self.mesh.faces)} verts={len(self.mesh.vertices)}")
        # register instance for external control (stdin thread)
        try:
            self.__class__._instance = self
        except Exception:
            pass
        # Try to focus the underlying window (may help event delivery)
        try:
            win = getattr(self, 'wnd', None)
            if win is not None and hasattr(win, '_window'):
                _w = win._window
                if hasattr(_w, 'activate'):
                    _w.activate()
                if hasattr(_w, 'set_focus'):
                    try:
                        _w.set_focus(True)
                    except Exception:
                        pass
        except Exception:
            pass

    def _build_buffers(self):
        # build line segments from mesh
        faces = self.mesh.to_face_indices()
        verts = [v.pos for v in self.mesh.vertices]
        edges = set()
        for a, b, c in faces:
            edges.add(tuple(sorted((a, b))))
            edges.add(tuple(sorted((b, c))))
            edges.add(tuple(sorted((c, a))))

        lines = []
        for i, j in edges:
            xa, ya, za = verts[i]
            xb, yb, zb = verts[j]
            lines.extend([xa, ya, za, xb, yb, zb])

        data = np.array(lines, dtype='f4') if lines else np.array([], dtype='f4')
        if self.vbo:
            self.vbo.release()
        if self.vao:
            self.vao.release()

        self.vbo = self.ctx.buffer(data.tobytes())
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, '3f', 'in_position')])
        self.line_count = len(data) // 3
        logger.info(f"Built buffers: line_count={self.line_count} vertices={len(self.mesh.vertices)} faces={len(self.mesh.faces)}")
        # update camera target when geometry changes
        try:
            self._update_camera_for_mesh()
        except Exception:
            pass

    def _update_camera_for_mesh(self):
        """Compute mesh centroid and a sensible camera distance based on bbox."""
        verts = [v.pos for v in self.mesh.vertices]
        if not verts:
            self.target = Vector3([0.0, 0.0, 0.0])
            return
        arr = np.array(verts, dtype='f4')
        centroid = arr.mean(axis=0)
        self.target = Vector3(centroid.tolist())
        # bounding box size
        mins = arr.min(axis=0)
        maxs = arr.max(axis=0)
        diag = np.linalg.norm(maxs - mins)
        # choose a camera distance proportionate to object size
        if diag > 0:
            self.camera_distance = max(self.camera_distance, float(diag) * 1.8)
        # clamp distance
        self.camera_distance = float(max(self.min_distance, min(self.camera_distance, self.max_distance)))

    def render(self, time, frame_time):
        # Process any terminal commands queued by the stdin reader thread
        try:
            q = getattr(self.__class__, '_cmd_queue', None)
            while q is not None and not q.empty():
                cmd = q.get_nowait().strip().lower()
                if not cmd:
                    continue
                logger.info(f"Received stdin command: {cmd}")
                if cmd in ('s', 'sub', 'subdivide'):
                    if self.level < 3:
                        if getattr(self, 'method', 'midpoint') == 'midpoint':
                            self.mesh = midpoint_subdivide(self.mesh)
                        elif self.method == 'loop':
                            from subdivisions import loop_subdivide
                            self.mesh = loop_subdivide(self.mesh)
                        elif self.method == 'butterfly':
                            from subdivisions import butterfly_subdivide
                            self.mesh = butterfly_subdivide(self.mesh)
                        else:
                            self.mesh = midpoint_subdivide(self.mesh)
                        self.level += 1
                        self._build_buffers()
                        logger.info(f"Subdivided to level {self.level} using {self.method}")
                elif cmd in ('r', 'reset'):
                    self.mesh = self.original_mesh
                    self.level = 0
                    self._build_buffers()
                    logger.info("Reset mesh")
                elif cmd.startswith('method'):
                    parts = cmd.split()
                    if len(parts) > 1:
                        m = parts[1]
                        if m in ('midpoint', 'loop', 'butterfly'):
                            self.method = m
                            logger.info(f"Switched subdivision method to {m}")
                        else:
                            logger.info(f"Unknown method '{m}' (valid: midpoint, loop, butterfly)")
                elif cmd.startswith('rot') or cmd.startswith('rotate'):
                    parts = cmd.split()
                    if len(parts) >= 3:
                        try:
                            dx = float(parts[1])
                            dy = float(parts[2])
                            self.yaw += dx
                            self.pitch += dy
                            logger.info(f"Rotated yaw={self.yaw:.2f} pitch={self.pitch:.2f}")
                        except Exception:
                            logger.info("Failed to parse rot command; use: rot dx dy")
                elif cmd.startswith('yaw'):
                    try:
                        self.yaw += float(cmd.split()[1])
                        logger.info(f"Yaw now {self.yaw}")
                    except Exception:
                        pass
                elif cmd.startswith('pitch'):
                    try:
                        self.pitch += float(cmd.split()[1])
                        logger.info(f"Pitch now {self.pitch}")
                    except Exception:
                        pass
                elif cmd.startswith('zoom'):
                    try:
                        val = float(cmd.split()[1])
                        self.camera_distance += val
                        logger.info(f"Camera distance now {self.camera_distance}")
                    except Exception:
                        pass
                elif cmd.startswith('load'):
                    parts = cmd.split(maxsplit=1)
                    if len(parts) > 1:
                        name = parts[1].strip()
                        obj_map = getattr(self.__class__, '_object_map', {})
                        # allow direct path too
                        path = obj_map.get(name) or (name if name.endswith('.obj') else None)
                        if path is None:
                            # try name as filename in objects dir
                            od = getattr(self.__class__, '_object_map', {})
                            if name in od:
                                path = od[name]
                        logger.info(f"Resolved load name='{name}' -> path={path}")
                        if path and os.path.isfile(path):
                            try:
                                logger.info(f"Loading object: {path}")
                                self.original_mesh = Mesh.load_obj(path)
                                self.mesh = self.original_mesh
                                self.level = 0
                                self._build_buffers()
                                # remember current object name for UI
                                self.current_object = name
                                logger.info(f"Loaded {path} (as '{name}')")
                                print(f"Loaded object: {name}", flush=True)
                            except Exception as e:
                                logger.exception(f"Failed to load {path}: {e}")
                                print(f"Failed to load {name}: {e}", flush=True)
                        else:
                            logger.info(f"Unknown object '{name}' (not found in objects/)")
                            print(f"Unknown object: {name}", flush=True)
                elif cmd.startswith('orbit'):
                    parts = cmd.split()
                    # 'orbit' toggles
                    if len(parts) == 1:
                        self.orbiting = not getattr(self, 'orbiting', False)
                    else:
                        op = parts[1].lower()
                        if op in ('start', 'on'):
                            self.orbiting = True
                        elif op in ('stop', 'off'):
                            self.orbiting = False
                        elif op in ('toggle',):
                            self.orbiting = not getattr(self, 'orbiting', False)
                        elif op == 'speed' and len(parts) > 2:
                            try:
                                self.orbit_speed = float(parts[2])
                            except Exception:
                                pass
                        else:
                            # maybe a numeric speed was provided directly
                            try:
                                self.orbit_speed = float(op)
                                self.orbiting = True
                            except Exception:
                                pass
                    logger.info(f"Orbiting={'ON' if self.orbiting else 'OFF'} speed={self.orbit_speed}")
                    print(f"Orbiting={'ON' if self.orbiting else 'OFF'} speed={self.orbit_speed}", flush=True)
                elif cmd in ('q', 'quit', 'exit'):
                    logger.info("Quit command received, closing window")
                    try:
                        self.wnd.close()
                    except Exception:
                        try:
                            os._exit(0)
                        except Exception:
                            pass
        except Exception:
            logger.exception("Error processing stdin commands")

        self.ctx.clear(0.2, 0.2, 0.2)
        self.ctx.enable(moderngl.DEPTH_TEST)

        # automatic orbit: advance yaw when orbiting
        try:
            if getattr(self, 'orbiting', False):
                # orbit_speed is in degrees/sec; frame_time is seconds for this frame
                self.yaw += float(self.orbit_speed) * float(frame_time)
        except Exception:
            pass

        proj = Matrix44.perspective_projection(45.0, self.wnd.aspect_ratio, 0.01, 1000.0)
        # Orbit camera around self.target using spherical coordinates
        # clamp pitch to avoid flipping
        self.pitch = max(-89.0, min(89.0, self.pitch))
        # convert to radians
        yaw_r = math.radians(self.yaw)
        pitch_r = math.radians(self.pitch)
        r = max(self.min_distance, min(self.camera_distance, self.max_distance))
        # spherical -> cartesian (note: y is up)
        cx = r * math.cos(pitch_r) * math.sin(yaw_r)
        cy = r * math.sin(pitch_r)
        cz = r * math.cos(pitch_r) * math.cos(yaw_r)
        cam_pos = Vector3([self.target.x + cx, self.target.y + cy, self.target.z + cz])
        view = Matrix44.look_at(cam_pos, self.target, Vector3([0.0, 1.0, 0.0]))

        mvp = proj * view
        self.mvp.write(mvp.astype('f4').tobytes())

        if self.line_count > 0:
            self.vao.render(mode=moderngl.LINES)
        # log frame occasionally
        if int(time) % 5 == 0:
            logger.debug(f"render time={time:.2f} frame_time={frame_time:.4f} line_count={self.line_count}")

    # moderngl-window expects on_render to be implemented; forward to render
    def on_render(self, time: float, frame_time: float):
        return self.render(time, frame_time)

    # input handling
    def mouse_drag_event(self, x, y, dx, dy):
        # dx, dy are in pixels; map to degrees (sensitivity applied)
        self.yaw += dx * self.rotate_sensitivity
        # invert pitch change so dragging up looks up
        self.pitch += -dy * self.rotate_sensitivity
        # debug
        try:
            logger.info(f"mouse_drag_event dx={dx} dy={dy} yaw={self.yaw:.2f} pitch={self.pitch:.2f}")
        except Exception:
            pass
        # request redraw
        try:
            self.wnd.update()
        except Exception:
            pass

    # additional event hooks to increase compatibility with backends
    def mouse_position_event(self, x, y, dx, dy):
        # movement without button pressed
        try:
            print(f"mouse_position_event x={x} y={y} dx={dx} dy={dy}", flush=True)
        except Exception:
            pass
        try:
            self.wnd.update()
        except Exception:
            pass

    # pyglet-style handlers (some backends call these names directly)
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers=None):
        try:
            logger.info(f"on_mouse_drag dx={dx} dy={dy} buttons={buttons}")
        except Exception:
            pass
        self.mouse_drag_event(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers=None):
        try:
            logger.info(f"on_mouse_press x={x} y={y} button={button}")
        except Exception:
            pass
        self.mouse_press_event(x, y, button)

    def on_mouse_release(self, x, y, button, modifiers=None):
        try:
            logger.info(f"on_mouse_release x={x} y={y} button={button}")
        except Exception:
            pass
        self.mouse_release_event(x, y, button)

    def on_mouse_scroll(self, x, y, sx, sy):
        try:
            logger.info(f"on_mouse_scroll x={x} y={y} sx={sx} sy={sy}")
        except Exception:
            pass
        self.mouse_scroll_event(x, y, sx, sy)

    def on_key_press(self, symbol, modifiers):
        # Try to map pyglet key symbols to our key_event handling
        try:
            import pyglet
            S_sym = getattr(pyglet.window.key, 'S', None)
            R_sym = getattr(pyglet.window.key, 'R', None)
        except Exception:
            S_sym = None
            R_sym = None
        # If symbol matches S or R, call key_event with a synthetic ACTION_PRESS
        try:
            if symbol == S_sym or symbol == ord('s') or symbol == ord('S'):
                # call subdivide
                self.key_event(getattr(mglw.keys, 'S', 'S'), getattr(mglw.keys, 'ACTION_PRESS', 1), None)
            elif symbol == R_sym or symbol == ord('r') or symbol == ord('R'):
                self.key_event(getattr(mglw.keys, 'R', 'R'), getattr(mglw.keys, 'ACTION_PRESS', 1), None)
            else:
                # forward generic
                self.key_event(symbol, getattr(mglw.keys, 'ACTION_PRESS', 1), modifiers)
        except Exception:
            pass

    def mouse_press_event(self, x, y, button):
        try:
            print(f"mouse_press_event x={x} y={y} button={button}", flush=True)
        except Exception:
            pass

    def mouse_release_event(self, x, y, button):
        try:
            print(f"mouse_release_event x={x} y={y} button={button}", flush=True)
        except Exception:
            pass

    def mouse_scroll_event(self, x, y, sx, sy):
        try:
            # sy positive usually means scroll up -> zoom in
            # use exponential zoom for nicer feel
            delta = -sy * self.zoom_sensitivity
            # multiplicative zoom
            factor = math.pow(1.1, delta)
            self.camera_distance *= factor
            # clamp
            self.camera_distance = max(self.min_distance, min(self.camera_distance, self.max_distance))
            logger.info(f"mouse_scroll zoom sy={sy} camera_distance={self.camera_distance:.3f}")
            try:
                self.wnd.update()
            except Exception:
                pass
        except Exception:
            pass

    def key_event(self, key, action, modifiers):
        keys = mglw.keys
        if action == keys.ACTION_PRESS:
            # debug
            try:
                logger.info(f"key_event key={key} action={action} modifiers={modifiers}")
            except Exception:
                pass
            if key == keys.S:
                # subdivide
                if self.level < 3:
                    self.mesh = midpoint_subdivide(self.mesh)
                    self.level += 1
                    self._build_buffers()
                    logger.info(f"Subdivided to level {self.level}")
                    try:
                        self.wnd.update()
                    except Exception:
                        pass
            elif key == keys.R:
                self.mesh = self.original_mesh
                self.level = 0
                self._build_buffers()
                logger.info("Reset mesh")
                try:
                    self.wnd.update()
                except Exception:
                    pass


def run(mesh_path: str = 'objects/cube.obj'):
    # Set class attributes so the WindowConfig can pick them up when the
    # framework instantiates the window (do NOT instantiate the class
    # yourself, that leads to ctx=None errors).
    SubdivWindow.mesh_path = mesh_path
    SubdivWindow.window_size = (800, 600)
    SubdivWindow.title = 'Subdivision (moderngl)'
    # configure logging so our logger.info/debug calls are visible
    import logging, sys
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logger.info(f"Launching SubdivWindow with mesh_path={mesh_path}")
    # discover available objects in the objects/ folder
    import os
    objs_dir = os.path.join(os.path.dirname(__file__), 'objects')
    object_map = {}
    if os.path.isdir(objs_dir):
        for fn in sorted(os.listdir(objs_dir)):
            if fn.lower().endswith('.obj'):
                name = os.path.splitext(fn)[0]
                object_map[name] = os.path.join(objs_dir, fn)

    SubdivWindow._object_map = object_map

    helper = (
        "Commands (type and Enter): s/sub - subdivide | r/reset - reset | method <midpoint|loop|butterfly> | "
        "load <name> - load object from objects/ directory | rot dx dy - rotate view | yaw N | pitch N | zoom N | q/quit - exit"
    )
    # print helper to stdout so it's immediately visible in terminal
    print(helper, flush=True)
    logger.info(helper)
    # print available objects
    if object_map:
        print('\nAvailable objects:')
        for k, p in object_map.items():
            print(f"  {k} -> {p}")
        print('\nUse: load <name>')
        print('', flush=True)

    # create a queue and background thread to read stdin commands while the
    # moderngl-window main loop runs. Commands: s/sub/subdivide, r/reset, q/quit
    cmd_q = Queue()

    def stdin_reader(q: Queue):
        try:
            logger.info("stdin reader thread started; type 's' to subdivide, 'r' to reset, 'q' to quit")
            for line in sys.stdin:
                if not line:
                    continue
                q.put(line)
        except Exception as e:
            logger.info(f"stdin reader exiting: {e}")

    SubdivWindow._cmd_queue = cmd_q
    t = threading.Thread(target=stdin_reader, args=(cmd_q,), daemon=True)
    t.start()

    mglw.run_window_config(SubdivWindow)


if __name__ == '__main__':
    run()
