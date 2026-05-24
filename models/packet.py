def create_datagram(src_ip, dest_ip, ttl, payload):
    """Wrap a transport segment with IP addresses, like writing city addresses."""
    return {
        'src_ip': src_ip,
        'dest_ip': dest_ip,
        'ttl': ttl,
        'payload': payload
    }
