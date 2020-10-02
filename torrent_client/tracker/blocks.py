class Block:
    BLOCK_SIZE = 2 ** 14

    def __init__(self, index, begin, length):
        """Initialize a block object

        Args:
            index: integer specifying the zero-based piece index
            begin: integer specifying the zero-based byte offset within the piece
            length: length of block
        """

        self.index = index
        self.begin = begin
        self.length = length


class BlockManager:
    def __init__(self, torrent):
        """Initialize a block manager

        Args:
            torrent: a torrent object representing the metainfo file
        """

        self.file_size = torrent.length
        self.piece_length = torrent.piece_length

        if self.piece_length % Block.BLOCK_SIZE != 0:
            raise Exception("invalid piece length")

        self._blocks = []

        for offset in range(0, self.file_size, Block.BLOCK_SIZE):
            block = Block(offset // self.piece_length,
                          offset % self.piece_length,
                          Block.BLOCK_SIZE if offset + Block.BLOCK_SIZE < self.file_size else self.file_size - offset)

            self._blocks.append(block)

    def __iter__(self):
        """Returns the iterator object itself

        Returns:
            self
        """

        return self

    def __next__(self):
        """Returns the next item in the sequence. On reaching the end, it will raise StopIteration

        Returns:
            a block to be downloaded
        """

        if not self._blocks:
            raise StopIteration

        return self._blocks.pop(0)

    def add_block(self, block):
        """Add a block to the blocks to be downloaded if the block doesn't already exist

        Args:
            block: a block object to be downloaded

        Returns:
            None
        """

        if block not in self._blocks:
            self._blocks.append(block)
        else:
            raise Exception("block already exists")

    def extend_blocks(self, blocks):
        """Add multiple blocks to the blocks to be downloaded

        Args:
            blocks: a list of block objects

        Returns:
            None
        """

        for block in blocks:
            self.add_block(block)

    def empty(self):
        """Check if block pool is empty

        Returns:
            True if any blocks are left, else False
        """

        return self._blocks == []
