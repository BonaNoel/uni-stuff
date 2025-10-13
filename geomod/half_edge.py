"""Minimal half-edge mesh implementation.

Conventions:
- HalfEdge.origin is the vertex the half-edge points from (i.e. origin).
- destination of a half-edge is he.next.origin
- vertex.halfedge points to an outgoing half-edge for that vertex (or None)
- boundary half-edges have .face is None; interior half-edges have a Face object.

This implementation provides a builder from position + face lists and a tiny OBJ
loader helper that extracts only vertex positions and face indices.
"""

class Vertex:
    __slots__ = ("pos", "halfedge", "index")

    def __init__(self, x, y, z, index=None):
        self.pos = (float(x), float(y), float(z))
        self.halfedge = None  # an outgoing halfedge (or boundary halfedge)
        self.index = index


class Face:
    __slots__ = ("halfedge",)

    def __init__(self, halfedge=None):
        self.halfedge = halfedge


class HalfEdge:
    __slots__ = ("origin", "twin", "next", "prev", "face")

    def __init__(self, origin=None):
        self.origin = origin
        self.twin = None
        self.next = None
        self.prev = None
        self.face = None


class Mesh:
    """Container for vertices, halfedges and faces."""

    def __init__(self):
        self.vertices = []    # list[Vertex]
        self.halfedges = []   # list[HalfEdge]
        self.faces = []       # list[Face]

    # ---------------------- builders ----------------------
    @classmethod
    def build_from_faces(cls, positions, faces):
        """Build a half-edge mesh from positions and triangular faces.

        positions: iterable of (x,y,z)
        faces: iterable of triples of vertex indices (0-based). Polygons should
               be triangulated before calling this.
        """
        mesh = cls()

        # create vertices
        for i, p in enumerate(positions):
            x, y, z = p
            mesh.vertices.append(Vertex(x, y, z, index=i))

        # create halfedges and faces for each triangle
        for tri in faces:
            if len(tri) != 3:
                raise ValueError("build_from_faces expects triangles (3 indices per face)")
            a, b, c = tri
            va = mesh.vertices[a]
            vb = mesh.vertices[b]
            vc = mesh.vertices[c]

            he_ab = HalfEdge(origin=va)
            he_bc = HalfEdge(origin=vb)
            he_ca = HalfEdge(origin=vc)

            # link next/prev in CCW order
            he_ab.next, he_ab.prev = he_bc, he_ca
            he_bc.next, he_bc.prev = he_ca, he_ab
            he_ca.next, he_ca.prev = he_ab, he_bc

            face = Face(halfedge=he_ab)
            he_ab.face = he_bc.face = he_ca.face = face

            mesh.halfedges.extend([he_ab, he_bc, he_ca])
            mesh.faces.append(face)

            # set a representative outgoing halfedge for each vertex
            if va.halfedge is None:
                va.halfedge = he_ab
            if vb.halfedge is None:
                vb.halfedge = he_bc
            if vc.halfedge is None:
                vc.halfedge = he_ca

        # build edge map to match twins
        edge_map = {}  # key: (min_i,max_i) -> list of (i,j,he)
        for he in mesh.halfedges:
            i = he.origin.index
            j = he.next.origin.index
            key = (min(i, j), max(i, j))
            edge_map.setdefault(key, []).append((i, j, he))

        # match twins and create boundary halfedges where needed
        boundary_halfedges = []
        for key, entries in edge_map.items():
            if len(entries) == 2:
                (i1, j1, he1), (i2, j2, he2) = entries
                # tie the twins (he1 should be i1->j1 and he2 should be j1->i1)
                he1.twin = he2
                he2.twin = he1
            elif len(entries) == 1:
                # boundary edge: create a boundary halfedge going opposite direction
                i, j, he_int = entries[0]  # he_int goes i -> j
                he_bnd = HalfEdge(origin=mesh.vertices[j])
                he_bnd.face = None
                he_bnd.twin = he_int
                he_int.twin = he_bnd
                mesh.halfedges.append(he_bnd)
                boundary_halfedges.append(he_bnd)
                # ensure vertex has a halfedge
                if he_bnd.origin.halfedge is None:
                    he_bnd.origin.halfedge = he_bnd
            else:
                raise ValueError(f"Non-manifold edge {key} with {len(entries)} incident halfedges")

        # link boundary halfedges into loops so .next/.prev are defined
        if boundary_halfedges:
            # helper: find the next boundary halfedge for a given boundary halfedge
            for he in list(boundary_halfedges):
                # start from the interior twin of he and walk twin.next until we hit a boundary halfedge
                cur = he.twin.next
                # cur should be an interior halfedge; advance around vertex until we find a boundary
                loop_guard = 0
                while cur is not None and cur.face is not None:
                    cur = cur.twin.next
                    loop_guard += 1
                    if loop_guard > len(mesh.halfedges) * 2:
                        raise RuntimeError("Boundary linking failed (possible inconsistent mesh)")
                if cur is None:
                    raise RuntimeError("Could not link boundary halfedge; found None during traversal")
                # cur is the boundary halfedge that follows he along the boundary
                he.next = cur
                cur.prev = he

        return mesh

    @classmethod
    def load_obj(cls, path):
        """Load an OBJ file and build a half-edge mesh.

        Only supports 'v' and 'f' lines. Faces with >3 vertices are fan-triangulated.
        Negative indices are supported.
        """
        positions = []
        faces = []
        with open(path, 'r') as fh:
            for line in fh:
                if not line.strip() or line.startswith('#'):
                    continue
                parts = line.split()
                if parts[0] == 'v':
                    x, y, z = parts[1:4]
                    positions.append((float(x), float(y), float(z)))
                elif parts[0] == 'f':
                    idxs = []
                    for tok in parts[1:]:
                        v_str = tok.split('/')[0]
                        idx = int(v_str)
                        if idx < 0:
                            idx = len(positions) + idx
                        else:
                            idx = idx - 1
                        idxs.append(idx)
                    # triangulate fan
                    for i in range(1, len(idxs) - 1):
                        faces.append((idxs[0], idxs[i], idxs[i + 1]))

        return cls.build_from_faces(positions, faces)

    # ---------------------- utilities ----------------------
    def face_vertices(self, face):
        """Return the list of Vertex objects for the given Face."""
        verts = []
        he0 = face.halfedge
        he = he0
        while True:
            verts.append(he.origin)
            he = he.next
            if he is None or he == he0:
                break
        return verts

    def to_face_indices(self):
        """Return list of triangle index triples (0-based) representing the mesh faces."""
        out = []
        for f in self.faces:
            he = f.halfedge
            a = he.origin.index
            b = he.next.origin.index
            c = he.next.next.origin.index
            out.append((a, b, c))
        return out

    def vertex_neighbors(self, v):
        """Return neighboring Vertex objects around vertex v (pass Vertex or index).

        Uses twin/next traversal: start = v.halfedge; iteratively do he = he.twin.next
        """
        if isinstance(v, int):
            v = self.vertices[v]
        start = v.halfedge
        if start is None:
            return []
        out = []
        he = start
        loop_guard = 0
        while True:
            out.append(he.next.origin)
            # advance to next outgoing halfedge
            if he.twin is None:
                break
            he = he.twin.next
            loop_guard += 1
            if he is None or he == start or loop_guard > len(self.halfedges) * 2:
                break
        return out

    def is_boundary_edge(self, he):
        """Return True if the given halfedge borders the boundary (its face is None or its twin.face is None)."""
        return he.face is None or (he.twin is not None and he.twin.face is None)
