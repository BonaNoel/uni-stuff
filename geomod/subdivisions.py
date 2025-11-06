"""Simple subdivision utilities.

Provides a lightweight midpoint (triangle split into 4) subdivision that
operates by converting the half-edge mesh into positions+faces, creating
edge-midpoint vertices and rebuilding a new Mesh via Mesh.build_from_faces.
"""
from half_edge import Mesh
import numpy as np


def midpoint_subdivide(mesh: Mesh) -> Mesh:
    """Return a new Mesh subdivided by splitting each triangle into 4.

    This function is intentionally simple for a quick project demo.
    It preserves no vertex smoothing (pure topology + midpoint positions).
    """
    positions = [v.pos for v in mesh.vertices]
    faces = mesh.to_face_indices()

    # mapping undirected edge -> new midpoint index
    edge_mid = {}
    new_positions = list(positions)

    def midpoint(i, j):
        key = (min(i, j), max(i, j))
        if key in edge_mid:
            return edge_mid[key]
        xi, yi, zi = positions[i]
        xj, yj, zj = positions[j]
        m = ((xi + xj) / 2.0, (yi + yj) / 2.0, (zi + zj) / 2.0)
        idx = len(new_positions)
        new_positions.append(m)
        edge_mid[key] = idx
        return idx

    new_faces = []
    for a, b, c in faces:
        ab = midpoint(a, b)
        bc = midpoint(b, c)
        ca = midpoint(c, a)
        # four new triangles
        new_faces.append((a, ab, ca))
        new_faces.append((ab, b, bc))
        new_faces.append((ca, bc, c))
        new_faces.append((ab, bc, ca))

    return Mesh.build_from_faces(new_positions, new_faces)


def loop_subdivide(mesh: Mesh) -> Mesh:
    """Perform one iteration of Loop subdivision.

    This implementation follows the standard Loop scheme: topology is the
    same as midpoint subdivision (split each triangle into 4), but vertex
    and edge positions are smoothed using Loop weights.
    """
    positions = [v.pos for v in mesh.vertices]
    faces = mesh.to_face_indices()

    n_verts = len(positions)

    # build adjacency: neighbors set per vertex and edge opposite vertices
    neighbors = {i: set() for i in range(n_verts)}
    edge_opposites = {}  # (min,max) -> list of opposite vertex indices
    for a, b, c in faces:
        neighbors[a].update([b, c])
        neighbors[b].update([c, a])
        neighbors[c].update([a, b])

        for (i, j, opp) in ((a, b, c), (b, c, a), (c, a, b)):
            key = (min(i, j), max(i, j))
            edge_opposites.setdefault(key, []).append(opp)

    new_positions = [tuple(p) for p in positions]
    edge_mid = {}

    # compute new edge points with Loop rule
    for (i, j), opps in edge_opposites.items():
        pi = np.array(positions[i])
        pj = np.array(positions[j])
        if len(opps) == 2:
            p2 = np.array(positions[opps[0]])
            p3 = np.array(positions[opps[1]])
            newp = (3.0/8.0)*(pi + pj) + (1.0/8.0)*(p2 + p3)
        else:
            # boundary edge or non-manifold: fallback to midpoint
            newp = 0.5*(pi + pj)
        idx = len(new_positions)
        new_positions.append(tuple(newp.tolist()))
        edge_mid[(i, j)] = idx

    # compute new positions for old vertices
    for i in range(n_verts):
        P = np.array(positions[i])
        nbrs = list(neighbors[i])
        n = len(nbrs)
        # detect boundary: any incident edge with single opposite -> boundary
        is_boundary = False
        boundary_neighbors = []
        for j in nbrs:
            key = (min(i, j), max(i, j))
            if len(edge_opposites.get(key, [])) == 1:
                is_boundary = True
                boundary_neighbors.append(j)

        if is_boundary:
            # boundary vertex rule: new position = 3/4 * P + 1/8*(sum of two boundary neighbors)
            # ensure we pick at most two boundary neighbors
            bn = boundary_neighbors[:2]
            if len(bn) < 2:
                newp = P
            else:
                newp = (3.0/4.0)*P + (1.0/8.0)*(np.array(positions[bn[0]]) + np.array(positions[bn[1]]))
        else:
            if n == 0:
                newp = P
            else:
                if n == 3:
                    beta = 3.0/16.0
                else:
                    beta = 3.0/(8.0*n)
                sum_n = np.zeros(3, dtype=float)
                for j in nbrs:
                    sum_n += np.array(positions[j])
                newp = (1.0 - n*beta)*P + beta*sum_n

        new_positions[i] = tuple(newp.tolist())

    # rebuild faces with same midpoint connectivity as midpoint subdivision
    new_faces = []
    for a, b, c in faces:
        ia, ib, ic = a, b, c
        ab = edge_mid[(min(ia, ib), max(ia, ib))]
        bc = edge_mid[(min(ib, ic), max(ib, ic))]
        ca = edge_mid[(min(ic, ia), max(ic, ia))]
        new_faces.append((ia, ab, ca))
        new_faces.append((ab, ib, bc))
        new_faces.append((ca, bc, ic))
        new_faces.append((ab, bc, ca))

    return Mesh.build_from_faces(new_positions, new_faces)


def butterfly_subdivide(mesh: Mesh) -> Mesh:
    """A simple butterfly-like subdivision.

    This is a simplified/interpolatory variant: the new edge point for an
    interior edge uses the two opposite vertices but omits the farther ring
    correction terms (keeps implementation compact for a uni demo). For
    boundary edges we use the midpoint.
    """
    positions = [v.pos for v in mesh.vertices]
    faces = mesh.to_face_indices()

    edge_opposites = {}
    for a, b, c in faces:
        for (i, j, opp) in ((a, b, c), (b, c, a), (c, a, b)):
            key = (min(i, j), max(i, j))
            edge_opposites.setdefault(key, []).append(opp)

    new_positions = list(positions)
    edge_mid = {}

    for (i, j), opps in edge_opposites.items():
        pi = np.array(positions[i])
        pj = np.array(positions[j])
        if len(opps) == 2:
            p2 = np.array(positions[opps[0]])
            p3 = np.array(positions[opps[1]])
            # simplified butterfly: midpoint + 1/8*(p2+p3 - (pi+pj)/2)
            newp = 0.5*(pi + pj) + 0.125*(p2 + p3 - 0.5*(pi + pj))
        else:
            newp = 0.5*(pi + pj)
        idx = len(new_positions)
        new_positions.append(tuple(newp.tolist()))
        edge_mid[(i, j)] = idx

    new_faces = []
    for a, b, c in faces:
        ab = edge_mid[(min(a, b), max(a, b))]
        bc = edge_mid[(min(b, c), max(b, c))]
        ca = edge_mid[(min(c, a), max(c, a))]
        new_faces.append((a, ab, ca))
        new_faces.append((ab, b, bc))
        new_faces.append((ca, bc, c))
        new_faces.append((ab, bc, ca))

    return Mesh.build_from_faces(new_positions, new_faces)
