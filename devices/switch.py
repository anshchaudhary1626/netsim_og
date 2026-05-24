from utils.logger import log


class Switch:
    """A switch learns MAC addresses and forwards frames more intelligently than a hub."""

    def __init__(self, name):
        self.name = name
        # Ports are the devices connected to the switch.
        self.ports = []
        # This table remembers which MAC address is found on which port/device.
        self.mac_table = {}

    def connect(self, device):
        """Connects a device to the switch."""
        if device not in self.ports:
            self.ports.append(device)

    def receive_frame(self, frame, incoming_device):
        """Data link layer frame processing."""
        src_mac = frame['src_mac']
        dest_mac = frame['dest_mac']

        # Learn where the sender lives, so future frames can be sent directly.
        if src_mac not in self.mac_table:
            self.mac_table[src_mac] = incoming_device
            log(
                "Data Link",
                self.name,
                f"MAC Learning: {src_mac} -> Port to {incoming_device.name}"
            )

        # If destination is broadcast, send to all other ports.
        if dest_mac == "ff:ff:ff:ff:ff:ff":
            log("Data Link", self.name, "Broadcast MAC. Flooding all ports.")

            for device in self.ports:
                if device != incoming_device:
                    device.receive_frame(frame, incoming_device=self)

        elif dest_mac in self.mac_table:
            # If destination is known, send only to the correct device.
            target = self.mac_table[dest_mac]
            log(
                "Data Link",
                self.name,
                f"MAC known. Unicasting directly to {target.name}"
            )
            target.receive_frame(frame, incoming_device=self)

        else:
            # If destination is unknown, send to all other ports and let the right one accept it.
            log("Data Link", self.name, "Unknown destination MAC. Flooding frame.")

            for device in self.ports:
                if device != incoming_device:
                    device.receive_frame(frame, incoming_device=self)
