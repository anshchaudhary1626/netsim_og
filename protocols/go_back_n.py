import random
import time

from utils.logger import log


def split_data_into_chunks(data):
    """Break the message into smaller words so each word can act like one packet."""
    chunks = data.split()

    if not chunks:
        # If the message has no spaces or is empty, still send it as one piece.
        chunks = [data]

    return chunks


def simulate_ack(device_name, current_base):
    """Pretend the receiver sends an ACK, with a small chance that the ACK is lost."""
    time.sleep(1)

    # 25% chance that the ACK gets lost in the network.
    if random.random() < 0.25:
        log(
            "Transport",
            device_name,
            "ACK LOST!"
        )

        return None

    return current_base
