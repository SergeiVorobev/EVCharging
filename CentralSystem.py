import asyncio
import websockets
import logging
from datetime import datetime

from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import Action, RegistrationStatus
from ocpp.v16 import call_result


logging.basicConfig(level=logging.DEBUG)

start_conn = datetime.utcnow()
interval = 0
current_delay = 0
counter = 0
response_time = datetime.utcnow()

class ChargePoint(cp):

    @on(Action.BootNotification)
    async def on_boot_notitication(self, charge_point_vendor, charge_point_model,  **kwargs):
        global counter
        global cur_t
        global current_delay
        global response_time
        delay = 1.5
        time_cp_request = datetime.utcnow()
        connection_time = (time_cp_request - start_conn).total_seconds()
        counter += 1

        logging.info(f"CONNECTION TIME {connection_time}")
        logging.info(f"COUNT {counter}")

        if counter == 1:
            """ find delay """
            current_delay = connection_time % interval

        if counter > 1:
            logging.info(f"CS response {response_time}")
            logging.info(f"CP request {time_cp_request}")

            """ find delay """
            current_delay = (time_cp_request - response_time).total_seconds() - interval

        logging.info(f"DELAY {current_delay}")

        status = RegistrationStatus.pending

        """ check delay with 1.5s tolerance """
        if current_delay > delay: status = RegistrationStatus.rejected

        """ assign RegistrationStatus 'accepted' """
        if counter > 10: status = RegistrationStatus.accepted

        response_time = datetime.utcnow()
        return call_result.BootNotificationPayload(
                current_time=response_time.isoformat(),
                interval=interval,
                status=status,
            )

async def on_connect(websocket, path):
    """ For every new charge point that connects, create a ChargePoint
    instance and start listening for messages.
    """
    try:
        requested_protocols = websocket.request_headers[
            'Sec-WebSocket-Protocol']
    except KeyError:
        logging.info("Client hasn't requested any Subprotocol. "
                     "Closing Connection")
    if websocket.subprotocol:
        logging.info("Protocols Matched: %s", websocket.subprotocol)
    else:
        # In the websockets lib if no subprotocols are supported by the
        # client and the server, it proceeds without a subprotocol,
        # so we have to manually close the connection.
        logging.warning('Protocols Mismatched | Expected Subprotocols: %s,'
                        ' but client supports  %s | Closing connection',
                        websocket.available_subprotocols,
                        requested_protocols)
        return await websocket.close()

    charge_point_id = path.strip('/')
    cp = ChargePoint(charge_point_id, websocket)

    global start_conn
    start_conn = datetime.utcnow()
    logging.info(f"START connection time: {start_conn}")

    await cp.start()


async def run_server(interv):
    server = await websockets.serve(
        on_connect,
        '127.0.0.1',
        # '167.172.177.42',
        9000,
        subprotocols=['ocpp1.6']
    )
    global interval
    interval = interv
    logging.info("WebSocket Server Started")
    await server.wait_closed()


if __name__ == '__main__':
    asyncio.run(run_server(6))
