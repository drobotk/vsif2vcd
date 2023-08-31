#!/usr/bin/env python3

import argparse
import lzma
import os
import re
import struct
import traceback

__version__ = "0.1.0"
__all__ = (
    "IMAGE_HEADER_SIZE",
    "SCENE_ENTRY_SIZE",
    "get_image_string",
    "calculate_valve_crc32",
    "extract_scene_names",
    "BufferReader",
    "decompile_bvcd",
)

IMAGE_HEADER_SIZE: int = 5 * 4
SCENE_ENTRY_SIZE: int = 4 * 4

_args: argparse.Namespace


def _print(*args, **kwargs):
    if not _args or not _args.quiet:
        print(*args, **kwargs)


def _dbg(*args, **kwargs):
    if _args and _args.verbose:
        _print("DEBUG:", *args, **kwargs)


def get_image_string(image: bytes, index: int) -> str:
    (offset,) = struct.unpack_from("<I", image, IMAGE_HEADER_SIZE + index * 4)
    end = image.index(0, offset)
    return image[offset:end].decode()


# fmt: off
VALVE_CRC = [
    0x00000000, 0x77073096, 0xEE0E612C, 0x990951BA,
    0x076DC419, 0x706AF48F, 0xE963A535, 0x9E6495A3,
    0x0EDB8832, 0x79DCB8A4, 0xE0D5E91E, 0x97D2D988,
    0x09B64C2B, 0x7EB17CBD, 0xE7B82D07, 0x90BF1D91,
    0x1DB71064, 0x6AB020F2, 0xF3B97148, 0x84BE41DE,
    0x1ADAD47D, 0x6DDDE4EB, 0xF4D4B551, 0x83D385C7,
    0x136C9856, 0x646BA8C0, 0xFD62F97A, 0x8A65C9EC,
    0x14015C4F, 0x63066CD9, 0xFA0F3D63, 0x8D080DF5,
    0x3B6E20C8, 0x4C69105E, 0xD56041E4, 0xA2677172,
    0x3C03E4D1, 0x4B04D447, 0xD20D85FD, 0xA50AB56B,
    0x35B5A8FA, 0x42B2986C, 0xDBBBC9D6, 0xACBCF940,
    0x32D86CE3, 0x45DF5C75, 0xDCD60DCF, 0xABD13D59,
    0x26D930AC, 0x51DE003A, 0xC8D75180, 0xBFD06116,
    0x21B4F4B5, 0x56B3C423, 0xCFBA9599, 0xB8BDA50F,
    0x2802B89E, 0x5F058808, 0xC60CD9B2, 0xB10BE924,
    0x2F6F7C87, 0x58684C11, 0xC1611DAB, 0xB6662D3D,
    0x76DC4190, 0x01DB7106, 0x98D220BC, 0xEFD5102A,
    0x71B18589, 0x06B6B51F, 0x9FBFE4A5, 0xE8B8D433,
    0x7807C9A2, 0x0F00F934, 0x9609A88E, 0xE10E9818,
    0x7F6A0DBB, 0x086D3D2D, 0x91646C97, 0xE6635C01,
    0x6B6B51F4, 0x1C6C6162, 0x856530D8, 0xF262004E,
    0x6C0695ED, 0x1B01A57B, 0x8208F4C1, 0xF50FC457,
    0x65B0D9C6, 0x12B7E950, 0x8BBEB8EA, 0xFCB9887C,
    0x62DD1DDF, 0x15DA2D49, 0x8CD37CF3, 0xFBD44C65,
    0x4DB26158, 0x3AB551CE, 0xA3BC0074, 0xD4BB30E2,
    0x4ADFA541, 0x3DD895D7, 0xA4D1C46D, 0xD3D6F4FB,
    0x4369E96A, 0x346ED9FC, 0xAD678846, 0xDA60B8D0,
    0x44042D73, 0x33031DE5, 0xAA0A4C5F, 0xDD0D7CC9,
    0x5005713C, 0x270241AA, 0xBE0B1010, 0xC90C2086,
    0x5768B525, 0x206F85B3, 0xB966D409, 0xCE61E49F,
    0x5EDEF90E, 0x29D9C998, 0xB0D09822, 0xC7D7A8B4,
    0x59B33D17, 0x2EB40D81, 0xB7BD5C3B, 0xC0BA6CAD,
    0xEDB88320, 0x9ABFB3B6, 0x03B6E20C, 0x74B1D29A,
    0xEAD54739, 0x9DD277AF, 0x04DB2615, 0x73DC1683,
    0xE3630B12, 0x94643B84, 0x0D6D6A3E, 0x7A6A5AA8,
    0xE40ECF0B, 0x9309FF9D, 0x0A00AE27, 0x7D079EB1,
    0xF00F9344, 0x8708A3D2, 0x1E01F268, 0x6906C2FE,
    0xF762575D, 0x806567CB, 0x196C3671, 0x6E6B06E7,
    0xFED41B76, 0x89D32BE0, 0x10DA7A5A, 0x67DD4ACC,
    0xF9B9DF6F, 0x8EBEEFF9, 0x17B7BE43, 0x60B08ED5,
    0xD6D6A3E8, 0xA1D1937E, 0x38D8C2C4, 0x4FDFF252,
    0xD1BB67F1, 0xA6BC5767, 0x3FB506DD, 0x48B2364B,
    0xD80D2BDA, 0xAF0A1B4C, 0x36034AF6, 0x41047A60,
    0xDF60EFC3, 0xA867DF55, 0x316E8EEF, 0x4669BE79,
    0xCB61B38C, 0xBC66831A, 0x256FD2A0, 0x5268E236,
    0xCC0C7795, 0xBB0B4703, 0x220216B9, 0x5505262F,
    0xC5BA3BBE, 0xB2BD0B28, 0x2BB45A92, 0x5CB36A04,
    0xC2D7FFA7, 0xB5D0CF31, 0x2CD99E8B, 0x5BDEAE1D,
    0x9B64C2B0, 0xEC63F226, 0x756AA39C, 0x026D930A,
    0x9C0906A9, 0xEB0E363F, 0x72076785, 0x05005713,
    0x95BF4A82, 0xE2B87A14, 0x7BB12BAE, 0x0CB61B38,
    0x92D28E9B, 0xE5D5BE0D, 0x7CDCEFB7, 0x0BDBDF21,
    0x86D3D2D4, 0xF1D4E242, 0x68DDB3F8, 0x1FDA836E,
    0x81BE16CD, 0xF6B9265B, 0x6FB077E1, 0x18B74777,
    0x88085AE6, 0xFF0F6A70, 0x66063BCA, 0x11010B5C,
    0x8F659EFF, 0xF862AE69, 0x616BFFD3, 0x166CCF45,
    0xA00AE278, 0xD70DD2EE, 0x4E048354, 0x3903B3C2,
    0xA7672661, 0xD06016F7, 0x4969474D, 0x3E6E77DB,
    0xAED16A4A, 0xD9D65ADC, 0x40DF0B66, 0x37D83BF0,
    0xA9BCAE53, 0xDEBB9EC5, 0x47B2CF7F, 0x30B5FFE9,
    0xBDBDF21C, 0xCABAC28A, 0x53B39330, 0x24B4A3A6,
    0xBAD03605, 0xCDD70693, 0x54DE5729, 0x23D967BF,
    0xB3667A2E, 0xC4614AB8, 0x5D681B02, 0x2A6F2B94,
    0xB40BBE37, 0xC30C8EA1, 0x5A05DF1B, 0x2D02EF8D,
]
# fmt: on


