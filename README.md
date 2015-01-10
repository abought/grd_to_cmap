## Photoshop Gradient to Matplotlib conversion tool
### Purpose
Many useful, special-purpose color maps (lookup tables) have been created for 
Adobe Photoshop. This tool is intended to extract information from these files 
and make these color maps available in matplotlib for use as part of a 
free and open-source toolchain. 

The conversion tool presently supports colors specified in RGB, HSV, and CMYK, 
and will automatically convert to RGB format for matplotlib internal use.

### Usage
This tool has been tested with python 2.7. 
Required dependencies can be installed via the following command:

`pip install -r requirements.txt`

And the tool can be run as follows:

`python grd_reader.py input_filename.grd`

At present raw data is dumped to the console and some reformatting is required;
this may be refined in future versions.

### Known limitations
This tool was originally designed for a specific purpose (extraction of the 
[ORI "Advanced forensic actions" lookup tables](http://ori.hhs.gov/advanced-forensic-actions) for use with matplotlib).

As such, it is heavily optimized for the creation of Linear Segmented Color 
Maps with evenly spaced colors. Discontinuous gradients, opacity, and the 
LAB color scheme are among the features not presently supported. 
Issue reports and pull requests are welcome.

### Acknowledgments 
Valek Filippov and the RE-lab team decoded the .grd file format and provided 
an [initial parser implementation](https://gitorious.org/re-lab/graphics/source/781a65604d405f29c2da487820f64de8ddb0724d:photoshop/grd) 
that this tool relies heavily on.