from .blocks import Block
import math
from hashlib import sha1
from .torrent import SingleFileTorrent, MultiFileTorrent
import os


class FileSaver:
    def __init__(self, torrent, progress_bar):
        """Initialize a file saver class instance

        Args:
            torrent: a torrent object that represents the metainfo file
            progress_bar: a gui progress bar to be updated as blocks are downloaded
        """

        self._torrent = torrent
        self._progress_bar = progress_bar
        self._downloaded = []
        self._blocks = []

        for offset in range(0, torrent.length, Block.BLOCK_SIZE):
            block = Block(offset // torrent.piece_length,
                          offset % torrent.piece_length,
                          Block.BLOCK_SIZE if offset + Block.BLOCK_SIZE < torrent.length else torrent.length - offset)

            self._blocks.append(block)

    def append(self, block):
        """Append a downloaded block to the downloaded pool and update the gui progress bar

        Args:
            block: a downloaded block to be appended

        Returns:
            None
        """

        self._downloaded.append(block)
        self._progress_bar["value"] = int((len(self._downloaded) / len(self._blocks)) * 100)

    def save(self):
        """Save the complete torrent and update the progress bar to 100%

        Returns:
            None
        """

        if isinstance(self._torrent, SingleFileTorrent):
            self._save_singlefile()
        elif isinstance(self._torrent, MultiFileTorrent):
            self._save_multifile()
        else:
            raise TypeError("torrent object must be SingleFileTorrent or MultiFileTorrent")

        self._progress_bar["value"] = 100

    def _save_multifile(self):
        """Save a multi file torrent

        Returns:
            None
        """

        data = b""
        for block in self._blocks:
            data += [down for down in self._downloaded if (down.index == block.index and down.begin == block.begin)][0].block

        for file in self._torrent.files:
            path = f"{self._torrent.file_name}/{'/'.join([p.decode() for p in file[b'path']])}"

            dirs = os.path.dirname(path)
            if dirs:
                os.makedirs(dirs, exist_ok=True)

            with open(path, "wb") as f:
                f.write(data[:file[b"length"]])

            data = data[file[b"length"]:]

    def _save_singlefile(self):
        """Save a single file torrent

        Returns:
            None
        """

        data = b""
        for block in self._blocks:
            data += [down for down in self._downloaded if (down.index == block.index and down.begin == block.begin)][0].block

        with open(self._torrent.file_name, "wb") as f:
            f.write(data)

    def get_failed_blocks(self):
        """Validate block hashes, remove failed ones from the downloaded pool and return them

        Returns:
            a list of blocks whose hashes aren't valid
        """

        pieces = [[] for _ in range(math.ceil(self._torrent.length / self._torrent.piece_length))]
        for block in self._downloaded:
            pieces[block.index].append(block)

        [lst.sort(key=lambda b: b.begin) for lst in pieces]

        ret = []

        for i, blocks in enumerate(pieces):
            data = b""
            data += b"".join([block.block for block in blocks])

            if sha1(data).digest() != self._torrent.piece_hashes[i] and (
                len(data) == self._torrent.piece_length or
                (len(data) == self._torrent.length - i * self._torrent.piece_length and
                i + 1 == self._torrent.length // self._torrent.piece_length)):

                ret.extend(blocks)

        [self._downloaded.remove(block) for piece in ret for block in piece]
        ret = [Block(block.index, block.begin, len(block.block)) for piece in ret for block in piece]
        return ret

