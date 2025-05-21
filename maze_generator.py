import random
import matplotlib.pyplot as plt

side = 20
height = width = side
seed = 1234
random_seed = True
random.seed(random.randint(0, 0xFFFFFFFF) if random_seed else seed)
grid = [[0 for _ in range(height)] for _ in range(width)]

N, S, E, W = 1, 2, 4, 8
DX = {E: 1, W: -1, N: 0, S: 0}
DY = {E: 0, W: 0, N: -1, S: 1}
OPPOSITE = {E: W, W: E, N: S, S: N}

def carve_passages_from(cx, cy, grid):
    directions = [N, S, E, W]
    random.shuffle(directions)
    for direction in directions:
        nx, ny = cx + DX[direction], cy + DY[direction]
        if 0 <= ny < height and 0 <= nx < width and grid[ny][nx] == 0:
            grid[cy][cx] |= direction
            grid[ny][nx] |= OPPOSITE[direction]
            carve_passages_from(nx, ny, grid)

carve_passages_from(0, 0, grid)

fig, ax = plt.subplots(figsize=(width / 2, height / 2))
ax.set_aspect('equal')
ax.axis('off')
for y in range(height):
    for x in range(width):
        cx, cy = x, height - y - 1  # invert y for correct display in matplotlib

        # Draw north wall if no passage north
        if (grid[y][x] & N) == 0:
            ax.plot([cx, cx + 1], [cy + 1, cy + 1], color='black')

        # Draw west wall if no passage west
        if (grid[y][x] & W) == 0:
            ax.plot([cx, cx], [cy, cy + 1], color='black')

        # Draw south wall if no passage south (for bottom row)
        if y == height - 1 and (grid[y][x] & S) == 0:
            ax.plot([cx, cx + 1], [cy, cy], color='black')

        # Draw east wall if no passage east (for rightmost column)
        if x == width - 1 and (grid[y][x] & E) == 0:
            ax.plot([cx + 1, cx + 1], [cy, cy + 1], color='black')

# Entrance (top-left) - open the north wall of (0,0)
ax.plot([0, 1], [height, height], color='white', linewidth=2)

# Exit (bottom-right) - open the south wall of (width-1, height-1)
ax.plot([width - 1, width], [0, 0], color='white', linewidth=2)

plt.show()

def print_ascii_maze():
    # Top border with entrance at (0, 0)
    print("S  S" + "_" * (width * 2 - 3))
    for y in range(height):
        line = "|"
        for x in range(width):
            cell = grid[y][x]

            # Bottom wall: "_" if there's no South passage
            if cell & S:
                bottom = " "
            else:
                bottom = "_"

            # Right wall: check East wall and also South wall of neighbor
            if cell & E:
                if (x + 1 < width) and (grid[y][x + 1] & S):
                    right = " "
                else:
                    right = "_"
            else:
                right = "|"

            line += bottom + right

        # Ensure proper entrance (open top of top-left cell)
        if y == 0:
            line = line[:1] + " " + line[2:]

        # Ensure proper exit (open bottom of bottom-right cell)
        if y == height - 1:
            line = line[:-3] + "E E"

        print(line)


print_ascii_maze()

edges = []

for y in range(height):
    for x in range(width):
        cell = grid[y][x]
        if cell & N:
            edges.append(((x, y), (x, y - 1)))
        if cell & S:
            edges.append(((x, y), (x, y + 1)))
        if cell & E:
            edges.append(((x, y), (x + 1, y)))
        if cell & W:
            edges.append(((x, y), (x - 1, y)))

undirected_edges = set()
for a, b in edges:
    undirected_edges.add(frozenset([a, b])) #maybe is ok a /2

for edge in undirected_edges:
    print(tuple(edge))

print(len(edges))
print(len(undirected_edges))
