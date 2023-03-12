import time
import asyncio
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from threading import current_thread
from queue import Queue
from typing import List, Any
from tools import *
from config import *
from FseqAnimator import *

# Run this to make a forever loop with no sleep
async def loop():
    while True:
        # This can't be 0, as it will load the cpu like crazy...
        await asyncio.sleep(0.001)

class UDPBridge(object):
    def __init__(self):
        super(UDPBridge, self).__init__()

    async def main(self, dispatcher):

        server = AsyncIOOSCUDPServer((SERVER_IP, SERVER_PORT), dispatcher,
                                     asyncio.get_event_loop())
        # Create datagram endpoint and start serving
        transport, protocol = await server.create_serve_endpoint()

        self.animator_q = Queue()
        self.animator = FseqAnimator(self.animator_q, current_thread())
        self.animator.start()

        await loop()
        transport.close()  # Clean up serve endpoint

    def send(self, *args: List[Any]) -> None:
        std_out (f'{time.strftime("%H:%M:%S %d-%m-%Y")}: {args[0]}\n', 'SACN')

        # We just remove the UDP_FILTER
        msg = args[0].replace(UDP_FILTER[:-1], '')

        # Kill the running thread, start a new one.
        # TODO Maybe better with notify?
        self.animator.stop()
        self.animator = FseqAnimator(self.animator_q, current_thread())
        self.animator.start()
        self.animator_q.put(msg)

udpbridge = UDPBridge()
dispatcher = Dispatcher()
# Filter OSC messages by "/leds"
dispatcher.map(UDP_FILTER, udpbridge.send)
# Run main loop
asyncio.run(udpbridge.main(dispatcher))
