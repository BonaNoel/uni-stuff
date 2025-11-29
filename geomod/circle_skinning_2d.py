import pygame
import math

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)

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

    def is_collinear(P, O, R, tol=1e-6):
        # P, O, R are points (x,y)
        x0, y0 = O
        x1, y1 = P
        x2, y2 = R
        # Distance from P to line O-R
        dist = abs((y2 - y0)*x1 - (x2 - x0)*y1 + x2*y0 - y2*x0) / math.hypot(y2 - y0, x2 - x0)
        return dist < tol
   

    def check_orientation(P, O, desired='CCW'):
        # radius vector
        rx, ry = P[0] - O[0], P[1] - O[1]
        # tangent vector
        tx, ty = -ry, rx  # CCW
        if desired == 'CW':
            tx, ty = ry, -rx
        # Here you can compare with vector to next point or some reference
        # For now, just return tangent vector for later use
        return (tx, ty)

    def get_touching_point_of_2_circles(C1, C2):
        # Calculate touching point between circle C1 and C2
        dx = C2.center[0] - C1.center[0]
        dy = C2.center[1] - C1.center[1]
        D = math.hypot(dx, dy)

        # Guard against degenerate or numerically unstable situations:
        if D == 0:
            # Return two opposite points on circle C1 as a fallback
            p1 = (C1.center[0] + C1.r, C1.center[1])
            p2 = (C1.center[0] - C1.r, C1.center[1])
            return p1, p2

        acos_arg = (C1.r + C2.r) / D
        # clamp to [-1, 1]
        if acos_arg > 1.0:
            acos_arg = 1.0
        elif acos_arg < -1.0:
            acos_arg = -1.0

        t_angle = math.acos(acos_arg)  # note: acos for internal tangents
        c_angle = math.atan2(dy, dx)

        p1 = (C1.center[0] + C1.r * math.cos(c_angle + t_angle),
            C1.center[1] + C1.r * math.sin(c_angle + t_angle))

        p2 = (C1.center[0] + C1.r * math.cos(c_angle - t_angle),
            C1.center[1] + C1.r * math.sin(c_angle - t_angle))

        return p1, p2

    def check_if_point_on_circle(P, C):
        # Check if point P is on circle C
        dx = P[0] - C.center[0]
        dy = P[1] - C.center[1]
        dist = math.hypot(dx, dy)
        return abs(dist - C.r) < 1e-6

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
            R = radical_center(circles[i-1], circles[i], circles[i+1])
            print("Radical center: ", R)
            if R is not None:
                pygame.draw.circle(screen, WHITE, (int(R[0]), int(R[1])), 5)
            Appollonius_circles = get_two_same_orientation_appolonius(circles[i-1], circles[i], circles[i+1])
            # First filter by orientation: keep only Apollonius solutions whose sign
            # triple (s1,s2,s3) is uniform (all +1 or all -1). This matches the
            # paper's observation that the two solutions where all three given
            # circles have the same orientation provide the desired touching points.
            for item in Appollonius_circles:
                ac, signs = item
                if ac is None:
                    continue
                pygame.draw.circle(screen, BLUE, (int(ac.center[0]), int(ac.center[1])), max(1, int(ac.r)), 2)
                # now calculate circle[i] and ac touching point
                tp = get_touching_point_of_2_circles(circles[i], ac)
                print("Touching points from Apollonius circle: ", tp)
                pygame.draw.circle(screen, RED, (int(tp[0][0]), int(tp[0][1])), 4)
                pygame.draw.circle(screen, RED, (int(tp[1][0]), int(tp[1][1])), 4)
                
                # check orientation of touching points

    # Calculate touching point for last circle with cn-1,cn   
    result = get_touching_point_from_external_tanget(circles[-1], circles[-2])
    touching_points.append(result[0])
    touching_points.append(result[1])

    print("Touching points number: ", len(touching_points))
    # Show touching points with green dots
    for tp in touching_points:
        pygame.draw.circle(screen, GREEN, (int(tp[0]), int(tp[1])), 3)
 

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
