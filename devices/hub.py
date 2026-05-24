from utils.logger import log


class Hub:
    """A hub repeats the same signal to every connected device."""

    def __init__(self, name):
        self.name = name
        # Ports are the devices plugged into this hub.
        self.ports = []

    def connect(self, device):
        """Connects a device to the hub."""
        if device not in self.ports:
            self.ports.append(device)

    def receive_frame(self, frame, incoming_device):
        """Send the incoming frame to everyone except the sender."""
        log(
            "Physical",
            self.name,
            f"Signal received from {incoming_device.name}. Broadcasting to all other ports."
        )

        for device in self.ports:
            # Do not send the frame back to the device that just sent it.
            if device != incoming_device:
                device.receive_frame(frame, incoming_device=self)
