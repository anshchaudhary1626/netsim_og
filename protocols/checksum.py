import zlib


def crc_checksum(data):
    """Create a CRC value so the receiver can check if data changed."""
    checksum = zlib.crc32(str(data).encode())
    return hex(checksum)
