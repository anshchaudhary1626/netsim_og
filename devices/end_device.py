from http.server import BaseHTTPRequestHandler, HTTPServer
import ipaddress
import random
from urllib.parse import parse_qs, urlparse

from models.frame import create_frame
from models.packet import create_datagram
from models.segment import create_segment
from protocols.csma_cd import DataLinkProtocols
from protocols.go_back_n import simulate_ack as simulate_go_back_n_ack
from protocols.go_back_n import split_data_into_chunks
from utils.logger import generate_mac, log


class EndDevice:
    """A computer or server that can send and receive network data."""

    def __init__(self, name, ip_address, subnet):
        self.name = name
        self.ip_address = ip_address
        self.subnet = subnet
        self.mac_address = generate_mac()

        # connected_link is the cable/device this computer is plugged into.
        self.connected_link = None
        # gateway_ip is used when the destination is outside this computer's subnet.
        self.gateway_ip = None
        # ARP table maps IP addresses to MAC addresses.
        self.arp_table = {}

        # Go-Back-N variables used to track packet sending and receiving.
        self.seq_num = 0
        self.window_size = 4
        self.timeout = 2
        self.sender_window = {}
        self.expected_seq = 0
        # Each separate conversation gets its own expected sequence number.
        self.receiver_expected_seq = {}

        # Application services
        self.services = {
            80: self.http_handler,
            21: self.ftp_handler
        }

    def connect(self, device):
        """Connect this computer to another computer, hub, or switch."""
        if self.connected_link == device:
            return

        self.connected_link = device

        # Also tell the other device about this connection if it supports connect().
        if hasattr(device, 'connect'):
            if getattr(device, 'connected_link', None) != self:
                device.connect(self)

    # Application layer
    def http_handler(self, payload):
        log(
            "Application",
            self.name,
            f"HTTP Request Received: {payload}"
        )

        return "HTTP 200 OK"

    def ftp_handler(self, payload):
        log(
            "Application",
            self.name,
            f"FTP Request Received: {payload}"
        )

        return "FTP FILE SENT"

    def start_application_server(self, host="127.0.0.1", port=8080):
        """
        Start a small real HTTP server for browser testing.
        Browser path /http calls this device's HTTP application handler.
        """
        device = self

        class ApplicationRequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed_url = urlparse(self.path)
                query = parse_qs(parsed_url.query)
                payload = query.get("payload", ["BROWSER_TEST_MESSAGE"])[0]

                if parsed_url.path == "/":
                    self.send_text(
                        "Application Layer Test Server\n\n"
                        "Open this URL in your browser:\n"
                        f"http://{host}:{port}/http?payload=GET_INDEX_HTML_FILE\n"
                    )
                    return

                if parsed_url.path == "/http":
                    response = device.http_handler(payload)
                    self.send_text(
                        "HTTP Application Service\n"
                        f"Device: {device.name}\n"
                        f"Request payload: {payload}\n"
                        f"Response: {response}\n"
                    )
                    return

                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found. Try /http.")

            def send_text(self, body):
                encoded_body = body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded_body)))
                self.end_headers()
                self.wfile.write(encoded_body)

            def log_message(self, format, *args):
                log("Application", device.name, format % args)

        server = HTTPServer((host, port), ApplicationRequestHandler)

        log(
            "Application",
            self.name,
            f"Browser test server running at http://{host}:{port}"
        )
        log(
            "Application",
            self.name,
            f"HTTP test URL: http://{host}:{port}/http?payload=GET_INDEX_HTML_FILE"
        )

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            log("Application", self.name, "Browser test server stopped.")
        finally:
            server.server_close()

    def generate_ephemeral_port(self):
        """Create a temporary source port for this outgoing communication."""
        return random.randint(49152, 65535)

    # Go-Back-N transport layer
    def start_communication(self, data, dest_ip, dest_port):
        """Start sending application data to a destination IP and port."""
        src_port = self.generate_ephemeral_port()

        log(
            "Application",
            self.name,
            f"Application started | SRC PORT={src_port} DEST PORT={dest_port}"
        )

        log(
            "Transport",
            self.name,
            f"GO-BACK-N Started | Window Size={self.window_size}"
        )

        chunks = split_data_into_chunks(data)
        total_packets = len(chunks)

        # base is the first packet in the current sending window.
        base = 0
        # next_seq is the next packet number that should be sent.
        next_seq = 0

        while base < total_packets:
            # Send all packets that fit inside the current Go-Back-N window.
            while (
                next_seq < base + self.window_size and
                next_seq < total_packets
            ):
                segment = create_segment(
                    next_seq,
                    src_port,
                    dest_port,
                    chunks[next_seq]
                )

                log(
                    "Transport",
                    self.name,
                    f"Sending Segment SEQ={next_seq}"
                )

                self.sender_window[next_seq] = segment
                # After transport creates a segment, pass it down to the network layer.
                self.pass_to_network(segment, dest_ip)
                next_seq += 1

            # Wait for an ACK for the first unconfirmed packet.
            ack = self.simulate_ack(base)

            if ack is not None:
                log(
                    "Transport",
                    self.name,
                    f"ACK RECEIVED for SEQ={ack}"
                )

                base = ack + 1

            else:
                # If ACK is lost, Go-Back-N sends the whole unconfirmed window again.
                log(
                    "Transport",
                    self.name,
                    f"TIMEOUT! Go-Back-N Retransmission from SEQ={base}"
                )

                for seq in range(base, next_seq):
                    log(
                        "Transport",
                        self.name,
                        f"Retransmitting SEQ={seq}"
                    )

                    self.pass_to_network(
                        self.sender_window[seq],
                        dest_ip
                    )

    def simulate_ack(self, current_base):
        """Use the protocol helper to imitate receiving an ACK."""
        return simulate_go_back_n_ack(self.name, current_base)

    # Network layer
    def pass_to_network(self, segment, dest_ip):
        """Wrap the transport segment inside an IP datagram."""
        datagram = create_datagram(
            self.ip_address,
            dest_ip,
            64,
            segment
        )

        log(
            "Network",
            self.name,
            f"Encapsulating Datagram -> {dest_ip}"
        )

        target_ip = dest_ip
        network = ipaddress.ip_network(
            self.subnet,
            strict=False
        )

        # If destination is outside this subnet, send the frame to the router first.
        if ipaddress.ip_address(dest_ip) not in network:
            target_ip = self.gateway_ip

            log(
                "Network",
                self.name,
                f"Using Default Gateway {self.gateway_ip}"
            )

        dest_mac = self.resolve_arp(target_ip)
        self.pass_to_datalink(datagram, dest_mac)

    def resolve_arp(self, target_ip):
        """Find the MAC address for an IP address using the ARP table."""
        if target_ip in self.arp_table:
            log(
                "Network",
                self.name,
                f"ARP HIT: {target_ip}"
            )

            return self.arp_table[target_ip]

        log(
            "Network",
            self.name,
            f"ARP MISS: Broadcasting ARP Request"
        )

        # Broadcast MAC means "send this to everyone on the local network."
        return "ff:ff:ff:ff:ff:ff"

    # Data link layer
    def pass_to_datalink(self, datagram, dest_mac):
        """Wrap the IP datagram inside a frame and send it to the link."""
        success = DataLinkProtocols.csma_cd(self.name)

        if not success:
            log(
                "Data Link",
                self.name,
                "Transmission Failed"
            )

            return

        frame = create_frame(
            self.mac_address,
            dest_mac,
            datagram
        )

        log(
            "Data Link",
            self.name,
            f"Frame Created | DEST MAC={dest_mac}"
        )

        log(
            "Physical",
            self.name,
            "Sending bits over medium"
        )

        if self.connected_link:
            # Give the frame to whatever this device is connected to.
            self.connected_link.receive_frame(
                frame,
                incoming_device=self
            )

    # Receiving side
    def receive_frame(self, frame, incoming_device=None):
        """Receive a frame and unwrap it layer by layer."""

        # First check if this frame is meant for this device.
        if (
            frame['dest_mac'] != self.mac_address and
            frame['dest_mac'] != "ff:ff:ff:ff:ff:ff"
        ):
            return

        log(
            "Physical",
            self.name,
            "Bits Received"
        )

        # Recalculate CRC and compare it with the sender's CRC.
        calculated_crc = DataLinkProtocols.crc_checksum(
            frame['payload']
        )

        if frame['crc'] != calculated_crc:
            log(
                "Data Link",
                self.name,
                "CRC ERROR! Frame Dropped"
            )

            return

        log(
            "Data Link",
            self.name,
            "CRC Check Passed"
        )

        datagram = frame['payload']

        # Then check if the IP packet is meant for this device.
        if (
            datagram['dest_ip'] != self.ip_address and
            datagram['dest_ip'] != "255.255.255.255"
        ):
            return

        log(
            "Network",
            self.name,
            f"Datagram received for {self.ip_address}"
        )

        segment = datagram['payload']
        seq = segment['seq_num']
        flow_key = (
            datagram['src_ip'],
            segment['src_port'],
            segment['dest_port']
        )
        expected_seq = self.receiver_expected_seq.get(flow_key, 0)

        # Go-Back-N accepts packets only in the expected order.
        if seq == expected_seq:
            log(
                "Transport",
                self.name,
                f"Correct Packet Received SEQ={seq}"
            )

            log(
                "Transport",
                self.name,
                f"ACK Sent for SEQ={seq}"
            )

            self.receiver_expected_seq[flow_key] = expected_seq + 1
            self.expected_seq = expected_seq + 1

            dest_port = segment['dest_port']

            # Port number decides which application service receives the data.
            if dest_port in self.services:
                response = self.services[dest_port](
                    segment['payload']
                )

                log(
                    "Application",
                    self.name,
                    f"Response: {response}"
                )

            else:
                log(
                    "Transport",
                    self.name,
                    f"Port {dest_port} unreachable"
                )

        else:
            # Out-of-order packets are thrown away in Go-Back-N.
            log(
                "Transport",
                self.name,
                f"Out-of-order Packet! Expected={expected_seq}, Got={seq}"
            )

            log(
                "Transport",
                self.name,
                f"Discarding Packet SEQ={seq}"
            )

            log(
                "Transport",
                self.name,
                f"Re-sending ACK for SEQ={expected_seq - 1}"
            )
