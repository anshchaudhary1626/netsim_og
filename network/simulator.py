from devices import EndDevice, Hub, Router, Switch


def run_simulation():
    """Build sample networks and send test messages through them."""
    print("\n" + "=" * 75)
    print(" ITL351: COMPLETE NETWORK PROTOCOL STACK SIMULATOR (Sub 1, 2, 3)")
    print("=" * 75)

    # --------------------------------------------------------------------------
    # SUBMISSION 1: TEST CASE 1 (Dedicated Connection)
    # --------------------------------------------------------------------------
    # Two computers are directly connected, so no hub, switch, or router is needed.
    print("\n[SUBMISSION 1: TEST CASE 1] - Dedicated Connection between 2 Devices")
    pc_a = EndDevice("PC-A", "10.0.0.1", "10.0.0.0/24")
    pc_b = EndDevice("PC-B", "10.0.0.2", "10.0.0.0/24")

    # Connect PC-A directly to PC-B.
    pc_a.connect(pc_b)

    # Pre-fill ARP so PC-A already knows PC-B's MAC address.
    pc_a.arp_table["10.0.0.2"] = pc_b.mac_address
    pc_a.start_communication("PING_MESSAGE", "10.0.0.2", 80)

    # --------------------------------------------------------------------------
    # SUBMISSION 1: TEST CASE 2 (Star Topology - Hub)
    # --------------------------------------------------------------------------
    # A hub sends every incoming frame to every connected device.
    print("\n[SUBMISSION 1: TEST CASE 2] - 1 Hub, 5 End Devices")
    hub1 = Hub("Hub1")
    hub_pcs = [
        EndDevice(f"HubPC{i}", f"192.168.1.{i}", "192.168.1.0/24")
        for i in range(1, 6)
    ]

    for pc in hub_pcs:
        pc.connect(hub1)

    # HubPC1 sends to HubPC3 using HubPC3's MAC address.
    hub_pcs[0].arp_table["192.168.1.3"] = hub_pcs[2].mac_address
    hub_pcs[0].start_communication("HELLO_HUB_BROADCAST", "192.168.1.3", 80)
    print("\n>>> DOMAINS: Broadcast Domains = 1, Collision Domains = 1 (Hub combines all into one collision domain)")

    # --------------------------------------------------------------------------
    # SUBMISSION 1: TEST CASE 3 (Switch with 5 Devices)
    # --------------------------------------------------------------------------
    # A switch learns MAC addresses and tries to avoid sending frames everywhere.
    print("\n[SUBMISSION 1: TEST CASE 3] - 1 Switch, 5 End Devices (Address Learning)")
    sw1 = Switch("Switch1")
    sw_pcs = [
        EndDevice(f"SwPC{i}", f"172.16.0.{i}", "172.16.0.0/24")
        for i in range(1, 6)
    ]

    for pc in sw_pcs:
        pc.connect(sw1)

    # First send: the switch does not know the destination yet, so it floods.
    sw_pcs[0].start_communication("FLOOD_MSG", "172.16.0.4", 80)

    # Pre-fill ARP so the sender can use the destination MAC address next time.
    sw_pcs[0].arp_table["172.16.0.4"] = sw_pcs[3].mac_address
    print("\n--- Sending again (Switch learned MAC, so it will Unicast now) ---")
    sw_pcs[0].start_communication("UNICAST_MSG", "172.16.0.4", 80)
    print("\n>>> DOMAINS: Broadcast Domains = 1, Collision Domains = 5 (Switch separates collision domains per port)")

    # --------------------------------------------------------------------------
    # SUBMISSION 1: TEST CASE 4 (Two Hubs, One Switch, 10 Devices)
    # --------------------------------------------------------------------------
    # This creates a larger LAN: two hub groups connected through one switch.
    print("\n[SUBMISSION 1: TEST CASE 4] - 2 Hubs connected via 1 Switch (10 Devices total)")
    core_sw = Switch("CoreSwitch")
    h_left = Hub("LeftHub")
    h_right = Hub("RightHub")

    core_sw.connect(h_left)
    core_sw.connect(h_right)

    left_pcs = [
        EndDevice(f"L_PC{i}", f"10.1.1.{i}", "10.1.1.0/24")
        for i in range(1, 6)
    ]
    right_pcs = [
        EndDevice(f"R_PC{i}", f"10.1.1.{i + 5}", "10.1.1.0/24")
        for i in range(1, 6)
    ]

    for pc in left_pcs:
        pc.connect(h_left)

    for pc in right_pcs:
        pc.connect(h_right)

    # Send data from the left hub side to a PC on the right hub side.
    left_pcs[0].arp_table[right_pcs[4].ip_address] = right_pcs[4].mac_address
    left_pcs[0].start_communication("CROSS_HUB_DATA", right_pcs[4].ip_address, 21)
    print("\n>>> DOMAINS: Broadcast Domains = 1, Collision Domains = 2 (Switch separates the two hubs into distinct collision domains)")

    # --------------------------------------------------------------------------
    # SUBMISSIONS 2 & 3: FULL STACK TEST (Routing, IP, Subnets, Ports, App layer)
    # --------------------------------------------------------------------------
    # This test shows two different IP networks connected by a router.
    print("\n[SUBMISSIONS 2 & 3] - Full Stack Routing, HTTP/FTP, Ports, IPv4 CIDR")

    router = Router("GatewayRouter")

    # Setup Subnet A: the client side of the network.
    sw_a = Switch("SwitchA")
    client_pc = EndDevice("ClientPC", "10.20.30.5", "10.20.30.0/24")
    client_pc.connect(sw_a)
    client_pc.gateway_ip = "10.20.30.1"

    # Setup Subnet B: the server side of the network.
    sw_b = Switch("SwitchB")
    server_pc = EndDevice("HTTPServer", "192.168.100.50", "192.168.100.0/24")
    server_pc.connect(sw_b)
    server_pc.gateway_ip = "192.168.100.1"

    # Give the router one interface in each subnet.
    router.configure_interface("eth0", "10.20.30.1", "10.20.30.0/24", sw_a)
    router.configure_interface("eth1", "192.168.100.1", "192.168.100.0/24", sw_b)

    # Add one static route to demonstrate manual routing.
    router.add_static_route("0.0.0.0/0", "10.20.30.254", "eth0")

    # Demonstrate RIP using Bellman-Ford on three routers.
    print("\n--- RIP Bellman-Ford Dynamic Routing Demo ---")
    rip_r1 = Router("RIP-R1")
    rip_r2 = Router("RIP-R2")
    rip_r3 = Router("RIP-R3")

    rip_sw1 = Switch("RIP-Switch1")
    rip_sw2 = Switch("RIP-Switch2")
    rip_sw3 = Switch("RIP-Switch3")
    rip_link12 = Switch("RIP-Link12")
    rip_link23 = Switch("RIP-Link23")
    rip_link13 = Switch("RIP-Link13")

    rip_r1.configure_interface("eth0", "10.50.1.1", "10.50.1.0/24", rip_sw1)
    rip_r2.configure_interface("eth0", "10.50.2.1", "10.50.2.0/24", rip_sw2)
    rip_r3.configure_interface("eth0", "10.50.3.1", "10.50.3.0/24", rip_sw3)

    rip_r1.configure_interface("eth1", "172.16.12.1", "172.16.12.0/30", rip_link12)
    rip_r2.configure_interface("eth1", "172.16.12.2", "172.16.12.0/30", rip_link12)
    rip_r2.configure_interface("eth2", "172.16.23.1", "172.16.23.0/30", rip_link23)
    rip_r3.configure_interface("eth1", "172.16.23.2", "172.16.23.0/30", rip_link23)
    rip_r1.configure_interface("eth2", "172.16.13.1", "172.16.13.0/30", rip_link13)
    rip_r3.configure_interface("eth2", "172.16.13.2", "172.16.13.0/30", rip_link13)

    # R1 can reach R3 directly with metric 5, but Bellman-Ford should find
    # the better path R1 -> R2 -> R3 with total metric 2.
    rip_r1.add_rip_neighbor(rip_r2, "eth1", "172.16.12.2", metric=1)
    rip_r2.add_rip_neighbor(rip_r1, "eth1", "172.16.12.1", metric=1)
    rip_r2.add_rip_neighbor(rip_r3, "eth2", "172.16.23.2", metric=1)
    rip_r3.add_rip_neighbor(rip_r2, "eth1", "172.16.23.1", metric=1)
    rip_r1.add_rip_neighbor(rip_r3, "eth2", "172.16.13.2", metric=5)
    rip_r3.add_rip_neighbor(rip_r1, "eth2", "172.16.13.1", metric=5)

    Router.run_rip_bellman_ford([rip_r1, rip_r2, rip_r3])

    # Pre-fill tables so the demo focuses on routing instead of extra ARP broadcasts.
    client_pc.arp_table["10.20.30.1"] = router.mac_address
    router.connected_devices["eth1"].mac_table[server_pc.mac_address] = server_pc

    # Send HTTP traffic across the router.
    print("\n--- Client Requesting Web Page from Server across subnets (Port 80) ---")
    client_pc.start_communication("GET_INDEX_HTML_FILE", "192.168.100.50", 80)

    # Send FTP traffic across the same route.
    print("\n--- Client Requesting File via FTP across subnets (Port 21) ---")
    client_pc.start_communication("RETR_FILE_TXT_DATA", "192.168.100.50", 21)

    print("\n" + "=" * 75)
    print(" SIMULATION SUCCESSFULLY COMPLETED.")
    print("=" * 75)
