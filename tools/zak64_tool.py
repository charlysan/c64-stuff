# Copyright (c) 2023 charlysan

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse

DISK2_SIDE_A_SIGNAGURE = b"\x31\x0A"
DISK2_SIDE_B_SIGNAGURE = b"\x32\x01"

NUM_ROOMS = 59

sector_offset = [
	0, 0, 21, 42, 63, 84, 105, 126, 147, 168, 189, 210, 
    231, 252, 273, 294, 315, 336, 357, 376, 395, 414, 433, 452, 
    471, 490, 508, 526, 544, 562, 580, 598, 615, 632, 649, 666
]

resources_per_file = [
	 0, 29, 12, 14, 13,  4,  4, 10,  7,  4,
	14, 19,  5,  4,  7,  6, 11,  9,  4,  4,
	 1,  3,  3,  5,  1,  9,  4, 10, 13,  6,
	 7, 10,  2,  6,  1, 11,  2,  5,  7,  1,
	 7,  1,  4,  2,  8,  6,  6,  6,  4, 13,
	 3,  1,  2,  1,  2,  1, 10,  1,  1
]

def main():
    parser = argparse.ArgumentParser(
        description="Zak McKracken and the Alien Mindbenders c64 tool"
    )

    subparsers = parser.add_subparsers(
        title="subcommands", description="valid subcommands"
    )

    parser_lfl_extract = subparsers.add_parser(
        "lfl-extract", help="Extract .LFL from .D64 image files"
    )

    parser_lfl_extract.add_argument("DISK2_A_PATH", help="Disk 2 - Side A")
    parser_lfl_extract.add_argument("DISK2_B_PATH", help="Disk 2 - Side B")
    parser_lfl_extract.add_argument(
        "--xor",
        action="store_true",
        dest="xor",
        default=False,
        help="XOR each byte with 0xFF (Needed for scummvm)",
    )

    parser.add_argument(
        "-v",
        action="store",
        dest="verbose",
        default=False,
        type=bool,
        help="Print verbose information",
    )

    args = parser.parse_args()

    # Extract lfl
    if parser_lfl_extract:
        room_disks_c64 = []
        room_tracks_c64 = []
        room_sectors_c64 = []

        global xor_output
        xor_output = args.xor

        with open(args.DISK2_A_PATH, "rb") as file_a, open(
            args.DISK2_B_PATH, "rb"
        ) as file_b:
            signature_a = file_a.read(2)
            if signature_a != DISK2_SIDE_A_SIGNAGURE:
                print(f"Invalid signature for Disk 2 - Side A: {signature_a.hex()}")
                exit(-1)
            signature_b = file_b.read(2)
            if signature_b != DISK2_SIDE_B_SIGNAGURE:
                print(f"Invalid signature for Disk 2 - Side B: {signature_b.hex()}")
                exit(-1)

            with open("00.LFL", "wb") as lfl_00:
                # Write header (must match Disk 2 Side B signature)
                write(lfl_00, bytearray(DISK2_SIDE_B_SIGNAGURE))

                # copy object flags
                for _ in range(775):
                    write(lfl_00, file_a.read(1))

                # copy room offsets
                for i in range(0, NUM_ROOMS):
                    room_disks_c64.append(file_a.read(1))
                    write(lfl_00, room_disks_c64[i])

                for i in range(0, NUM_ROOMS):
                    room_sectors_c64.append(file_a.read(1))
                    write(lfl_00, room_sectors_c64[i])
                    room_tracks_c64.append(file_a.read(1))
                    write(lfl_00, room_tracks_c64[i])

                # copy costume offsets
                for _ in range(38):
                    write(lfl_00, file_a.read(1))
                for _ in range(38):
                    write(lfl_00, file_a.read(2))

                # copy script offsets
                for _ in range(155):
                    write(lfl_00, file_a.read(1))
                for _ in range(155):
                    write(lfl_00, file_a.read(2))

                # copy sound offsets
                for _ in range(127):
                    write(lfl_00, file_a.read(1))
                for _ in range(127):
                    write(lfl_00, file_a.read(2))

            for i in range(NUM_ROOMS):
                if room_disks_c64[i] == b"1":
                    input_file = file_a
                elif room_disks_c64[i] == b"2":
                    input_file = file_b
                else:
                    continue

                fname = f"{i:02d}.LFL"
                with open(fname, "wb") as file_out:
                    print(f"Creating {fname}...")
                    offset = (
                        sector_offset[
                            int.from_bytes(room_tracks_c64[i], byteorder="little")
                        ]
                        + int.from_bytes(room_sectors_c64[i], byteorder="little")
                    ) * 256
                    print(f"Offset: {offset}")
                    input_file.seek(offset)

                    for _ in range(resources_per_file[i]):
                        len = 0xFFFF

                        while len == 0xFFFF:
                            len_bytes = input_file.read(2)
                            len = int.from_bytes(len_bytes, byteorder="little")
                            write(file_out, len_bytes)

                        len -= 2

                        while len > 0:
                            write(file_out, input_file.read(1))
                            len -= 1


def write(file, data):
    if xor_output:
        data = bytearray(data)
        for i in range(len(data)):
            data[i] ^= 0xFF
    file.write(data)


if __name__ == "__main__":
    main()
