from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.transfer import copy_file_resumable, sha256_of_file


def main() -> int:
    root = Path('dummy_transfer')
    src_dir = root / 'src'
    dst_dir = root / 'dst'
    src_dir.mkdir(parents=True, exist_ok=True)
    dst_dir.mkdir(parents=True, exist_ok=True)
    src = src_dir / 'data.bin'
    # create random data
    with open(src, 'wb') as f:
        f.write(os.urandom(1024 * 1024 + 123))
    dst = dst_dir / 'data.bin'
    # write partial file to simulate resume
    with open(src, 'rb') as sf, open(dst, 'wb') as df:
        df.write(sf.read(256 * 1024))
    success = copy_file_resumable(str(src), str(dst))
    if not success:
        print('copy_file_resumable returned False')
        return 1
    if sha256_of_file(str(src)) != sha256_of_file(str(dst)):
        print('hash mismatch after transfer')
        return 1
    print('Integration transfer succeeded')
    return 0


if __name__ == '__main__':
    sys.exit(main())
