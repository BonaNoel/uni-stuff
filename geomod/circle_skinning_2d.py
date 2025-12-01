import pygame
import math

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)


center = True
center_pos = None
circles = []
show_helpers = True

class Circle:
    def __init__(self, center, r):
        self.center = center
        self.r = r



def compute_skinning(circles):
    # Step 1 Get touching points of circles
    touching_points = compute_touching_points(circles)
    # Step 2 separate right/left touching points
    left, right = compute_left_right(touching_points, circles)
    # Step 3 calculate tangent vectors for hermite splines
    left_tv, right_tv = compute_tangent_vectors(left, right, circles)
    # Step 4 draw the hermite splines
    draw_skins(left, right, left_tv, right_tv)

def draw_skins(left_points, right_points, left_tangents, right_tangents):
    """Sample cubic Hermite curves for left and right point chains and draw them.

    Returns (left_curve_points, right_curve_points) where each is a flat list
    of sampled 2D points (tuples).
    """
    def hermite_segment(p0, p1, v0, v1, steps=30):
        pts = []
        for i in range(steps + 1):
            t = i / float(steps)
            t2 = t * t
            t3 = t2 * t
            h30 = 2*t3 - 3*t2 + 1
            h31 = -2*t3 + 3*t2
            h32 = t3 - 2*t2 + t
            h33 = t3 - t2
            x = h30 * p0[0] + h31 * p1[0] + h32 * v0[0] + h33 * v1[0]
            y = h30 * p0[1] + h31 * p1[1] + h32 * v0[1] + h33 * v1[1]
            pts.append((x, y))
        return pts

    def hermite_chain(points, tangents, steps_per_seg=30):
        n = len(points)
        if n < 2:
            return []
        curve = []
        for i in range(n - 1):
            p0 = points[i]
            p1 = points[i+1]
            v0 = tangents[i]
            v1 = tangents[i+1]
            seg = hermite_segment(p0, p1, v0, v1, steps=steps_per_seg)
            # avoid duplicating the last point of a segment except for final
            if i < n - 2:
                curve.extend(seg[:-1])
            else:
                curve.extend(seg)
        return curve

    # sample density (you can change to between 20 and 50)
    steps = 30

    left_curve = hermite_chain(left_points, left_tangents, steps_per_seg=steps)
    right_curve = hermite_chain(right_points, right_tangents, steps_per_seg=steps)

    # draw curves
    if len(left_curve) > 1:
        pygame.draw.lines(screen, PURPLE, False, [(int(x), int(y)) for x,y in left_curve], 2)
    if len(right_curve) > 1:
        pygame.draw.lines(screen, CYAN, False, [(int(x), int(y)) for x,y in right_curve], 2)

    return left_curve, right_curve

