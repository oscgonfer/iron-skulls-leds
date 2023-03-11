import time
import asyncio
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from threading import currentThread
from queue import Queue
from typing import List, Any
from tools import *
from config import *
from FseqAnimator import *

# Run this to make a forever loop with no sleep
async def loop():
    while True:
        await asyncio.sleep(0)

class UDPBridge(object):
    """
        Makes a bridge between an OSC-UDP async server and a serial
        device. The UDP input is forwarded with some
    """
    def __init__(self):
        super(UDPBridge, self).__init__()

    async def main(self, dispatcher):

        server = AsyncIOOSCUDPServer((SERVER_IP, SERVER_PORT), dispatcher,
                                     asyncio.get_event_loop())
        transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

        self.animator_q = Queue()
        self.animator = FseqAnimator(self.animator_q, currentThread())
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
        self.animator = FseqAnimator(self.animator_q, currentThread())
        self.animator.start()
        self.animator_q.put(msg)

udpbridge = UDPBridge()
dispatcher = Dispatcher()
# Filter OSC messages by "/leds"
dispatcher.map(UDP_FILTER, udpbridge.send)
# Run main fseq2sacn loop
asyncio.run(udpbridge.main(dispatcher))