def calculate_valve_crc32(inp: str | bytes) -> int:
    if isinstance(inp, str):
        inp = inp.encode()

    crc = 0xFFFFFFFF

    for c in inp:
        crc = (crc >> 8) ^ VALVE_CRC[(crc ^ c) & 0xFF]

    return crc ^ 0xFFFFFFFF


def extract_scene_names(inp: str) -> set[str]:
    return {
        m.group().lower().replace("/", "\\")
        for m in re.finditer(r"scenes(?:\/|\\).+?\.vcd", inp, re.IGNORECASE)
    }


class BufferReader:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._cur = 0

    def skip(self, n: int):
        self._cur += n

    def byte(self):
        out = self._data[self._cur]
        self._cur += 1
        return out

    def slice(self, n: int):
        out = self._data[self._cur : self._cur + n]
        self._cur += n
        return out

    def unpack(self, fmt: str):
        out = struct.unpack_from(fmt, self._data, self._cur)[0]
        self._cur += struct.calcsize(fmt)
        return out


def decompile_bvcd_ramp(image: bytes, r: BufferReader, name: str, t: str = "") -> str:
    n_ramps = r.byte()
    if n_ramps < 1:
        return ""

    _dbg("decompile_bvcd_ramp")

    # overflow in tf2 scenes\workshop\player\engineer\low\taunt_jackhammer_rodeo.vcd
    # TODO: what do we do with this?
    # if n_ramps == 3:
    #     n_ramps = 259

    out = f"{t}{name}\r\n{t}{{\r\n"
    for _ in range(n_ramps):
        f1 = r.unpack("f")
        f2 = r.byte() / 255
        out += f"{t}  {f1:.4f} {f2:.4f}\r\n"

    out += f"{t}}}\r\n"

    return out


