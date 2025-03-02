import subprocess
import zlib
import re
import argparse
from typing import List


def run_binwalk(file_path: str) -> str:
    """Run binwalk and capture the output."""
    result = subprocess.run(
        ["binwalk", "--signature", file_path], capture_output=True, text=True
    )
    return result.stdout


def extract_offsets(binwalk_output: str) -> List[int]:
    """Extract Zlib offsets from binwalk output."""
    return [int(line.split(" ")[0]) for line in binwalk_output.split("\n")[3:-2]]


def read_file(file_path: str) -> bytes:
    """Read the file into memory as binary data."""
    with open(file_path, "rb") as f:
        return f.read()


def decompress_segments(file_data: bytes, offsets: List[int]) -> None:
    """Decompress and print data segments based on offsets."""
    for i in range(len(offsets)):
        start = offsets[i]
        end = offsets[i + 1] if i + 1 < len(offsets) else len(file_data)
        compressed_data = file_data[start:end]

        try:
            decompressed_data = zlib.decompress(compressed_data)
            print(f"Decompressed data from offset {hex(start)}:")
            print(decompressed_data.decode("utf-8", errors="ignore"))
        except zlib.error as e:
            print(f"Failed to decompress data at offset {hex(start)}: {e}")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Decompress Zlib segments in a file.")
    parser.add_argument(
        "file_path", type=str, help="Path to the file containing Zlib compressed data."
    )
    return parser.parse_args()


def main() -> None:
    """Main function to run the decompression process."""
    args = parse_arguments()
    binwalk_output = run_binwalk(args.file_path)
    offsets = extract_offsets(binwalk_output)
    file_data = read_file(args.file_path)
    decompress_segments(file_data, offsets)


if __name__ == "__main__":
    main()