def compute_tangent_vectors(left_points, right_points, circles):
    def compute_radical_line(c1, c2):
        x1, y1, r1 = c1.center[0], c1.center[1], c1.r
        x2, y2, r2 = c2.center[0], c2.center[1], c2.r

        A = 2 * (x2 - x1)
        B = 2 * (y2 - y1)
        C = x1**2 - x2**2 + y1**2 - y2**2 - r1**2 + r2**2

        return (A, B, C)

    def distance_point_to_line(A, B, C, point):
        x0, y0 = point
        denom = math.hypot(A, B)
        return 0.0 if denom == 0 else abs(A * x0 + B * y0 + C) / denom

    def vector_from_points(p1, p2):
        return (p2[0] - p1[0], p2[1] - p1[1])

    def norm(v):
        return math.hypot(v[0], v[1])

    def normalize(v):
        n = norm(v)
        return (v[0] / n, v[1] / n) if n != 0 else (0.0, 0.0)

    def dot(u, v):
        return u[0] * v[0] + u[1] * v[1]

    def tangent_unit(circle, p):
        # radial vector from center to point
        rx = p[0] - circle.center[0]
        ry = p[1] - circle.center[1]
        tx, ty = -ry, rx
        return normalize((tx, ty))

    n = len(circles)
    # accumulators of distances to radical lines for each touching point index
    left_dists = [[] for _ in range(n)]
    right_dists = [[] for _ in range(n)]

    # gather distances from each radical line (pair i,i+1)
    for i in range(n - 1):
        A, B, C = compute_radical_line(circles[i], circles[i+1])
        # left points distances
        d1_left = distance_point_to_line(A, B, C, left_points[i])
        d2_left = distance_point_to_line(A, B, C, left_points[i+1])
        left_dists[i].append(d1_left)
        left_dists[i+1].append(d2_left)
        # right points distances
        d1_right = distance_point_to_line(A, B, C, right_points[i])
        d2_right = distance_point_to_line(A, B, C, right_points[i+1])
        right_dists[i].append(d1_right)
        right_dists[i+1].append(d2_right)

    # compute final tangent vectors using averaged distances
    left_tv = [None] * n
    right_tv = [None] * n

    # helper to compute desired direction for orientation
    def desired_direction(points, idx):
        if idx < n - 1:
            d = vector_from_points(points[idx], points[idx + 1])
        else:
            d = vector_from_points(points[idx - 1], points[idx])
        if norm(d) == 0.0:
            # fallback to center-to-center direction if touching points coincide
            if idx < n - 1:
                d = vector_from_points(circles[idx].center, circles[idx + 1].center)
            else:
                d = vector_from_points(circles[idx - 1].center, circles[idx].center)
        return normalize(d)

    for i in range(n):
        # left
        if len(left_dists[i]) > 0:
            avg_d = sum(left_dists[i]) / len(left_dists[i])
            mag = 2.0 * avg_d
            t = tangent_unit(circles[i], left_points[i])
            des = desired_direction(left_points, i)
            if dot(t, des) < 0:
                t = (-t[0], -t[1])
            left_tv[i] = (t[0] * mag, t[1] * mag)
        else:
            left_tv[i] = (0.0, 0.0)

        # right
        if len(right_dists[i]) > 0:
            avg_d = sum(right_dists[i]) / len(right_dists[i])
            mag = 2.0 * avg_d
            t = tangent_unit(circles[i], right_points[i])
            des = desired_direction(right_points, i)
            if dot(t, des) < 0:
                t = (-t[0], -t[1])
            right_tv[i] = (t[0] * mag, t[1] * mag)
        else:
            right_tv[i] = (0.0, 0.0)

    # draw tangent vectors for debugging
    # for j in range(n):
    #     lp = left_points[j]
    #     rp = right_points[j]
    #     ltv = left_tv[j]
    #     rtv = right_tv[j]
    #     pygame.draw.line(screen, RED, (int(lp[0]), int(lp[1])), (int(lp[0] + ltv[0]), int(lp[1] + ltv[1])), 2)
    #     pygame.draw.line(screen, BLUE, (int(rp[0]), int(rp[1])), (int(rp[0] + rtv[0]), int(rp[1] + rtv[1])), 2)

    return left_tv, right_tv

