from datetime import datetime, timedelta
import asyncio

class CLI:
    def __init__(self):
        return

    async def get_dependencies(self):
        return ['']

    async def setup_comms(in_port, out_port):
        pass

    def tick(self, message):
        print('CLI Recieved A Message: ' + message)