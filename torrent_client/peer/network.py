import struct
from bitstring import BitArray
'''
Common network constants
'''

# types of peer messages
MESSAGE_HANDSHAKE = -2
MESSAGE_KEEPALIVE = -1
MESSAGE_CHOKE = 0
MESSAGE_UNCHOKE = 1
MESSAGE_INTERESTED = 2
MESSAGE_UNINTERESTED = 3
MESSAGE_HAVE = 4
MESSAGE_BITFIELD = 5
MESSAGE_REQUEST = 6
MESSAGE_PIECE = 7
MESSAGE_CANCEL = 8
MESSAGE_PORT = 9

HANDSHAKE_PROTOCOL_STR = b'BitTorrent protocol'

'''
Classes for types of Peer messages
'''


class AbstractPeerMessage:
    def __init__(self, len_prefix, message_type):
        """Initialize an abstract peer message

        Args:
            len_prefix: message length prefix according to the protocol
            message_type: a constant value mostly specified by the protocol
        """

        self.message_type = message_type
        self.len_prefix = len_prefix

    @property
    def raw(self):
        """raw message bytes"""
        raise NotImplementedError()

    @classmethod
    def from_msg(cls, msg):
        """create a class instance from the raw message"""
        raise NotImplementedError()


class SimpleMessage(AbstractPeerMessage):
    def __init__(self, len_prefix, message_type):
        """Initialize a simple peer message of the form <len_prefix=0001><message_type=x>

        Args:
            len_prefix: message length prefix according to the protocol
            message_type: a constant value mostly specified by the protocol
        """

        super().__init__(len_prefix, message_type)

    @property
    def raw(self):
        """raw message bytes"""
        return struct.pack(">I", self.len_prefix) + chr(self.message_type).encode()

    @classmethod
    def from_msg(cls, msg):
        """create a class instance from the raw message"""
        return cls(struct.unpack(">I", msg[:4])[0], msg[4])


class HaveMessage(AbstractPeerMessage):
    def __init__(self, len_prefix, message_type, piece_index):
        """Initialize a 'have' message

        Args:
            len_prefix: message length prefix according to the protocol
            message_type: a constant value mostly specified by the protocol
            piece_index: the piece index that the peer has
        """

        if message_type != MESSAGE_HAVE:
            raise Exception("Incorrect 'Have' message")

        super().__init__(len_prefix, message_type)
        self.piece_index = piece_index

    @property
    def raw(self):
        """raw message bytes"""
        return struct.pack(">I", self.len_prefix) + chr(self.message_type).encode() + struct.pack(">I", self.piece_index)

    @classmethod
    def from_msg(cls, msg):
        """create a class instance from the raw message"""
        return cls(struct.unpack(">I", msg[:4])[0], msg[4], struct.unpack(">I", msg[5:9])[0])


class BitfieldMessage(AbstractPeerMessage):
    def __init__(self, len_prefix, message_type, bitfield):
        """Initialize a bitfield message that specifies the peer available pieces

        Args:
            len_prefix: message length prefix according to the protocol
            message_type: a constant value mostly specified by the protocol
            bitfield: a bit array that specifies which pieces are present
        """

        if message_type != MESSAGE_BITFIELD:
            raise Exception("Incorrect 'Bitfield' message")
        super().__init__(len_prefix, message_type)

        self._bitfield = bitfield
        bit_arr = BitArray(self._bitfield)

        self.available_pieces = [i for i in range(len(bit_arr)) if bit_arr[i]]

    @property
    def raw(self):
        """raw message bytes"""
        return struct.pack(">I", self.len_prefix) + chr(self.message_type).encode() + self._bitfield

    @classmethod
    def from_msg(cls, msg):
        """create a class instance from the raw message"""
        return cls(struct.unpack(">I", msg[:4])[0], msg[4], msg[5:])


class KeepAliveMessage(AbstractPeerMessage):
    def __init__(self, len_prefix=0, message_type=MESSAGE_KEEPALIVE):
        """Initialize a 'keepalive' message

        Args:
            len_prefix: message length prefix according to the protocol
            message_type: a constant value mostly specified by the protocol
        """

        super().__init__(len_prefix, message_type)

    @property
    def raw(self):
        """raw message bytes"""
        return struct.pack(">I", self.len_prefix)

    @classmethod
    def from_msg(cls, msg):
        """create a class instance from the raw message"""
        return cls(struct.unpack(">I", msg)[0], MESSAGE_KEEPALIVE)


class PieceMessage(AbstractPeerMessage):
    def __init__(self, index, begin, block, len_prefix, message_type):
        """Initialize a 'piece' message

        Args:
            index: integer specifying the zero-based piece index
            begin: integer specifying the zero-based byte offset within the piece
            block: block of data, which is a subset of the piece specified by index
            len_prefix: message length prefix according to the protocol
            message_type: a constant value mostly specified by the protocol
        """

        super().__init__(len_prefix, message_type)

        self.index = index
        self.begin = begin
        self.block = block

    @property
    def raw(self):
        """raw message bytes"""
        return struct.pack('>IbII' + str(self.len_prefix - 9) + 's', self.len_prefix, self.message_type, self.index, self.begin, self.block)

    @classmethod
    def from_msg(cls, msg):
        """create a class instance from the raw message"""
        length = struct.unpack('>I', msg[:4])[0]
        parts = struct.unpack('>IbII' + str(length - 9) + 's', msg[:length + 4])
        return cls(parts[2], parts[3], parts[4], len_prefix=parts[0], message_type=parts[1])


class HandshakeMessage(AbstractPeerMessage):
    def __init__(self, info_hash, peer_id, len_prefix=19, message_type=MESSAGE_HANDSHAKE):
        """Initialize a 'handshake' message

        Args:
            info_hash: 20-byte SHA1 hash of the info key in the metainfo file
            peer_id: 20-byte string used as a unique ID for the client
            len_prefix: message length prefix according to the protocol
            message_type: a constant value mostly specified by the protocol
        """

        super().__init__(len_prefix, message_type)

        self.info_hash = info_hash
        self.peer_id = peer_id

    @property
    def raw(self):
        """raw message bytes"""
        return b''.join([
            chr(self.len_prefix).encode(),
            b'BitTorrent protocol',
            (chr(0) * 8).encode(),
            self.info_hash,
            self.peer_id
        ])

    @classmethod
    def from_msg(cls, msg):
        """create a class instance from the raw message"""
        return cls(msg[28:48], msg[48:], len_prefix=msg[0])


class RequestMessage(AbstractPeerMessage):
    def __init__(self, index, begin, length, len_prefix=13, message_type=MESSAGE_REQUEST):
        """Initialize a piece request message

        Args:
            index: integer specifying the zero-based piece index
            begin: integer specifying the zero-based byte offset within the piece
            length: integer specifying the requested length.
            len_prefix: message length prefix according to the protocol
            message_type: a constant value mostly specified by the protocol
        """

        super().__init__(len_prefix, message_type)

        self.index = index
        self.begin = begin
        self.length = length

    @property
    def raw(self):
        """raw message bytes"""
        return struct.pack('>IbIII',
                           self.len_prefix,
                           self.message_type,
                           self.index,
                           self.begin,
                           self.length)

    @classmethod
    def from_msg(cls, msg):
        """create a class instance from the raw message"""
        return cls(*struct.unpack('>IbIII', msg))
