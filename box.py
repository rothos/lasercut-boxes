# This program generates an SVG file of plans for an open-topped box
# whose faces are joined by box joints (also called finger joints),
# which resemble battlements.
#
# The program can be run from the command-line by typing:
# > python box.py LxWxH "boxname"
# The specified dimensions are in inches. For example:
# > python box.py 6x4x3 "mybox"
# will save a file called mybox-6x4x3.svg which contains the plans
# for a box 6 inches long, 4 inches wide, and 3 inches high.

import sys
import math
import svgwrite

# # Save the command-line arguments in variables.
# dimensions = sys.argv[1]
# boxname = sys.argv[2]

# If any dimension is less than 0.25", return an error.
# [todo]

dimensions = "4x2x1"
dimensions = "12x24x8"

# If the user didn't specify a box name, use the name "box".
# if boxname == "":
    # boxname = "box"
boxname = "box"

# Parse the dimensions string.
length, width, height = map(float, dimensions.split("x"))

#-----------------------------------------------------------------------------
# BOX PARAMETERS, all lengths in inches
# (1/8" wood is actually 0.106" thick)
# path_buffer specifies how much space between the panel paths

wood_thickness = 0.106
laser_offset_socket_depth = 0.02
laser_offset_socket_length = 0.02
path_buffer = 0.1
dpi = 72

#-----------------------------------------------------------------------------

# Define the Path class
class Path:
    def __init__(self):
        self.points = []

    # add_point adds a point to the path.
    def add_point(self, x, y):
        self.points.append((x, y))
        return self

    # You can also add a point using the "+" operator.
    # If other is a point, append it to the points list.
    # If other is a Path, append its points to the points list.
    def __add__(self, other):
        if isinstance(other, tuple):
            self.points.append(other)
        elif isinstance(other, Path):
            self.join(other)
        return self

    def join(self, other):
        self.points += other.points
        return self

    def shift(self, x, y):
        self.points = [(p[0] + x, p[1] + y) for p in self.points]

    def scale(self, factor):
        self.points = [(p[0]*factor, p[1]*factor) for p in self.points]
        return self

    def mirror(self, axis):
        if axis == "x":
            self.points = [(p[0], -p[1]) for p in self.points]
        elif axis == "y":
            self.points = [(-p[0], p[1]) for p in self.points]

    # Finding the bounding box
    def min_x(self): return min([p[0] for p in self.points])
    def max_x(self): return max([p[0] for p in self.points])
    def min_y(self): return min([p[1] for p in self.points])
    def max_y(self): return max([p[1] for p in self.points])

    def clean_up(self):
        for i, pt in enumerate(self.points):
            self.points[i] = (round(pt[0], 12), round(pt[1], 12))


#-----------------------------------------------------------------------------

# Create a reference shape, a 1"x1" square.
def generate_reference_square():
    path = Path()
    path.add_point(0, 0)
    path.add_point(1, 0)
    path.add_point(1, 1)
    path.add_point(0, 1)
    return path

# Calculate where the sockets will go. These values do NOT account for
# the laser offset, which will be factored in later.
# The returned values do NOT include the first and last point of the side,
# only where the socket cuts go.
def calculate_socket_points(dimension_name, dimension_value):
    socket_length = 2*wood_thickness
    pts = []

    # Sockets locations along the bottom sides, running left to right.
    if dimension_name == "length":
        num_sockets = (dimension_value - 2*wood_thickness - socket_length) // (2*socket_length)
        num_sockets = int(num_sockets)
        shift = (dimension_value - ((2*num_sockets - 1) * socket_length)) / 2
        pts = [shift+socket_length*i for i in range(2*num_sockets)]
        return pts

    # Sockets locations along the bottom front/back, running left to right.
    elif dimension_name == "width":
        num_sockets = (dimension_value - socket_length) // (2*socket_length)
        num_sockets = int(num_sockets)
        shift = (dimension_value - ((2*num_sockets - 1) * socket_length)) / 2
        pts = [shift+socket_length*i for i in range(2*num_sockets)]
        return pts

    # Sockets locations along the height, running top to bottom.
    elif dimension_name == "height":
        num_sockets = (dimension_value - wood_thickness) // (2*socket_length)
        num_sockets = int(num_sockets)
        pts = [socket_length*(i+1) for i in range(2*num_sockets)]
        return pts

    else:
        print("Error: invalid dimension name \"%s\"." % dimension_name)
        return