BVCD_EVENT_TYPE_NAMES = [
    "unspecified",
    "section",
    "expression",
    "lookat",
    "moveto",
    "speak",
    "gesture",
    "sequence",
    "face",
    "firetrigger",
    "flexanimation",
    "subscene",
    "loop",
    "interrupt",
    "stoppoint",
    "permitresponses",
    "generic",
]

BVCD_EVENT_FLAGS = {
    1 << 0: "resumecondition",
    1 << 1: "lockbodyfacing",
    1 << 2: "fixedlength",
    1 << 4: "forceshortmovement",
    1 << 5: "playoverscript",
}

BVCD_EVENT_CC_TYPES = {
    1: "cc_slave",
    2: "cc_disabled",
}

BVCD_EVENT_CC_FLAGS = {
    1 << 0: "cc_usingcombinedfile",
    1 << 1: "cc_combinedusesgender",
    1 << 2: "cc_noattenuate",
}

BVCD_EVENT_FLEX_INTERPOLATORS = [
    "default",
    "catmullrom_normalize_x",
    "easein",
    "easeout",
    "easeinout",
    "bspline",
    "linear_interp",
    "kochanek",
    "kochanek_early",
    "kochanek_late",
    "simple_cubic",
    "catmullrom",
    "catmullrom_normalize",
    "catmullrom_tangent",
    "exponential_decay",
    "hold",
]


def decompile_bvcd_event(image: bytes, r: BufferReader, t: str = "") -> str:
    _dbg("decompile_bvcd_event")

    out = ""

    event_type_name = BVCD_EVENT_TYPE_NAMES[r.byte()]
    name = get_image_string(image, r.unpack("<h"))
    out += f'{t}event {event_type_name} "{name}"\r\n{t}{{\r\n'

    f1 = r.unpack("f")
    f2 = r.unpack("f")
    out += f"{t}  time {f1:.6f} {f2:.6f}\r\n"

    param = get_image_string(image, r.unpack("<h"))
    out += f'{t}  param "{param}"\r\n'

    for i in 2, 3:
        param = get_image_string(image, r.unpack("<h"))
        if param:
            out += f'{t}  param{i} "{param}"\r\n'

    out += decompile_bvcd_ramp(image, r, "event_ramp", t + "  ")

    flags = r.byte()
    for b, flag in BVCD_EVENT_FLAGS.items():
        if flags & b:
            out += f"{t}  {flag}\r\n"

    if flags & 0x8 == 0:
        out += f"{t}  active 0\r\n"

    f = r.unpack("f")
    if f > 0:
        out += f"{t}  distancetotarget {f:.2f}\r\n"

    for tt in "tags", "flextimingtags":
        n_tags = r.byte()
        if n_tags:
            out += f"{t}  {tt}\r\n{t}  {{\r\n"
            for _ in range(n_tags):
                tag = get_image_string(image, r.unpack("<h"))
                f = r.byte() / 255
                out += f'{t}    "{tag}" {f:.6f}\r\n'

            out += f"{t}  }}\r\n"

    for tt in "playback_time", "shifted_time":
        n_tags = r.byte()
        if n_tags:
            out += f"{t}  absolutetags {tt}\r\n{t}  {{\r\n"
            for _ in range(n_tags):
                tag = get_image_string(image, r.unpack("<h"))
                f = r.unpack("<H") / 4096
                out += f'{t}    "{tag}" {f:.6f}\r\n'

            out += f"{t}  }}\r\n"

    if event_type_name == "gesture":
        f = r.unpack("f")
        if f != -1:
            out += f"{t}  sequenceduration {f:.2f}\r\n"

    # Using relative tags
    if r.byte() == 1:
        tag = get_image_string(image, r.unpack("<h"))
        wav = get_image_string(image, r.unpack("<h"))
        out += f'{t}  relativetag "{tag}" "{wav}"\r\n'

    n_flex = r.byte()
    if n_flex > 0:
        _dbg("decompile_bvcd_event: flex")
        out += f"{t}  flexanimations samples_use_time\r\n{t}  {{\r\n"
        for _ in range(n_flex):
            name = get_image_string(image, r.unpack("<h"))
            out += f'{t}    "{name}"'

            flags = r.byte()
            if flags & 1 == 0:
                out += " disabled"
            if flags & 2:
                out += " combo"

            f1 = r.unpack("f")
            f2 = r.unpack("f")
            if f1 != 0.0 and f2 != 1.0:
                out += f" range {f1:.1f} {f2:.1f}"

            out += f"\r\n"

            for _ in range(flags & 2 or 1):
                out += f"{t}    {{\r\n"
                n_samples = r.unpack("<H")
                for _ in range(n_samples):
                    f1 = r.unpack("f")
                    f2 = r.byte() / 255
                    out += f"{t}      {f1:.4f} {f2:.4f}"

                    curve_to = r.byte()
                    curve_from = r.byte()
                    if curve_to or curve_from:
                        out += f" curve_{BVCD_EVENT_FLEX_INTERPOLATORS[curve_from]}_to_curve_{BVCD_EVENT_FLEX_INTERPOLATORS[curve_to]}"

                    out += "\r\n"

                out += f"{t}    }}\r\n"

        out += f"{t}  }}\r\n"

    if event_type_name == "loop":
        out += f'{t}  loopcount "{r.byte()}"\r\n'

    if event_type_name == "speak":
        cctype = BVCD_EVENT_CC_TYPES.get(r.byte(), "cc_master")
        out += f'{t}  cctype "{cctype}"\r\n'
        token = get_image_string(image, r.unpack("<h"))
        out += f'{t}  cctoken "{token}"\r\n'
        flags = r.byte()
        for b, flag in BVCD_EVENT_CC_FLAGS.items():
            if flags & b:
                out += f"{t}  {flag}\r\n"

    out += f"{t}}}\r\n"

    return out


