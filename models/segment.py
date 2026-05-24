def create_segment(seq_num, src_port, dest_port, payload):
    """Wrap app data with port numbers and a sequence number."""
    return {
        'seq_num': seq_num,
        'src_port': src_port,
        'dest_port': dest_port,
        'payload': payload
    }