def compute_left_right(touching_points, circles):

    def radical_center(c1, c2, c3):
        x1, y1, r1 = c1.center[0], c1.center[1], c1.r
        x2, y2, r2 = c2.center[0], c2.center[1], c2.r
        x3, y3, r3 = c3.center[0], c3.center[1], c3.r

        # Solve two radical lines: (x - x1)^2 + (y - y1)^2 - r1^2 = (x - x2)^2 + (y - y2)^2 - r2^2
        A1 = 2*(x2 - x1)
        B1 = 2*(y2 - y1)
        C1 = x1**2 - x2**2 + y1**2 - y2**2 - r1**2 + r2**2

        A2 = 2*(x3 - x2)
        B2 = 2*(y3 - y2)
        C2 = x2**2 - x3**2 + y2**2 - y3**2 - r2**2 + r3**2

        denom = A1*B2 - A2*B1
        if abs(denom) < 1e-10:
            return None  # collinear centers
        # We have the system: A1*x + B1*y + C1 = 0 and A2*x + B2*y + C2 = 0
        # Rewrite as A1*x + B1*y = -C1, A2*x + B2*y = -C2 and solve.
        D1 = -C1
        D2 = -C2
        x_r = (D1*B2 - D2*B1)/denom
        y_r = (A1*D2 - A2*D1)/denom
        return (x_r, y_r)

    def cross_product(v1, v2):
        return v1[0]*v2[1] - v1[1]*v2[0]
    
    def vector_from_points(p1, p2):
        return (p2[0] - p1[0], p2[1] - p1[1])

    left = []
    right = []

    '''Thus the separation can easily be computedby the following steps 
    (see notations of Fig. 7): if the vector oi−1oican be rotated tothe direction of
    vector oi−1oi+1by a positive angle (in counterclockwise direction, withless than 
    180◦) then the touching point being closer to the radical center riwill be inthe
    left group, i.e. will be denoted by pi. If the direction of rotation is opposite
    (as itis for the next circle in Fig. 7) then the touching point closer to the
    radical center ri+1is in the right group: ¯pi+1. Special attention must pay to the 
    ﬁrst and last circle as wellas for circles with collinear centers. In these cases 
    the vector oi−1oiis rotated to thedirection of oi−1piand the angle is similarly 
    measured and evaluated as above'''

    # First circle
    c1 = circles[0]
    c2 = circles[1]
    p1 = touching_points[0]
    p2 = touching_points[1]
    # compute vector o1o2
    v_o1_o2 = vector_from_points(c1.center, c2.center)
    # compute vector c1p1 and c1p2
    v_o1_p1 = vector_from_points(c1.center, p1)
    v_o1_p2 = vector_from_points(c1.center, p2)
    # compute cross products to determine rotation direction
    cross1 = cross_product(v_o1_o2, v_o1_p1)
    if cross1 > 0:
        left.append(p1)
        right.append(p2)
    else:
        left.append(p2)
        right.append(p1) 
    

    # Inner circles
    for i in range(1, len(circles) - 1):
        c_prev = circles[i-1]
        c_curr = circles[i]
        c_next = circles[i+1]
        p1 = touching_points[2*i]
        p2 = touching_points[2*i + 1]
        # compute radical center R
        R = radical_center(c_prev, c_curr, c_next)
        # compute vector o(prev)o(curr)
        v_op_oc = vector_from_points(c_prev.center, c_curr.center)
        # compute vector o(prev)o(next)
        v_op_on = vector_from_points(c_prev.center, c_next.center)
        # compute cross products to determine rotation direction
        crossc = cross_product(v_op_oc, v_op_on)
        # compute distance from R to p1 and p2
        d1 = math.hypot(p1[0] - R[0], p1[1] - R[1])
        d2 = math.hypot(p2[0] - R[0], p2[1] - R[1])
        if crossc > 0:
            # counterclockwise
            if d1 < d2:
                left.append(p1)
                right.append(p2)
            else:
                left.append(p2)
                right.append(p1)
        else:
            # clockwise
            if d1 < d2:
                right.append(p1)
                left.append(p2)
            else:
                right.append(p2)
                left.append(p1)

    # Last circle
    c_last_minus_1 = circles[-2]
    c_last = circles[-1]
    p1 = touching_points[-2]
    p2 = touching_points[-1]
    # compute vector o(n-1)o(n)
    v_onm1_on = vector_from_points(c_last_minus_1.center, c_last.center)
    # compute vector o(n)p1 and o(n)p2
    v_on_p1 = vector_from_points(c_last.center, p1)
    v_on_p2 = vector_from_points(c_last.center, p2)
    # compute cross products to determine rotation direction
    crossn = cross_product(v_onm1_on, v_on_p1)
    if crossn > 0:
        left.append(p1)
        right.append(p2)
    else:
        left.append(p2)
        right.append(p1)


    for i in range(len(left)):
        pygame.draw.circle(screen, BLUE, (int(left[i][0]), int(left[i][1])), 4)
        pygame.draw.circle(screen, GREEN, (int(right[i][0]), int(right[i][1])), 4)

    return left, right

