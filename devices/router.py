import copy
import ipaddress

from protocols.csma_cd import DataLinkProtocols
from utils.logger import generate_mac, log


class Router:
    """A router moves packets between different IP networks."""

    def __init__(self, name):
        self.name = name
        # Each interface is like one router port with its own IP address.
        self.interfaces = {}
        # This tells which switch/hub is connected to each router interface.
        self.connected_devices = {}
        # The routing table tells the router where to send packets next.
        self.routing_table = {}
        self.mac_address = generate_mac()

    def configure_interface(self, interface_name, router_ip, network_prefix, connected_device):
        """Give one router interface an IP address and connect it to a network."""
        self.interfaces[interface_name] = router_ip
        self.connected_devices[interface_name] = connected_device

        # A directly connected route means this router is already attached to that network.
        self.routing_table[network_prefix] = {
            "interface": interface_name,
            "next_hop": "0.0.0.0",
            "metric": 0
        }

        connected_device.connect(self)
        log(
            "Network",
            self.name,
            f"Configured {interface_name}: IP {router_ip} on subnet {network_prefix}"
        )

    def add_static_route(self, network_prefix, next_hop, interface):
        """Manually add a route, like telling the router a known road."""
        self.routing_table[network_prefix] = {
            "interface": interface,
            "next_hop": next_hop,
            "metric": 1
        }
        log("Network", self.name, f"Static Route added: {network_prefix} via {next_hop}")

    def add_rip_route(self, network_prefix, next_hop, metric):
        """Pretend a RIP update taught this router a route."""
        self.routing_table[network_prefix] = {
            "interface": "eth0",
            "next_hop": next_hop,
            "metric": metric
        }
        log(
            "Network",
            self.name,
            f"RIP Route updated: {network_prefix} via {next_hop} [Metric {metric}]"
        )

    def longest_mask_match(self, dest_ip):
        """Find the most specific route that matches the destination IP."""
        best_match = None
        longest_prefix = -1
        destination = ipaddress.ip_address(dest_ip)

        for prefix in self.routing_table:
            network = ipaddress.ip_network(prefix, strict=False)

            # Example: 192.168.100.50 belongs inside 192.168.100.0/24.
            if destination in network:
                if network.prefixlen > longest_prefix:
                    longest_prefix = network.prefixlen
                    best_match = prefix

        return best_match

    def receive_frame(self, frame, incoming_device):
        """Take a frame, read the IP packet inside it, and forward it."""
        datagram = frame['payload']

        # TTL prevents a packet from travelling forever in a loop.
        if datagram['ttl'] <= 1:
            log("Network", self.name, "TTL expired. Packet dropped.")
            return

        datagram['ttl'] -= 1

        dest_ip = datagram['dest_ip']
        log("Network", self.name, f"Packet received for {dest_ip}")

        # Look in the routing table to decide where the packet should go.
        matched_route = self.longest_mask_match(dest_ip)

        if not matched_route:
            log("Network", self.name, "No route to host. Dropped.")
            return

        route = self.routing_table[matched_route]
        out_interface = route['interface']
        outgoing_network = self.connected_devices[out_interface]
        log("Network", self.name, f"Routing via {matched_route} out {out_interface}")

        # Find the MAC address of the final device if it is on the outgoing network.
        next_hop_mac = "ff:ff:ff:ff:ff:ff"

        if hasattr(outgoing_network, 'ports'):
            for device in outgoing_network.ports:
                if hasattr(device, 'ip_address') and device.ip_address == dest_ip:
                    next_hop_mac = device.mac_address

        # Build a new frame because the packet is now leaving through the router.
        new_frame = copy.deepcopy(frame)
        new_frame['src_mac'] = self.mac_address
        new_frame['dest_mac'] = next_hop_mac
        new_frame['crc'] = DataLinkProtocols.crc_checksum(new_frame['payload'])

        # Send the frame into the next connected network.
        outgoing_network.receive_frame(new_frame, incoming_device=self)
