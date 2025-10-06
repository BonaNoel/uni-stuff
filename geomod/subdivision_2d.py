import pygame

BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

points = []
weights1 = [-1 / 6, 4 / 6, 4 / 6, -1 / 6]
current_weight = weights1
weights2 = [-1 / 8, 5 / 8, 5 / 8, -1 / 8]
weights3 = [-1 / 12, 7 / 12, 7 / 12, -1 / 12]
weights4 = [-1 / 24, 13 / 24, 13 / 24, -1 / 24]
iterations = 0
# if not interpolate then approximate
interpolate = True
save_original = True
original_points = []


def place_point(pos):
    points.append(pos)
    pygame.draw.circle(screen, RED, pos, 5)
    if len(points) > 1:
        pygame.draw.lines(screen, WHITE, False, points, 2)


def subdivision(points=points, weights=current_weight):
    if interpolate:
        interpolate_subdivision(points, weights)
    else:
        aproximate_subdivision(points, weights)


def interpolate_subdivision(points, weights=current_weight):
    for _ in range(iterations):
        new_points = []
        for i in range(len(points)):
            p0 = points[i - 1]
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            p3 = points[(i + 2) % len(points)]

            new_x = (
                weights[0] * p0[0]
                + weights[1] * p1[0]
                + weights[2] * p2[0]
                + weights[3] * p3[0]
            )
            new_y = (
                weights[0] * p0[1]
                + weights[1] * p1[1]
                + weights[2] * p2[1]
                + weights[3] * p3[1]
            )

            new_points.append((new_x, new_y))

        points = merge_points(points, new_points)
        redraw(points)


def merge_points(points, new_points):
    merged = []
    for p, np in zip(points, new_points):
        merged.append(p)
        merged.append(np)

    longer = points if len(points) > len(new_points) else new_points
    merged.extend(longer[len(merged) // 2 :])
    return merged


def aproximate_subdivision(points, weights=current_weight):
    pass


def redraw(points):
    screen.fill(BLACK)
    for p in points:
        pygame.draw.circle(screen, RED, p, 5)
    if len(points) > 1:
        pygame.draw.lines(screen, WHITE, True, points, 2)


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("2D Subdivision Example")
    screen.fill(BLACK)

    print("****************************************************************")
    print("Left click to place points, right click for dragging.")
    print("C to clear points.")
    print("O to connect first and last points.")
    print("S to increase subdivision level, A to decrease.")
    print("R to toggle between interpolate and approximate.")
    print("W to change weights")
    print("Press ESC to exit.")
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
                place_point(event.pos)
                print(f"Point placed at {event.pos}")
            # Right Click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                print(f"Right click at {event.pos}")

            # C
            if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                points = []
                save_original = True
                screen.fill(BLACK)
                print("Cleared all points.")

            # O
            if event.type == pygame.KEYDOWN and event.key == pygame.K_o:
                if len(points) > 3:
                    pygame.draw.lines(screen, WHITE, True, points, 2)
                    print("Connected first and last points.")
                else:
                    print("Need at least 4 points to connect.")

            # A and S
            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                iterations += 1
                if save_original:
                    original_points = points.copy()
                    save_original = False
                print(f"Increased subdivision level to {iterations}.")
                subdivision(points, current_weight)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                if iterations <= 0:
                    print("Subdivision level cannot be less than 0.")
                    continue

                iterations -= 1
                print(f"Decreased subdivision level to {iterations}.")

                if iterations > 0:
                    subdivision(points, current_weight)
                else:
                    redraw(original_points)
            # R
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                interpolate = not interpolate
                mode = "Interpolate" if interpolate else "Approximate"
                print(f"Subdivision mode set to {mode}.")
                subdivision()

            # W
            if event.type == pygame.KEYDOWN and event.key == pygame.K_w:
                if current_weight == weights1:
                    current_weight = weights2
                    print("Weights set to weights2" + weights2.__str__())
                    if iterations > 0:
                        subdivision(points, current_weight)
                        continue

                if current_weight == weights2:
                    current_weight = weights3
                    print("Weights set to weights3." + weights3.__str__())
                    if iterations > 0:
                        subdivision(points, current_weight)
                        continue

                if current_weight == weights3:
                    current_weight = weights4
                    print("Weights set to weights4." + weights4.__str__())
                    if iterations > 0:
                        subdivision(points, current_weight)
                        continue

                if current_weight == weights4 or current_weight == []:
                    current_weight = weights1
                    print("Weights set to weights1." + weights1.__str__())
                    if iterations > 0:
                        subdivision(points, current_weight)
                        continue

            # toggle
        pygame.display.flip()

    pygame.quit()