def compute_touching_points(circles):
    
    def get_touching_point_from_external_tanget(c1, c2, asd=WHITE, toggle_helpers=False):
        # Calculate the touching point between two circles c1 and c2 with the help of tangent
        dx = c2.center[0] - c1.center[0]
        dy = c2.center[1] - c1.center[1]
        D = math.hypot(dx, dy)

        # Guard against degenerate or numerically unstable situations:
        # - If D == 0 (coincident centers) we cannot form tangents; return two reasonable points
        # - Clamp the argument to acos to [-1, 1] to avoid ValueError from floating point error
        if D == 0:
            # Return two opposite points on circle c1 as a fallback
            p1 = (c1.center[0] + c1.r, c1.center[1])
            p2 = (c1.center[0] - c1.r, c1.center[1])
            return p1, p2

        acos_arg = (c1.r - c2.r) / D
        # clamp to [-1, 1]
        if acos_arg > 1.0:
            acos_arg = 1.0
        elif acos_arg < -1.0:
            acos_arg = -1.0

        t_angle = math.acos(acos_arg)  # note: acos for external tangents
        c_angle = math.atan2(dy, dx)

        p1 = (c1.center[0] + c1.r * math.cos(c_angle + t_angle),
            c1.center[1] + c1.r * math.sin(c_angle + t_angle))

        p2 = (c1.center[0] + c1.r * math.cos(c_angle - t_angle),
            c1.center[1] + c1.r * math.sin(c_angle - t_angle))

        p3 = (c2.center[0] + c2.r * math.cos(c_angle + t_angle),
            c2.center[1] + c2.r * math.sin(c_angle + t_angle))

        p4 = (c2.center[0] + c2.r * math.cos(c_angle - t_angle),
            c2.center[1] + c2.r * math.sin(c_angle - t_angle))

        # draw the 2 tangent lines
        if toggle_helpers:
            pygame.draw.line(screen, asd, (int(p1[0]), int(p1[1])), (int(p3[0]), int(p3[1])), 1)
            pygame.draw.line(screen, asd, (int(p2[0]), int(p2[1])), (int(p4[0]), int(p4[1])), 1)

        return p1, p2

    def solveApollonius(c1, c2, c3, s1, s2, s3):
        '''
        >>> solveApollonius((0, 0, 1), (4, 0, 1), (2, 4, 2), 1,1,1)
        Circle(x=2.0, y=2.1, r=3.9)
        >>> solveApollonius((0, 0, 1), (4, 0, 1), (2, 4, 2), -1,-1,-1)
        Circle(x=2.0, y=0.8333333333333333, r=1.1666666666666667) 

        c1,c2,c3: (x,y,r) Circles
        s1,s2,s3: +1 or -1 for each circle it means inner or outer tangency for that circle 
        '''
        x1, y1, r1 = c1
        x2, y2, r2 = c2
        x3, y3, r3 = c3

        v11 = 2*x2 - 2*x1
        v12 = 2*y2 - 2*y1
        v13 = x1*x1 - x2*x2 + y1*y1 - y2*y2 - r1*r1 + r2*r2
        v14 = 2*s2*r2 - 2*s1*r1
    
        v21 = 2*x3 - 2*x2
        v22 = 2*y3 - 2*y2
        v23 = x2*x2 - x3*x3 + y2*y2 - y3*y3 - r2*r2 + r3*r3
        v24 = 2*s3*r3 - 2*s2*r2
    
        w12 = v12/v11
        w13 = v13/v11
        w14 = v14/v11
    
        w22 = v22/v21-w12
        w23 = v23/v21-w13
        w24 = v24/v21-w14
    
        P = -w23/w22
        Q = w24/w22
        M = -w12*P-w13
        N = w14 - w12*Q
    
        a = N*N + Q*Q - 1
        b = 2*M*N - 2*N*x1 + 2*P*Q - 2*Q*y1 + 2*s1*r1
        c = x1*x1 + M*M - 2*M*x1 + P*P + y1*y1 - 2*P*y1 - r1*r1
    
        # Find a root of a quadratic equation. This requires the circle centers not to be e.g. colinear
        
        D = b*b-4*a*c
        if D < 0:
            return None  # No real solution
        rs = (-b-math.sqrt(D))/(2*a)
    
        xs = M+N*rs
        ys = P+Q*rs
    
        return Circle((xs, ys), rs)

    def get_two_same_orientation_appolonius(c1, c2, c3):
        '''
        Returns all 8 Apollonius circles for the given three circles
        '''
        appollonius_circles = []
        # Historically we computed all 8 sign combinations; the user prefers
        # only the two uniform-orientation solutions (s1==s2==s3 == +1 or -1).
        for signs in ((1, 1, 1), (-1, -1, -1)):
            s1, s2, s3 = signs
            circle = solveApollonius(
                (c1.center[0], c1.center[1], c1.r),
                (c2.center[0], c2.center[1], c2.r),
                (c3.center[0], c3.center[1], c3.r),
                s1, s2, s3
            )
            if circle is not None:
                appollonius_circles.append((circle, signs))
        return appollonius_circles

    def radical_center(c1, c2, c3):
        x1, y1, r1 = c1.center[0], c1.center[1], c1.r
        x2, y2, r2 = c2.center[0], c2.center[1], c2.r
        x3, y3, r3 = c3.center[0], c3.center[1], c3.r

        # Solve two radical lines: (x - x1)^2 + (y - y1)^2 - r1^2 = (x - x2)^2 + (y - y2)^2 - r2^2
        A1 = 2*(x2 - x1)
        B1 = 2*(y2 - y1)
        C1 = x1**2 - x2**2 + y1**2 - y2**2 - r1**2 + r2**2

        A2 = 2*(x3 - x2)
        B2 = 2*(y3 - y2)
        C2 = x2**2 - x3**2 + y2**2 - y3**2 - r2**2 + r3**2

        denom = A1*B2 - A2*B1
        if abs(denom) < 1e-10:
            return None  # collinear centers
        # We have the system: A1*x + B1*y + C1 = 0 and A2*x + B2*y + C2 = 0
        # Rewrite as A1*x + B1*y = -C1, A2*x + B2*y = -C2 and solve.
        D1 = -C1
        D2 = -C2
        x_r = (D1*B2 - D2*B1)/denom
        y_r = (A1*D2 - A2*D1)/denom
        return (x_r, y_r)
   

    def get_closest_point_on_circle_to_circle(C1, C2):
        # calculate the line computed by the 2 centers
        dx = C2.center[0] - C1.center[0]
        dy = C2.center[1] - C1.center[1]
        D = math.hypot(dx, dy)
        if D == 0:
            # coincident centers, return arbitrary point on C1
            return (C1.center[0] + C1.r, C1.center[1])
        
        # Calculate both points on C1 which the line intersects
        ux = dx / D
        uy = dy / D
        p1 = (C1.center[0] + C1.r * ux, C1.center[1] + C1.r * uy)
        p2 = (C1.center[0] - C1.r * ux, C1.center[1] - C1.r * uy)

        #pygame.draw.circle(screen, WHITE, (int(p1[0]), int(p1[1])), 5)
        #pygame.draw.circle(screen, WHITE, (int(p2[0]), int(p2[1])), 5)
        
        # Now determine which point is closest to both circles circumference
        # Not by teh distance from center but from circumference
        d1 = abs(math.hypot(p1[0] - C2.center[0], p1[1] - C2.center[1]) - C2.r)
        d2 = abs(math.hypot(p2[0] - C2.center[0], p2[1] - C2.center[1]) - C2.r)
        if d1 < d2:
            return p1
        else:
            return p2

    touching_points = []
    # Calculate touching point for first circle with c1,c2
    result = get_touching_point_from_external_tanget(circles[0], circles[1])
    touching_points.append(result[0])
    touching_points.append(result[1])
    

    # Calculate touching point for ci from ci-1 and ci+1 with appollonius circle
    if len(circles) >= 3:
        for i in range(1, len(circles) - 1):
            chosen_points = []
            # generate all Appollonius circles for ci
            #R = radical_center(circles[i-1], circles[i], circles[i+1])
            #print("Radical center: ", R)
            #if R is not None:
                #pygame.draw.circle(screen, WHITE, (int(R[0]), int(R[1])), 5)
            Appollonius_circles = get_two_same_orientation_appolonius(circles[i-1], circles[i], circles[i+1])
            # First filter by orientation: keep only Apollonius solutions whose sign
            # triple (s1,s2,s3) is uniform (all +1 or all -1). This matches the
            # paper's observation that the two solutions where all three given
            # circles have the same orientation provide the desired touching points.
            for item in Appollonius_circles:
                ac, signs = item
                if ac is None:
                    continue
                #pygame.draw.circle(screen, BLUE, (int(ac.center[0]), int(ac.center[1])), max(1, int(ac.r)), 2)
                # now calculate closest point on circle[i] to ac 
                point = get_closest_point_on_circle_to_circle(circles[i], ac)
                #print("Touching points from Apollonius circle: ", point)
                touching_points.append(point)
                
    # Calculate touching point for last circle with cn-1,cn   
    result = get_touching_point_from_external_tanget(circles[-1], circles[-2])
    touching_points.append(result[0])
    touching_points.append(result[1])

    print("Touching points number: ", len(touching_points))
    # Show touching points with green dots
    #for tp in touching_points:
        #pygame.draw.circle(screen, GREEN, (int(tp[0]), int(tp[1])), 3)
 

    return touching_points

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Circle Skinning 2D Example")
    screen.fill(BLACK)
    print("****************************************************************")
    print("Left click to place points, second click gives radius and draws circle.")
    print("C to clear all points")
    print("G to draw the skinning.")
    print("****************************************************************")

    running = True
    while running:
        for event in pygame.event.get():
            if (
                event.type == pygame.QUIT
                or event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                running = False
            # Left Click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if center:
                    center_pos = event.pos
                    center = False
                    print(f"Center placed at {event.pos}")
                else:
                    radius = ((event.pos[0] - center_pos[0]) ** 2 + (event.pos[1] - center_pos[1]) ** 2) ** 0.5
                    circle = Circle(center_pos, radius)
                    circles.append(circle)
                    pygame.draw.circle(screen, RED, circle.center, int(circle.r), 2)
                    center = True
                    print(f"Circle drawn with center at {circle.center} and radius {circle.r}")
            # C
            if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                circles = []
                center = True
                center_pos = None
                screen.fill(BLACK)
                print("Cleared all points.")


            # G
            if event.type == pygame.KEYDOWN and event.key == pygame.K_g:
                if len(circles) >= 2:
                    compute_skinning(circles)
                    print("Drew skinning lines between circles.")
                else:
                    print("Need at least 2 circles to draw skinning.")


            # toggle
        pygame.display.flip()

    pygame.quit()
