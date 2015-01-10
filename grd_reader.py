# !/usr/bin/env python
"""
Parse Adobe .grd files

Adapted from work by Valek Filippov (c) 2010:
 https://gitorious.org/re-lab/graphics/source/781a65604d405f29c2da487820f64de8ddb0724d:photoshop/grd
"""

import sys, struct

import chroma

shift_buf = "                                    "

COLOR_TERMS = {"Cyn", "Mgnt", "Ylw", "Blck",
               "Rd", "Grn", "Bl",
               "H", "Strt", "Brgh"}


class GrdReader(object):
    """Read an Adobe .grd format file"""
    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as f:
            self.buffer = f.read()

        # Define functions used to handle particular types of data
        self.types = {"patt": self._p_patt, "desc": self._p_desc,
                      "VlLs": self._p_vlls, "TEXT": self._p_text,
                      "Objc": self._p_objc, "UntF": self._p_untf,
                      "bool": self._p_bool, "long": self._p_long,
                      "doub": self._p_doub, "enum": self._p_enum,
                      "tdta": self._p_tdta}

        # Store data about gradients
        # Because gradient names do not have to be unique, store names and gradients separately
        # TODO: API is a bit clumsy
        self.gradients = []  # File can contain multiple gradient entries
        self.gradient_names = []

        self._cur_obj_name = ""
        self._cur_gradient = []  # Single gradient is a list of color entries
        self._cur_clr = {}  # Each color is dict with colors + location + type

    def parse(self):
        """Parse file and load into a list of gradients"""
        offset = 28
        shift = 0  # spaces from the left edge
        while offset < len(self.buffer):
            offset = self._parse_entry(self.buffer, offset, shift)

        self._flush_gradient()

    def _flush_gradient(self):
        """Clear previous gradients"""
        self._flush_color()

        if self._cur_gradient:
            self.gradients.append(self._cur_gradient)
            self._cur_gradient = []

    def _flush_color(self):
        if self._cur_clr:
            self._cur_gradient.append(self._cur_clr)  # New color stop; store previous one
            self._cur_clr = {}

    def _convert_color(self, clr_data):
        """Parse color object (when field name = Clr). Return RGB triplet"""
        # TODO: Get color data.
        # TODO: Convert color data from specified format (PS) to tuple bounds used in py library

        palette = clr_data["palette"]
        if palette == "CMYC":
            fmt = "CMYK"
            # PS represents CMYK as a percent; chroma expects range 0..1
            color_tuple = (clr_data["Cyn"] / 100.,
                           clr_data["Mgnt"] / 100.,
                           clr_data["Ylw"] / 100.,
                           clr_data["Blck"] / 100.)
        elif palette == "RGBC":
            fmt = "RGB"
            # PS represents RGB values as 0-255; chroma expects range 0..1
            color_tuple = (clr_data["Rd"] / 255.,
                           clr_data["Grn"] / 255.,
                           clr_data["Bl"] / 255.)
        elif palette == "HSBC":
            fmt = "HSV"
            # PS represents Hue as an angle (0-360), and Sat/Bright as %
            color_tuple = (clr_data["H"],
                           clr_data["Strt"] / 100.,
                           clr_data["Brgh"] / 100.)
        else:
            raise NotImplementedError("Unknown color type: " + palette)

        color = chroma.Color(color_tuple, format=fmt)
        return color.rgb

    def grd_to_cmap(self, gradient_spec):
        """
        Convert Adobe PS gradient information to a matplotlib cmap spec
        gradient_spec: A list of color stops for one single gradient
        """
        # First, adjust the color stop positions to cover the full range 0..1:
        #  .grd files can sometimes omit these endpoints. So stretch range
        gradient_locations = [c["Lctn"] for c in gradient_spec]
        min_loc = min(gradient_locations)
        max_loc = max(gradient_locations)

        gradient_locations = [(loc-min_loc)*(1./(max_loc-min_loc))
                              for loc in gradient_locations]

        gradient_rgb = [self._convert_color(c)
                        for c in gradient_spec]

        cmap_dict = {'red': [],
                     'green': [],
                     'blue': []}

        for loc, rgb in zip(gradient_locations, gradient_rgb):
            cmap_dict["red"].append((loc, rgb[0], rgb[0]))
            cmap_dict["green"].append((loc, rgb[1], rgb[1]))
            cmap_dict["blue"].append((loc, rgb[2], rgb[2]))

        return cmap_dict

    def _parse_entry(self, buf, offset, shift):
        [nlen] = struct.unpack('>L', buf[offset:offset + 4])
        if nlen == 0:
            nlen = 4
        offset += 4

        name = buf[offset:offset + nlen]
        offset = offset + nlen
        field_type = buf[offset:offset + 4]
        offset += 4
        if field_type in self.types:  # Call appropriate func for field type
            offset = self.types[field_type](buf, offset, name, shift)
        else:
            print "Unknown key:\t", name, field_type
            self.p_unkn(buf, offset, name, shift)
        return offset

    def _p_patt(self, buf, offset, name, shift):
        """Not rev engineered yet"""
        return offset

    def _p_tdta(self, buf, offset, name, shift):
        [size] = struct.unpack('>L', buf[offset:offset + 4])
        offset += 4
        string = buf[offset:offset + size]
        offset += size
        print shift * " ", name, "(tdta", size, ")", string
        return offset

    def _p_desc(self, buf, offset, name, shift):
        # convert 4 bytes as big-endian unsigned long
        [size] = struct.unpack('>L', buf[offset:offset + 4])
        return offset + 26

    def _p_long(self, buf, offset, name, shift):
        [size] = struct.unpack('>L', buf[offset:offset + 4])
        print shift * " ", name, "(long)", size

        if self._cur_obj_name == "Clr" and name == "Lctn":
            # Represents color info in gradient
            self._cur_clr[name] = size
        return offset + 4

    def _p_vlls(self, buf, offset, name, shift):
        [size] = struct.unpack('>L', buf[offset:offset + 4])
        offset += 4
        print shift * " ", name, "(VlLs)", size
        shift += 2
        for i in range(size):
            field_type = buf[offset:offset + 4]
            offset += 4
            if field_type in self.types:
                offset = self.types[field_type](buf, offset, "----", shift)
            else:
                print "Unknown key:\t", name, field_type
                self.p_unkn(buf, offset, "", shift)
        shift -= 2
        return offset

    def _p_objc(self, buf, offset, name, shift):
        """Unpack data from an object that contains multiple fields/values"""
        [objnamelen] = struct.unpack('>L', buf[offset:offset + 4])
        offset += 4
        objname = buf[offset:offset + objnamelen * 2]
        offset += objnamelen * 2
        [objtypelen] = struct.unpack('>L', buf[offset:offset + 4])
        if objtypelen == 0:
            objtypelen = 4
        offset += 4
        typename = buf[offset:offset + objtypelen]
        offset += objtypelen
        [value] = struct.unpack('>L', buf[offset:offset + 4])
        offset += 4
        print shift * " ", name, "(Objc)", objname, typename, value

        self._cur_obj_name = name.strip()
        if self._cur_obj_name == "Grad":
            self._flush_gradient()
        elif self._cur_obj_name == "Clr":
            self._flush_color()
            self._cur_clr = {"palette": typename.strip()}

        shift += 2
        for i in range(value):
            offset = self._parse_entry(buf, offset, shift)
        shift -= 2
        return offset

    def _p_text(self, buf, offset, name, shift):
        [size] = struct.unpack('>L', buf[offset:offset + 4])
        string = ""
        for i in range(size - 1):
            string += str(
                buf[offset + 4 + i * 2 + 1:offset + 4 + i * 2 + 2])
        print shift * " ", name, "(TEXT", size, ")", string

        if self._cur_obj_name == "Grad" and name.strip() == "Nm":
            self.gradient_names.append(string.strip())

        return offset + 4 + size * 2

    def _p_untf(self, buf, offset, name, shift):
        field_type = buf[offset:offset + 4]
        [value] = struct.unpack('>d', buf[offset + 4:offset + 4 + 8])
        print shift * " ", name, "(UntF)", field_type, value

        name = name.strip()
        if self._cur_obj_name == "Clr" and name in COLOR_TERMS:
            # Store color information is this is a recognized palette
            self._cur_clr[name] = value
        return offset + 12

    def _p_bool(self, buf, offset, name, shift):
        # ord converts 1 byte number
        print shift * " ", name, "(bool)", ord(buf[offset:offset + 1])
        return offset + 1

    def _p_doub(self, buf, offset, name, shift):
        # unpack 8 bytes ieee 754 value to floating point number
        [value] = struct.unpack('>d', buf[offset:offset + 8])
        print shift * " ", name, "(doub)", value
        name = name.strip()
        if self._cur_obj_name == "Clr" and name in COLOR_TERMS:
            # Store color information is this is a recognized palette
            self._cur_clr[name] = value
        return offset + 8

    def _p_enum(self, buf, offset, name, shift):
        [size1] = struct.unpack('>L', buf[offset:offset + 4])
        offset += 4
        if size1 == 0:
            size1 = 4
        name1 = buf[offset:offset + size1]
        offset += size1
        [size2] = struct.unpack('>L', buf[offset:offset + 4])
        if size2 == 0:
            size2 = 4
        offset += 4
        name2 = buf[offset:offset + size2]
        offset += size2
        print shift * " ", name, "(enum)", name1, name2
        return offset

    def p_unkn(self, buf, offset, name, shift):
        # assume 4 bytes value
        # in such case offset+4:offset+8 is next length
        # and offset+8:offset+12 is next enum
        # check for it
        name = buf[offset + 8:offset + 12]
        if name in self.types:
            # everything is fine
            [size] = struct.unpack('>L', buf[offset:offset + 4])
            return size, offset + 4
        else:
            print "Failed with simple case\n"
            str_hex = ""
            str_asc = ""
            ml = 15
            for i in range(ml):
                try:
                    str_hex += "%02x " % ord(buf[offset + i])
                    if ord(buf[offset + i]) < 32 or 126 < ord(buf[offset + i]):
                        str_asc += '.'
                    else:
                        str_asc += buf[offset + i]
                    print str_hex, str_asc
                except:
                    print "Something failed"
            return str_hex + " " + str_asc, len(buf) + 1


def main():
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        try:
            data = GrdReader(filename)
        except IOError:
            print "No file"
            sys.exit(1)

        data.parse()

        print "JSON BELOW"
        from pprint import pprint as pp
        # Sample display of data in internal structure

        print "Gradient information"
        pp(zip(data.gradient_names, data.gradients))

        print "Modified gradients (consistent RGB)"
        mod_gradients = [[data._convert_color(c) for c in gradient]
                         for gradient in data.gradients]
        pp(zip(data.gradient_names, mod_gradients))

        print "Matplotlib gradient specs"
        for g in data.gradients:
            pp(data.grd_to_cmap(g))

if __name__ == '__main__':
    main()
