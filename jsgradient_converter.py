"""
Read in an adobe gradient file (.grd) and output a JS file describing
colorstops for an HTML canvas
"""
# TODO: Quick hack script; clean up to reduce duplication with matplotlib converter

import argparse, collections, json, keyword, os, re, sys

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


def generate_outfile(grd, out_fn):
    """Generate a python file containing colormap data"""
    out_str = StringIO()

    new_grd_names = unique_grd_names(grd.gradient_names)
    js_gradients = [grd.grd_to_js(g) for g in grd.gradients]

    gradient_data = {name: data
                     for name, data in zip(new_grd_names, js_gradients)}

    data_str = json.dumps(gradient_data, indent=4)
    out_str.write("var gradients = {0};".format(data_str))

    with open(out_fn, 'w') as out_f:
        out_f.write(out_str.getvalue())

if __name__ == "__main__":
    parsed_args = command_line()
    grd = parse_file(parsed_args.filename)

    out_fn = os.path.splitext(parsed_args.filename)[0] + ".js"

    generate_outfile(grd, out_fn)