# A function to generate a panel path.
# Valid names are "front", "side", and "bottom".
#
# Front/back panels look like this:
#  ________________________
# |                        |
# |_                      _|
#   |                    |   HEIGHT
#  _|   ____      ____   |_
# |____|    |____|    |____|
#           WIDTH
#
# Side panels look like this:
#    ______________________________
#   |                              |
#  _|                              |_
# |                                  | HEIGHT
# |_    ____      ____      ____    _|
#   |__|    |____|    |____|    |__|
#                LENGTH
#
# The bottom panel simply fits the above panels and is LENGTH x WIDTH.
#
# The top left point of the bounding box of the path is always (0, 0).
#
# This function must factor in the laser offsets.
def generate_panel_path(panel_name, use_offsets=True):
    path = Path()
    socket_points_length = calculate_socket_points("length", length)
    socket_points_width  = calculate_socket_points("width", width)
    socket_points_height = calculate_socket_points("height", height)

    socket_depth = wood_thickness - use_offsets*laser_offset_socket_depth
    eps = use_offsets*laser_offset_socket_length

    #------------------------------------------------------
    # FRONT PANEL
    if panel_name == "front":
        path.add_point(0, 0)

        for i in range(0, int(len(socket_points_height)), 2):
            path.add_point(0, socket_points_height[i]+eps)
            path.add_point(socket_depth, socket_points_height[i]+eps)
            path.add_point(socket_depth, socket_points_height[i+1]-eps)
            path.add_point(0, socket_points_height[i+1]-eps)

        path.add_point(0, height)

        for i in range(0, int(len(socket_points_width)), 2):
            path.add_point(socket_points_width[i]+eps, height)
            path.add_point(socket_points_width[i]+eps, height-socket_depth)
            path.add_point(socket_points_width[i+1]-eps, height-socket_depth)
            path.add_point(socket_points_width[i+1]-eps, height)

        path.add_point(width, height)

        for i in range(0, int(len(socket_points_height)), 2):
            path.add_point(width, socket_points_height[::-1][i]-eps)
            path.add_point(width-socket_depth, socket_points_height[::-1][i]-eps)
            path.add_point(width-socket_depth, socket_points_height[::-1][i+1]+eps)
            path.add_point(width, socket_points_height[::-1][i+1]+eps)

        path.add_point(width, 0)

    #------------------------------------------------------
    # SIDE PANEL
    elif panel_name == "side":
        path.add_point(socket_depth, 0)

        for i in range(0, int(len(socket_points_height)), 2):
            path.add_point(socket_depth, socket_points_height[i])
            path.add_point(0, socket_points_height[i])
            path.add_point(0, socket_points_height[i+1])
            path.add_point(socket_depth, socket_points_height[i+1])

        path.add_point(socket_depth, height)

        for i in range(0, int(len(socket_points_length)), 2):
            path.add_point(socket_points_length[i]+eps, height)
            path.add_point(socket_points_length[i]+eps, height-socket_depth)
            path.add_point(socket_points_length[i+1]-eps, height-socket_depth)
            path.add_point(socket_points_length[i+1]-eps, height)

        path.add_point(length-socket_depth, height)

        for i in range(0, int(len(socket_points_height)), 2):
            path.add_point(length-socket_depth, socket_points_height[::-1][i])
            path.add_point(length, socket_points_height[::-1][i])
            path.add_point(length, socket_points_height[::-1][i+1])
            path.add_point(length-socket_depth, socket_points_height[::-1][i+1])

        path.add_point(length-socket_depth, 0)

    #------------------------------------------------------
    # BOTTOM PANEL
    elif panel_name == "bottom":
        path.add_point(socket_depth, socket_depth)

        for i in range(0, int(len(socket_points_length)), 2):
            path.add_point(socket_points_length[i], socket_depth)
            path.add_point(socket_points_length[i], 0)
            path.add_point(socket_points_length[i+1], 0)
            path.add_point(socket_points_length[i+1], socket_depth)

        path.add_point(length-socket_depth, socket_depth)

        for i in range(0, int(len(socket_points_width)), 2):
            path.add_point(length-socket_depth, socket_points_width[i])
            path.add_point(length, socket_points_width[i])
            path.add_point(length, socket_points_width[i+1])
            path.add_point(length-socket_depth, socket_points_width[i+1])

        path.add_point(length-socket_depth, width-socket_depth)

        for i in range(0, int(len(socket_points_length)), 2):
            path.add_point(socket_points_length[::-1][i], width-socket_depth)
            path.add_point(socket_points_length[::-1][i], width)
            path.add_point(socket_points_length[::-1][i+1], width)
            path.add_point(socket_points_length[::-1][i+1], width-socket_depth)

        path.add_point(socket_depth, width-socket_depth)

        for i in range(0, int(len(socket_points_width)), 2):
            path.add_point(socket_depth, socket_points_width[::-1][i])
            path.add_point(0, socket_points_width[::-1][i])
            path.add_point(0, socket_points_width[::-1][i+1])
            path.add_point(socket_depth, socket_points_width[::-1][i+1])

    return path

