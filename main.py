# This is the starting file of the project.
import sys

from devices import EndDevice
from network.simulator import run_simulation


if __name__ == "__main__":
    if "--server" in sys.argv:
        app_device = EndDevice("BrowserApp", "127.0.0.1", "127.0.0.0/8")
        app_device.start_application_server()
    else:
        # Run all demo test cases from the simulator module.
        run_simulation()
