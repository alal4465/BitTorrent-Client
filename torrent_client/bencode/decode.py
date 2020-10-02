def bdecode(data):
    """Bdecodes python data

    Args:
        data: bencoded data

    Returns:
        decoded python bytes, dictionary, list or integer
    """

    if data[0] == ord('i'):
        return _parse_integer(data)[1]
    elif data[0] == ord('l'):
        return _parse_list(data)[1]
    elif data[0] == ord('d'):
        return _parse_dict(data)[1]
    elif chr(data[0]).isdigit():
        return _parse_bstr(data)[1]


def _decode_internal(data):
    """Internal bdecoding function

    Args:
        data: bencoded data

    Returns:
        a tuple consisting of (leftover data, decoded data)
    """

    if data[0] == ord('i'):
        return _parse_integer(data)
    elif data[0] == ord('l'):
        return _parse_list(data)
    elif data[0] == ord('d'):
        return _parse_dict(data)
    elif chr(data[0]).isdigit():
        return _parse_bstr(data)


def _parse_dict(data):
    """Bdecodes a python dictionary

    Args:
        data: a bencoded dict

    Returns:
        decoded dict
    """

    res_dict = {}

    data = data[1:]

    while data[0] != ord('e'):
        data, key = _decode_internal(data)
        data, value = _decode_internal(data)

        res_dict[key] = value

    return data[1:], res_dict


def _parse_bstr(data):
    """Bdecodes python bytes

    Args:
        data: bencoded bytes

    Returns:
        decoded bytes
    """

    length = int(data.split(b':')[0])
    bstr = data[data.find(b':') + 1:length + data.find(b':') + 1]

    return data[data.find(b':') + 1 + length:], bstr


def _parse_integer(data):
    """Bdecodes python integer

    Args:
        data: a bencoded integer

    Returns:
        a decoded integer
    """

    data = data[1:]
    value = int(data.split(b'e')[0])

    return data[data.find(b'e') + 1:], value


def _parse_list(data):
    """Bdecodes a python list

    Args:
        data: a bencoded list

    Returns:
        a decoded list
    """

    l = []
    data = data[1:]

    while data[0] != ord('e'):
        data, val = _decode_internal(data)
        l.append(val)

    return data[1:], l
