import random


def generate_mac():
    """Create a fake MAC address for a simulated network device."""
    return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))


def log(layer, device_name, message):
    """Print what is happening, along with the network layer and device name."""
    print(f"[{layer.upper():<11}] [{device_name:<10}] {message}")
