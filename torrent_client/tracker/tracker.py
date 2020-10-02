from .torrent import SingleFileTorrent, MultiFileTorrent
from bencode.decode import bdecode
from peer.peer import Peer
from .file_saver import FileSaver
from .blocks import BlockManager
import random
import asyncio
import aiohttp
import yarl
import urllib.parse
import ipaddress
import struct


class Tracker:
    def __init__(self, torrent_dict, progress_bar):
        """Initialize a tracker object

        Args:
            torrent_dict: a torrent dict that represents the *.torrent file
            progress_bar: a gui progress bar to be updated as the download progresses
        """

        if b"files" in torrent_dict[b"info"]:
            self._torrent = MultiFileTorrent.from_dict(torrent_dict)
        else:
            self._torrent = SingleFileTorrent.from_dict(torrent_dict)

        self._blocks = BlockManager(self._torrent)
        self._file_saver = FileSaver(self._torrent, progress_bar)
        self._peers = []
        self._interval = 0

    async def download(self):
        """Download the torrent file and save its contents

        Returns:
            None
        """

        if not self._peers and not self._interval:
            self._peers, self._interval = await self._request_peers()

        await self._handshake_peers()

        while not self._blocks.empty():
            scheduled = []
            tasks = []
            blocks = []

            for block in self._blocks:
                scheduled_peers = [tup[0] for tup in scheduled]

                try:
                    peer = random.choice([peer for peer in self._peers if
                            block.index in peer.available_pieces and
                            peer not in scheduled_peers])

                    scheduled.append((peer, block))
                except IndexError:
                    blocks.append(block)

            self._blocks.extend_blocks(blocks)

            for tup in scheduled:
                tasks.append(asyncio.create_task(tup[0].download(tup[1])))

            results = await asyncio.gather(*tasks)

            for i, downloaded in enumerate(results):
                if downloaded:
                    self._file_saver.append(downloaded)
                else:
                    self._blocks.add_block(scheduled[i][1])

                self._blocks.extend_blocks(self._file_saver.get_failed_blocks())

        self._file_saver.save()

    async def _handshake_peers(self):
        """Handshake the peers and update the pool of peers to contain only the ones whose handshake was successful

        Returns:
            None
        """

        tasks = []
        for peer in self._peers:
            if not peer.handshake_complete:
                tasks.append(asyncio.create_task(peer.handshake()))

        if tasks:
            await asyncio.gather(*tasks)

        self._peers = [peer for peer in self._peers if peer.handshake_complete]

    async def _request_peers(self):
        """Request peers from the tracker server

        Returns:
            a tuple consisting of (peers list, interval)
        """

        peers_list = []

        params = {name: urllib.parse.quote(value) if isinstance(value, bytes) else value
                  for name, value in self._torrent.request_params.items()}

        url = yarl.URL(self._torrent.announce_url).update_query(params)
        url = urllib.parse.unquote(str(url))

        async with aiohttp.ClientSession() as session:
            r = await session.get(url)
            content = await r.read()
            peers_dict = bdecode(content)

        interval = peers_dict[b'interval']

        if isinstance(peers_dict[b'peers'], list):
            for peer in peers_dict[b'peers']:
                peers_list.append(Peer(peer[b"ip"].decode(), peer[b"port"], self._torrent))
        elif isinstance(peers_dict[b'peers'], bytes):
            bstr = peers_dict[b'peers']
            while bstr:
                addr_bytes, port_bytes = (
                    bstr[:4], bstr[4:6]
                )
                ip_addr = str(ipaddress.IPv4Address(addr_bytes))
                port_bytes = struct.unpack('>H', port_bytes)[0]
                peers_list.append(Peer(ip_addr, port_bytes, self._torrent))

                bstr = bstr[6:]

        return peers_list, interval

    def get_peers(self):
        """Get the tracker peers"""
        return self._peers

    @classmethod
    def from_path(cls, file_path, progress_bar):
        """Initialize a tracker instance from a given path

        Args:
            file_path: the *.torrent file path
            progress_bar: a gui progress bar to be updated as the download progresses

        Returns:
            a tracker instance
        """

        with open(file_path, "rb") as f:
            data = f.read()

        return cls(bdecode(data), progress_bar)

    @property
    def torrent_name(self):
        """The torrent file name"""
        return self._torrent.file_name
