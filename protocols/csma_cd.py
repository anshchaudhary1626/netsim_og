import random
import time

from protocols.checksum import crc_checksum
from utils.logger import log


class DataLinkProtocols:
    """Small simulations of data-link layer rules."""

    # This represents one shared wire/channel. Only one device should use it at a time.
    channel_busy = False
    transmitting_devices = []

    @staticmethod
    def crc_checksum(data):
        # Keep this method so older code can still call DataLinkProtocols.crc_checksum().
        return crc_checksum(data)

    @staticmethod
    def csma_cd(device_name):
        """
        Check if the channel is free, then send.
        If a collision happens, wait for some time and try again.
        """
        MAX_RETRIES = 16
        attempt = 0

        while attempt < MAX_RETRIES:
            # Step 1: Listen first. If someone else is sending, wait.
            if DataLinkProtocols.channel_busy:
                log(
                    "Data Link",
                    device_name,
                    "CSMA/CD: Channel busy. Waiting..."
                )

                wait_time = random.uniform(0.5, 1.5)
                time.sleep(wait_time)
                continue

            # Step 2: The channel is free, so this device starts sending.
            log(
                "Data Link",
                device_name,
                "CSMA/CD: Carrier sensed. Channel idle."
            )

            DataLinkProtocols.channel_busy = True
            DataLinkProtocols.transmitting_devices.append(device_name)

            log(
                "Data Link",
                device_name,
                "CSMA/CD: Beginning transmission..."
            )

            # Step 3: Randomly simulate a collision, like two devices talking together.
            collision_probability = random.random()

            # 30% chance that a collision happens.
            if collision_probability < 0.3:
                log(
                    "Data Link",
                    device_name,
                    "CSMA/CD: COLLISION DETECTED!"
                )

                log(
                    "Data Link",
                    device_name,
                    "CSMA/CD: Sending JAM signal."
                )

                if device_name in DataLinkProtocols.transmitting_devices:
                    DataLinkProtocols.transmitting_devices.remove(device_name)

                DataLinkProtocols.channel_busy = False

                # Step 4: Wait longer after repeated collisions before retrying.
                k = min(attempt, 10)
                backoff_slots = random.randint(0, (2 ** k) - 1)
                backoff_time = backoff_slots * 0.5

                log(
                    "Data Link",
                    device_name,
                    f"CSMA/CD: Backoff for {backoff_time:.2f} seconds."
                )

                time.sleep(backoff_time)
                attempt += 1

            else:
                # Step 5: No collision happened, so the send is successful.
                log(
                    "Data Link",
                    device_name,
                    "CSMA/CD: Transmission successful."
                )

                if device_name in DataLinkProtocols.transmitting_devices:
                    DataLinkProtocols.transmitting_devices.remove(device_name)

                DataLinkProtocols.channel_busy = False
                return True

        log(
            "Data Link",
            device_name,
            "CSMA/CD: Transmission failed after 16 attempts."
        )

        return False
