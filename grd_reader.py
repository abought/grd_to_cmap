# !/usr/bin/env python
"""
Parse Adobe .grd files

Adapted from work by Valek Filippov (c) 2010:
 https://gitorious.org/re-lab/graphics/source/781a65604d405f29c2da487820f64de8ddb0724d:photoshop/grd
"""

import sys, struct

import chroma

shift_buf = "                                    "


class GrdReader(object):
    """Read an Adobe .grd format file"""
    def __init__(self, filename):
        self.filename = filename
        self.gradients = []  # File can contain multiple gradient entries
        with open(filename, 'r') as f:
            self.buffer = f.read()

        # Define functions used to handle particular types of data
        self.types = {"patt": self._p_patt, "desc": self._p_desc,
                      "VlLs": self._p_vlls, "TEXT": self._p_text,
                      "Objc": self._p_objc, "UntF": self._p_untf,
                      "bool": self._p_bool, "long": self._p_long,
                      "doub": self._p_doub, "enum": self._p_enum,
                      "tdta": self._p_tdta}

    def parse(self):
        """Parse file and load into a list of gradients"""
        offset = 28
        shift = 0  # spaces from the left edge
        while offset < len(self.buffer):
            offset = self._parse_entry(self.buffer, offset, shift)

    def _parse_color(self, clr_type):
        """Parse color object (when field name = Clr). Return RGB triplet"""
        # TODO: Get color data.
        # TODO: Convert color data from specified format (PS) to tuple bounds used in py library

        if clr_type == "CMYC":
            fmt = "CMYK"
            # PS represents CMYK as a percent; chroma expects range 0..1
            color_data = [x / 100. for x in color_data]
        elif clr_type == "RGBC":
            fmt = "RGB"
            # PS represents RGB values as 0-255; chroma expects range 0..1
            color_data = [x / 255. for x in color_data]
        elif clr_type == "HSBC":
            fmt = "HSV"
            # PS represents Hue as an angle (0-360), and Sat/Bright as %
            color_data[1] /= 100.
            color_data[2] /= 100.
        else:
            raise NotImplementedError("Unknown color type: " + clr_type)

        color = chroma.Color(color_data, format=fmt)
        return color.rgb

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
        """Unpack the data from an object that contains multiple fields/values"""
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
        return offset + 4 + size * 2

    def _p_untf(self, buf, offset, name, shift):
        field_type = buf[offset:offset + 4]
        [value] = struct.unpack('>d', buf[offset + 4:offset + 4 + 8])
        print shift * " ", name, "(UntF)", field_type, value
        return offset + 12

    def _p_bool(self, buf, offset, name, shift):
        # ord converts 1 byte number
        print shift * " ", name, "(bool)", ord(buf[offset:offset + 1])
        return offset + 1

    def _p_doub(self, buf, offset, name, shift):
        # unpack 8 bytes ieee 754 value to floating point number
        [value] = struct.unpack('>d', buf[offset:offset + 8])
        print shift * " ", name, "(doub)", value
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

if __name__ == '__main__':
    main()