#-----------------------------------------------------------------------------

def draw_path(dwg, path_obj):
    path_obj.shift(0.1,0.1)

    # First scale the path
    path_obj.scale(dpi)

    # This turns 12.999999999999998 into 13.0. Delete if desired.
    path_obj.clean_up()

    # Create a path and set its attributes
    svgpath = dwg.path(d='M{},{} L'.format(*path_obj.points[0]))
    svgpath.fill('none')
    svgpath.stroke('black', width=1)

    # Add each point to the path
    for point in path_obj.points[1:]:
        svgpath.push('{},{}'.format(*point))

    # Close the path
    svgpath.push('Z')

    # Add the path to the drawing and save it
    dwg.add(svgpath)

#-----------------------------------------------------------------------------

# Create the five paths for the box.
# The front and back panels (WIDTH x HEIGHT) will be the same,
# and the left and right panels (LENGTH x HEIGHT) will be the same.
# The bottom panel (LENGTH x WIDTH) is its own thing.
# So, there are three paths to create.

ref_square = generate_reference_square()
front = generate_panel_path("front", use_offsets=True)
front.shift(0, ref_square.max_y()+path_buffer)
back = generate_panel_path("front", use_offsets=True)
back.shift(0, front.max_y()+path_buffer)
left = generate_panel_path("side", use_offsets=True)
left.shift(0, back.max_y()+path_buffer)
right = generate_panel_path("side", use_offsets=True)
right.shift(0, left.max_y()+path_buffer)
bottom = generate_panel_path("bottom", use_offsets=True)
bottom.shift(0, right.max_y()+path_buffer)

#-----------------------------------------------------------------------------

# Create the svg
dwg = svgwrite.Drawing(
    filename=boxname + "-" + dimensions + ".svg",
    size=(str(max(length,width)*dpi + dpi), str(dpi*bottom.max_y() + dpi)),
    profile="full"
    )

# Draw the reference square
draw_path(dwg, ref_square)
dwg.add(dwg.text('1" x 1"', insert=(10, 18), fill='red',
    style='font-size: 10px; font-family: "Arial";'))

# Draw the panel paths
draw_path(dwg, front)
draw_path(dwg, back)
draw_path(dwg, left)
draw_path(dwg, right)
draw_path(dwg, bottom)

# Save the file
dwg.save()