def decompile_bvcd(image: bytes, data: bytes) -> str:
    r = BufferReader(data)

    magic = r.slice(4)
    assert magic == b"bvcd", f"Incorrect magic: {magic}"

    version = r.byte()
    if version != 4:
        _print(f"Warning: BVCD {version=}")

    r.skip(4)  # crc

    out = "// Choreo version 1\r\n"

    n_events = r.byte()
    for _ in range(n_events):
        out += decompile_bvcd_event(image, r)

    n_actors = r.byte()
    for _ in range(n_actors):
        name = get_image_string(image, r.unpack("<h"))
        _dbg(f'decompile_bvcd: actor "{name}"')
        out += f'actor "{name}"\r\n{{\r\n'

        n_channels = r.byte()
        for _ in range(n_channels):
            name = get_image_string(image, r.unpack("<h"))
            _dbg(f'decompile_bvcd: channel "{name}"')
            out += f'  channel "{name}"\r\n  {{\r\n'

            n_events = r.byte()
            for _ in range(n_events):
                out += decompile_bvcd_event(image, r, "    ")

            if r.byte() == 0:
                out += '    active "0"\r\n'

            out += "  }\r\n"

        if r.byte() == 0:
            out += '  active "0"\r\n'

        out += "}\r\n"

    out += decompile_bvcd_ramp(image, r, "scene_ramp")

    # Footer
    out += "scalesettings\r\n{\r\n"
    out += '  "CChoreoView" "100"\r\n'
    out += '  "SceneRampTool" "100"\r\n'
    out += '  "ExpressionTool" "100"\r\n'
    out += '  "GestureTool" "100"\r\n'
    out += '  "RampTool" "100"\r\n}\r\n'
    out += "fps 60\r\nsnap off\r\n"

    return out


def format_fraction(a, b) -> str:
    return f"{a}/{b} ({a/b*100:.2f}%)"


