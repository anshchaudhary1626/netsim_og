from protocols.checksum import crc_checksum


def create_frame(src_mac, dest_mac, payload):
    """Wrap a network packet with MAC addresses, like putting it in a local envelope."""
    return {
        'src_mac': src_mac,
        'dest_mac': dest_mac,
        'payload': payload,
        'crc': crc_checksum(payload)
    }
