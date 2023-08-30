# vsif2vcd.py

CLI utility to decompile and extract VCD (Valve Choreography Data) files from a scenes.image file found in Source games.

```
usage: vsif2vcd.py [-h] [--version] [-q] [-v] [-a] [-w] [--save-names] [-n PATH] [-o PATH] IMAGE

Decompile and extract VCDs from a scenes.image file.

positional arguments:
  IMAGE                  scenes.image file

options:
  -h, --help             show this help message and exit
  --version              show program's version number and exit
  -q, --quiet            Only print errors
  -v, --verbose          Print debug logs
  -a, --all              Extract unnamed VCDs
  -w, --overwrite        Overwrite existing VCDs in the output directory
  --save-names           Save gathered scene names to names.txt
  -n PATH, --names PATH  Search path for scene names in files; may also be a single file.
                         Can be specified more than once. Directories will be searched recursively
  -o PATH, --out PATH    Output directory
```