def main():
    # fmt: off
    parser = argparse.ArgumentParser(description='Decompile and extract VCDs from a scenes.image file.')
    parser.add_argument("--version",         action="version", version=__version__)

    parser.add_argument("-q", "--quiet",     action="store_true", help="Only print errors")
    parser.add_argument("-v", "--verbose",   action="store_true", help="Print debug logs")
    parser.add_argument("-a", "--all",       action="store_true", help="Extract unnamed VCDs")
    parser.add_argument("-w", "--overwrite", action="store_true", help="Overwrite existing VCDs in the output directory")
    parser.add_argument("--save-names",      action="store_true", help="Save gathered scene names to names.txt")

    parser.add_argument("-n", "--names",     action="append", metavar="PATH", help="Search path for scene names in files; may also be a single file. Can be specified more than once. Directories will be searched recursively")
    parser.add_argument("-o", "--out",       metavar="PATH", default=".", help="Output directory")
    parser.add_argument("image",             metavar="IMAGE", help="scenes.image file")
    # fmt: on

    global _args
    _args = parser.parse_args()

    _print(f"vsif2vcd.py {__version__}", end="\n\n")

    try:
        with open(_args.image, "rb") as f:
            header = f.read(4)
            assert header == b"VSIF"
            f.seek(0)
            image = f.read()
    except FileNotFoundError as e:
        return print(f"FileNotFoundError: {e}")
    except AssertionError:
        return print(f"ERROR: {_args.image} is not a valid VSIF scenes.image file.")

    version, n_scenes, n_strings = struct.unpack_from("<3I", image, 4)
    _print(f"Image version: {version}")
    _print(f"Scene count: {n_scenes}")
    _print(f"String count: {n_strings}")

    names: set[str] = set()

    if _args.names:
        _print("Searching for scene names")

        def search_file(path):
            _print(f"Searching {path}")
            with open(path, errors="ignore") as f:
                data = f.read()
            new = extract_scene_names(data)
            for s in new:
                _print(f"\t+ {s}")
            names.update(new)

        for p in _args.names:
            if os.path.isfile(p):
                search_file(p)
            elif os.path.isdir(p):
                for dir, _, files in os.walk(p):
                    for file in files:
                        search_file(f"{dir}/{file}")
            else:
                print(f"ERROR: {p} is not a valid search path")

    n_names = len(names)
    _print(f"Known scene names: {n_names}")

    if not names and not _args.all:
        _print(f"No scenes will be extracted. Use `--all` to extract unnamed scenes.")
        return

    os.makedirs(_args.out, exist_ok=True)

    if _args.save_names:
        path = f"{_args.out}/names.txt"
        _print(f"Saving names to {path}")
        with open(path, "w") as f:
            f.write("\n".join(names))

    _dbg("Calculating CRCs")
    crc_to_name = {calculate_valve_crc32(name): name for name in names}
    del names

    n_named = 0
    n_decompiled = 0
    n_skipped = 0
    failed: list[tuple[str, str]] = []

    (entries_offset,) = struct.unpack_from("<I", image, 16)
    for i in range(n_scenes):
        crc, offset, length = struct.unpack_from(
            "<3I", image, entries_offset + i * SCENE_ENTRY_SIZE
        )

        name = crc_to_name.get(crc)
        if not name:
            if _args.all:
                name = f"scenes/{hex(crc)}.vcd"
            else:
                n_skipped += 1
                continue
        else:
            n_named += 1
            name = name.replace("\\", "/")

        outpath = f"{_args.out}/{name}"
        if not _args.overwrite and os.path.exists(outpath):
            n_skipped += 1
            continue

        _print(f"Extracting:", name)

        data = image[offset : offset + length]
        if data[:4] == b"LZMA":
            properties = data[12:17]
            compressed = data[17:]
            _dbg("Decompressing LZMA")
            data = lzma.LZMADecompressor(lzma.FORMAT_RAW, None, [lzma._decode_filter_properties(lzma.FILTER_LZMA1, properties)]).decompress(compressed)  # type: ignore

        try:
            vcd = decompile_bvcd(image, data)
        except Exception as e:
            print(f"ERROR: {name}: {e.__class__.__name__}: {e}")
            tb = traceback.format_exc()
            failed.append((name, tb))
        else:
            n_decompiled += 1
            _dbg("Saving to file")
            os.makedirs(os.path.dirname(outpath), exist_ok=True)
            with open(outpath, "wb") as f:
                f.write(vcd.encode())

    _print(f"Finished!")
    _print(f"Decompiled: {format_fraction(n_decompiled, n_scenes)}")
    _print(f"Skipped: {format_fraction(n_skipped, n_scenes)}")
    _print(f"Failed: {format_fraction(len(failed), n_scenes)}")
    if n_names:
        _print(f"Named: {format_fraction(n_named, n_scenes)}")
        _print(f"Names used: {format_fraction(n_named, n_names)}")

    if failed:
        _print(f"Scenes that failed to decompile:")
        for name, tb in failed:
            _print(f"{name}\n{tb}")


if __name__ == "__main__":
    main()
