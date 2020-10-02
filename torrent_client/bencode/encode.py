def bencode(data):
    """Bencodes python data

    Args:
        data: python bytes, dictionary, list or integer to be encoded

    Returns:
        data encoded in the bencode format
    """

    if type(data) is int:
        return _encode_integer(data)
    elif type(data) is list:
        return _encode_list(data)
    elif type(data) is dict:
        return _encode_dict(data)
    elif type(data) is bytes:
        return _encode_bstr(data)


def _encode_dict(data):
    """Bencodes a python dict

    Args:
        data: a python dictionary to be encoded

    Returns:
        dictionary encoded in the bencode format
    """

    bstr = b"d"

    for key, val in data.items():
        bstr += bencode(key)
        bstr += bencode(val)

    bstr += b"e"

    return bstr


def _encode_bstr(data):
    """Bencodes python bytes

    Args:
        data: python bytes to be encoded

    Returns:
        binary string encoded in the bencode format
    """

    return f"{len(data)}:".encode() + data


def _encode_integer(data):
    """Bencodes a python integer

    Args:
        data: a python integer to be encoded

    Returns:
        integer encoded in the bencode format
    """

    return f"i{str(data)}e".encode()


def _encode_list(data):
    """Bencodes a python list

    Args:
        data: a python list to be encoded

    Returns:
        list encoded in the bencode format
    """

    bstr = b"l"

    for val in data:
        bstr += bencode(val)

    bstr += b"e"
    return bstr


