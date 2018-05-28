from __future__ import print_function
import os
import math
import numpy as np
from xml.etree import ElementTree as et
from optparse import OptionParser
try:
    from itertools import izip as zip
except ImportError:
    pass

def dbl2str( f ):
    return str(int(f))

class Palette:
    """Helper class for generating colors from palettes"""
    def __init__(self,colors):
        self.colors = np.array(colors)
        self.x_points = np.linspace(0,1,len(colors))
    def at(self, pos):
        """Returns tuple of 3 integers. Pos is position in the palette, from 0 to 1"""
        def clr_i( i ):
            return round(np.interp( [pos],
                                    self.x_points, 
                                    self.colors[:,i] )[0])
        return clr_i(0), clr_i(1), clr_i(2)


def GenerateSVGContour(output, x,y, palette, options=None, margin=10, out_size = 640, svg_header=True):
    """Cerates an SVG file with the given contour"""
    if not options:
        line_color = "rgb(96,0,0)"
        line_width = "1.0"
        circle_radius = '1.5'
    else:
        line_color = options.line_color
        line_width = repr(options.line_weight )
        circle_radius = repr(options.node_radius)
        
    x0 = x.min()
    x1 = x.max()
    y0 = y.min()
    y1 = y.max()
    
    size = max( (x1-x0, y1-y0) )
    scale = (out_size-2*margin) / size
    x = (x-x0)*scale + margin
    y = (y-y0)*scale + margin

    real_w = int((x1-x0)*scale + 2*margin)
    real_h = int((y1-y0)*scale + 2*margin)

    def xy_seq():
        return zip(x,y)

    # create an SVG XML element
    doc = et.Element('svg', 
                     width=str(real_w),
                     height=str(real_h),
                     version='1.1', xmlns='http://www.w3.org/2000/svg')

    poly_code = ["%s,%s"%(dbl2str(xi),dbl2str(yi))
                 for xi, yi in xy_seq() ]
    et.SubElement(doc, 'polyline', 
                  points=" ".join(poly_code),
                  style='fill:none;stroke:%s;stroke-width:%s'%(line_color,line_width) )

    if not options or options.show_nodes:
        grp = et.SubElement(doc, 'g', id="circles")
        for i, (xi, yi) in enumerate(xy_seq()):
            # add a circle (using the SubElement function)
            et.SubElement(grp, 'circle', 
                          cx=dbl2str(xi), cy=dbl2str(yi), 
                          r=circle_radius, fill='rgb(%d,%d,%d)'%palette.at(float(i)/len(x)))

    # ElementTree 1.2 doesn't write the SVG file header errata, so do that manually
    with open(output, 'wb') as f:
        if svg_header:
            f.write(b'<?xml version=\"1.0\" standalone=\"no\"?>\n')
            f.write(b'<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\"\n')
            f.write(b'\"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n')
        f.write(et.tostring(doc))


pal_pale = Palette([(124,162,226),
                (129,184,160),
                (199, 198, 207),
                (219, 188,166)])

pal_bw = Palette([
        (0,0,0),
        (255,255,255),
        (0,0,0),
        (255,255,255),
        (0,0,0),
        (255,255,255),
        (0,0,0),
        (255,255,255),
        ])

pal_rainbow = Palette([(255,0,0),
                (250,116,0),
                (255,255,0),
                (0, 255, 0),
                (0, 200, 166),
                (0, 0, 255)])

DEFAULT_PALETTE = "pale"
palettes = {"pale": pal_pale,
            "bw": pal_bw,
            "rainbow":pal_rainbow}

class SolidPalette:
    def __init__(self,color):
        self.color = color
    def at(self, p):
        return self.color

def main():
    parser = OptionParser( description = "Converter from numpy files, generated by demo_tsp to SVG vector images."  )
    parser.add_option( "-o", "--output", dest="output",
                       help="Output file. By default, same as input, but with .svg extension" )
    parser.add_option("-s", "--size", type="int", default=640, dest="size",
                       help="Maximal dimension of the generated image" )
    parser.add_option( "--margin", type="int", default=10, dest="margin",
                       help="margin, left at the sides of the image" )

    parser.add_option( "-w", "--line-weight", type="float", dest="line_weight", default=1.0,
                       help="Weight of a line, showing the optimal course" )
    parser.add_option( "-c", "--show-nodes", action="store_false", dest="show_nodes", default=True,
                       help="Show nodes as circles" )
    parser.add_option( "-r", "--node-radius", type="float", default=2.0, dest="node_radius",
                       help="Radius of a circle, representing a node" )
    parser.add_option( "-l", "--line-color", dest="line_color", default="black",
                       help="Color of a line. May be any valid SVG color. Example: black, red, rgb(125,11,110)" )
    parser.add_option( "--node-palette", default=DEFAULT_PALETTE, dest="palette",
                       help="Color palette, used to colorize nodes. Available built-in palettes: "+",".join(palettes.keys()) )


    (options, args) = parser.parse_args()

    if not args:
        print( "Input files not specified")
        exit(1)

    if len(args) > 1 and options.output:
        print( "When processing several files, do not specify output")
        exit(1)
    try:
        palette = palettes[options.palette]
    except KeyError:
        print( "Unknown palette: %s"%options.palette)
        exit(1)

    for in_file in args:
        out_file = options.output or os.path.splitext(in_file)[0]+".svg"
        try:
            with open(in_file,"rb") as fl:
                xy = np.load( fl )
                x=xy[0,:]
                y=xy[1,:]
            GenerateSVGContour(out_file,x,y, palette, options=options,
                               out_size=options.size,
                               margin=options.margin)
            print( "Generated %s from %s"%(out_file, in_file))
        except IOError as err:
            print( err)
            exit(2)

if __name__=="__main__":
    main()
