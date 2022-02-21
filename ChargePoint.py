import asyncio
import logging
import sys

import websockets

from ocpp.v16 import call, ChargePoint as cp
from ocpp.v16.enums import RegistrationStatus


log_file = 'log_info.log'

with open(log_file, 'w+'):
    logger = logging.getLogger('ocpp')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file)
    sh = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)


class ChargePoint(cp):

    async def send_boot_notification(self):
        while True:
            request = call.BootNotificationPayload(
                charge_point_model="WILLBERT Amber I",
                charge_point_vendor=vendor,
                charge_point_serial_number='532821489',
                firmware_version="v.3.4.7",

            )
            response = await self.call(request)

            await asyncio.sleep(response.interval)

            status = "\tRegistration status: "
            if response.status == RegistrationStatus.pending:
                print(status + response.status + '\n')

            if response.status == RegistrationStatus.accepted:
                print(status + response.status + '\n')
                break

            if response.status == RegistrationStatus.rejected:
                print(status + response.status + " - Connection to central system server is rejected.\nYou need to reconnect to the server.")
                break


async def connect_server():
    async with websockets.connect(
            f'ws://localhost:9000/{vendor}',
            subprotocols=['ocpp1.6']
    ) as ws:
        cp = ChargePoint(vendor, ws)

        await asyncio.gather(cp.start(), cp.send_boot_notification())


if __name__ == '__main__':
    try:
        vendor = 'sergei_vorobev'
        asyncio.run(connect_server())
    except AttributeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(connect_server())
        loop.close()

