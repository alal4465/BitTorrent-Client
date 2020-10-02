from .network import *
import asyncio


class Peer:
    def __init__(self, ip, port, torrent):
        """Initialize a peer class

        Args:
            ip: peer ip address
            port: peer port number
            torrent: torrent class representing the metainfo file
        """

        self.available_pieces = []
        self.handshake_complete = False

        self._is_interested = False
        self._is_choking = True
        self._am_interested = False
        self._am_choking = True

        self._conn = PeerConnection(ip, port, torrent.info_hash, torrent.peer_id)

    async def handshake(self):
        """Performs a handshake and sets self.handshake_complete accordingly"""

        try:
            await self._conn.handshake()

            messages = await self._conn.recv()
            self._handle_messages(messages)
            self.handshake_complete = True

        except Exception:
            self.handshake_complete = False

    async def download(self, block):
        """Download a specified block

        Args:
            block: a block object specifying a piece block to download

        Returns:
            downloaded block, non if failed
        """

        downloaded = None

        try:
            if not self._am_interested:
                await self._conn.send(SimpleMessage(1, MESSAGE_INTERESTED).raw)
                self._am_interested = True

            messages = await self._conn.recv()
            self._handle_messages(messages)

            if self._am_interested and (not self._is_choking):
                await self._conn.send(RequestMessage(block.index, block.begin, block.length).raw)
                messages = await self._conn.recv()

                while messages:
                    piece_msg = [msg for msg in messages if (msg.message_type == MESSAGE_PIECE and (msg.index == block.index and msg.begin == block.begin))]
                    if piece_msg:
                        downloaded = piece_msg[0]

                    self._handle_messages(messages)
                    messages = await self._conn.recv()
        except Exception:
            downloaded = None

        return downloaded

    def _handle_messages(self, messages):
        """Handle a list of Message objects

        Args:
            messages: message list

        Returns:
            None
        """

        for msg in messages:
            if msg.message_type == MESSAGE_BITFIELD:
                self.available_pieces.extend(messages[0].available_pieces)
            elif msg.message_type == MESSAGE_INTERESTED:
                self._is_interested = True
            elif msg.message_type == MESSAGE_UNINTERESTED:
                self._is_interested = False
            elif msg.message_type == MESSAGE_CHOKE:
                self._is_choking = True
            elif msg.message_type == MESSAGE_UNCHOKE:
                self._is_choking = False
            elif msg.message_type == MESSAGE_HAVE:
                self.available_pieces.append(msg.piece_index)


class PeerConnection:
    _timeout = 1

    def __init__(self, ip, port, info_hash, peer_id):
        """Initialize a peer connection class

        Args:
            ip: peer ip
            port: peer port
            info_hash: 20-byte SHA1 hash of the info key in the metainfo file
            peer_id: 20-byte string used as a unique ID for the client
        """

        self._ip = ip
        self._port = port
        self._info_hash = info_hash
        self._peer_id = peer_id
        self._reader = None
        self._writer = None

    async def handshake(self):
        """Open a connection to another peer,
         update self._reader and self._writer and preform a bittorrent handshake

        Returns:
            None
        """

        self._reader, self._writer = await asyncio.open_connection(
            self._ip, self._port
        )

        handshake = HandshakeMessage(self._info_hash, self._peer_id.encode())
        await self.send(handshake.raw)

    async def recv(self):
        """Receive messages from the associated peer

        Returns:
            a list of Message objects received
        """

        messages = []
        data = b""

        while True:
            fut = self._reader.read(1024)
            try:
                data += await asyncio.wait_for(fut, timeout=PeerConnection._timeout)

            except asyncio.TimeoutError as e:
                return messages

            if not data:
                break

            if data.startswith(b'\x13BitTorrent protocol'):
                if len(data) < 68:
                    continue
                else:
                    msg = self.create_peer_message(data[:68])

                    if not self._validate_handshake(msg):
                        raise Exception(f"peer at {self._ip}:{self._port} handshake failed")
                    data = data[len(msg.raw):]

            if len(data) < 4:
                continue

            len_field = struct.unpack(">I", data[:4])[0]
            if len(data) - 4 < len_field:
                continue

            msg = self.create_peer_message(data[:len_field + 4])
            data = data[len_field + 4:]

            messages.append(msg)

            if not data:
                break

        return messages

    async def send(self, data):
        """Send data to the associated peer

        Args:
            data: raw data to be sent

        Returns:
            None
        """

        self._writer.write(data)

    def _validate_handshake(self, handshake):
        """Validate a handshake

        Args:
            handshake: a handshake message object

        Returns:
            True if the handshake is valid, else False
        """

        if handshake.info_hash != self._info_hash or len(handshake.raw) != 68:
            return False

        return True

    @staticmethod
    def create_peer_message(msg):
        """Create a message object from raw message

        Args:
            msg: raw message data

        Returns:
            a peer message object corresponding to the received message
        """

        if len(msg) == 4:
            return KeepAliveMessage()
        elif msg.startswith(b"\x13BitTorrent protocol"):
            return HandshakeMessage.from_msg(msg)
        elif msg[4] == MESSAGE_HAVE:
            return HaveMessage.from_msg(msg)
        elif msg[4] == MESSAGE_BITFIELD:
            return BitfieldMessage.from_msg(msg)
        elif msg[4] == MESSAGE_PIECE:
            return PieceMessage.from_msg(msg)
        elif len(msg) == 5:
            return SimpleMessage.from_msg(msg)

    def __del__(self):
        """Close peer connection

        Returns:
            None
        """

        if self._writer:
            self._writer.close()
