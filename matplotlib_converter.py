"""
Read in an adobe gradient file (.grd) and output a python-importable
set of matplotlib colormaps
"""
__author__ = 'abought'

import argparse, collections, keyword, os, pprint, re, sys

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import grd_reader


def command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename",
                        help="Path to an Adobe .grd file")

    return parser.parse_args()


#### Functions to process the input file
def parse_file(filename):
    """Parse a grd file to extract gradient information"""
    if os.path.splitext(filename)[1] != ".grd":
        print("File must be an Adobe PS gradient file with .grd extension")
        sys.exit(1)

    try:
        grd = grd_reader.GrdReader(filename)
    except IOError:
        print "File not found"
        sys.exit(1)

    try:
        grd.parse()
    except:
        print("Error occurred while reading file")
        sys.exit(1)

    return grd


def unique_grd_names(grd_names_list):
    """Adobe GRD format allows gradient names to be non-unique.

     Modify gradient names so that each can be referenced uniquely"""

    # First, the gradient names must be valid python variables and len > 0
    python_names = [re.sub("[^_A-Za-z][^_a-zA-Z0-9]*", "", n)
                    for n in grd_names_list]
    python_names = [n if len(n) > 0 and not keyword.iskeyword(n) else "grd"
                    for n in python_names]

    # Then, the gradient names must be unique
    counter = collections.Counter(python_names)
    new_grd_names = [n if counter[n] == 1 else "{}_{}".format(n, i)
                     for i, n in enumerate(python_names)]

    return new_grd_names


### Functions to write the output file
def write_headers(out_str):
    """
    Write header section that is independent of any specific gradient
    """
    out_str.write("import matplotlib.pyplot as plt\n"
                  "from matplotlib.colors import LinearSegmentedColormap\n\n")

    return out_str   # TODOL refactor to oop


def write_gradient(gradient_name, gradient_data, out_str):
    """Write data about one gradient"""
    grd_str = pprint.pformat(gradient_data)
    out_str.write("{0}_data = {1}\n".format(gradient_name, grd_str))

    out_str.write(
        "{0} = LinearSegmentedColormap('{0}', {0}_data)\n".format(
            gradient_name))

    out_str.write("plt.register_cmap(cmap={0})\n\n".format(gradient_name))
    return out_str


def write_gradients_list(gradient_names, out_str):
    """Write a list of all gradients in file for convenient external access"""
    grad_str = pprint.pformat(gradient_names)
    out_str.write("ALL_GRADIENTS = {}\n\n".format(grad_str))
    return out_str


def generate_outfile(grd, out_fn):
    """Generate a python file containing colormap data"""
    out_str = StringIO()

    out_str = write_headers(out_str)

    new_grd_names = unique_grd_names(grd.gradient_names)
    mpl_gradients = [grd.grd_to_cmap(g) for g in grd.gradients]

    for name, data in zip(new_grd_names, mpl_gradients):
        out_str = write_gradient(name, data, out_str)

    write_gradients_list(new_grd_names, out_str)

    with open(out_fn, 'w') as out_f:
        out_f.write(out_str.getvalue())

if __name__ == "__main__":
    parsed_args = command_line()
    grd = parse_file(parsed_args.filename)

    out_fn = os.path.splitext(parsed_args.filename)[0] + ".py"

    generate_outfile(grd, out_fn)
