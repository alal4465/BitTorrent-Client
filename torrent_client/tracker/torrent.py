from bencode.decode import bdecode
from bencode.encode import bencode
from hashlib import sha1
import random


class AbstractTorrent:
    def __init__(self, bencoded_data):
        """Initialize a torrent object that represents the metainfo file

        Args:
            bencoded_data: bencoded data. usually the content of a *.torrent file
        """

        torrent_dict = bdecode(bencoded_data)

        self._info = torrent_dict[b'info']

        self.announce_url = torrent_dict[b"announce"].decode()
        self.info_hash = sha1(bencode(self._info)).digest()
        self.peer_id = AbstractTorrent.gen_peer_id()

    @property
    def piece_hashes(self):
        """Return the torrent piece hashes"""
        return [self._info[b"pieces"][i:i + 20] for i in range(0, len(self._info[b"pieces"]), 20)]

    @property
    def request_params(self):
        """Get the tracker request parameters

        Returns:
            a dict representing the tracker request params
        """

        params = dict()

        params["info_hash"] = self.info_hash
        params["peer_id"] = self.peer_id
        params["left"] = str(self.length)
        params["compact"] = "1"
        params["port"] = "59696"
        params["uploaded"] = "0"
        params["downloaded"] = "0"
        params["event"] = "started"

        return params

    @classmethod
    def from_path(cls, path):
        """Initialize a torrent instance from the file path

        Args:
            path: a file path to the *.torrent file

        Returns:
            a torrent class instance
        """

        with open(path, "rb") as f:
            data = f.read()
        return cls(data)

    @classmethod
    def from_dict(cls, torrent_dict):
        """Initialize a torrent instance from the bdecoded torrent dictionary

        Args:
            torrent_dict: the torrent dict representing the metainfo file

        Returns:
            a torrent class instance
        """

        return cls(bencode(torrent_dict))

    @staticmethod
    def gen_peer_id():
        """Generate a peer id"""
        return '-PC0001-' + ''.join([str(random.randint(0, 9)) for _ in range(12)])

    @property
    def piece_length(self):
        """Torrent piece length"""
        return self._info[b"piece length"]

    @property
    def file_name(self):
        """Torrent file name or directory name if contains multiple files"""
        return self._info[b"name"].decode()

    @property
    def length(self):
        """Torrent complete size. Not implemented in the abstract class"""
        raise NotImplementedError()


class SingleFileTorrent(AbstractTorrent):
    def __init__(self, bencoded_data):
        """Initialize a single file torrent

        Args:
            bencoded_data: bencoded data. usually the content of a *.torrent file
        """

        super().__init__(bencoded_data)

    @property
    def length(self):
        """Torrent complete size"""
        return self._info[b"length"]


class MultiFileTorrent(AbstractTorrent):
    def __init__(self, bencoded_data):
        """Initialize a multi file torrent

        Args:
            bencoded_data: bencoded data. usually the content of a *.torrent file
        """

        super().__init__(bencoded_data)

    @property
    def length(self):
        """Torrent complete size"""
        torrent_size = 0
        for file in self.files:
            torrent_size += file[b"length"]

        return torrent_size

    @property
    def files(self):
        """File info from the metainfo file"""
        return self._info[b"files"]
