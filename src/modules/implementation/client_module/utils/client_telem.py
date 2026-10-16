# -*- coding: utf-8 -*-
"""
ARTIFICIAL INTELLIGENCE RESEARCH CENTER

Running in ВЬЮГА
@author: STARK

Created in Oct 2025
"""

import asyncio
from socketio import AsyncNamespace as AN


class ClientTelemetryNS(AN):

    def __init__(self, namespace, receiver):
        super().__init__(namespace)
        self.receiver = receiver

    async def on_connect(self, sid, environ, auth):
        print(f"[connect] {sid} (auth={auth})")
        if not await self.receiver.client_auth(sid, environ, auth):
            return False

        asyncio.create_task(self.receiver.client_proccess_connection(sid, auth))

    async def on_disconnect(self, sid):
        print(f"[disconnect] {sid}")
        await self.receiver.client_proccess_disconnection(sid)
        # TODO 2 min timeout to delete data

    async def on_connections_ask(self, sid, data=None):  # call back function
        return await self.receiver.client_get_connections()

    async def on_subscribe_ask(self, sid, data):
        return await self.receiver.client_subscribe(sid, data)

    # async def on_subscribe_ask(self, sid, data):  # call back function
    #     available = await self.receiver.client_get_connections()
    #     ans = {}
    #     print(f"{sid} want subscribe to {data}")
    #     for room in data:
    #         if room in available:
    #             await self.enter_room(sid, room)
    #             asyncio.create_task(self.receiver.forceload(room))
    #             ans[room] = 'ok'
    #         else:
    #             ans[room] = "no_con"
    #     return ans

    async def on_unsubscribe_ask(self, sid, data):
        return await self.receiver.client_unsubscribe(sid, data)

    # async def on_unsubscribe_ask(self, sid, data):  # call back function
    #     available = await self.receiver.client_get_connections()
    #     ans = {}
    #     for room in data:
    #         if room in available:
    #             await self.leave_room(sid, room)
    #             asyncio.create_task(self.receiver.forceload(room))
    #             ans[room] = 'ok'
    #         else:
    #             ans[room] = "no_con"
    #     return ans

    async def on_command(self, sid, data):
        '''
        data is awaitted to be {to_sid: sid, com : com, key : key}
        '''
        to_sid = data.pop("to_sid")
        await self.receiver.client_proccess_command(to_sid, data, author=sid)

    async def on_client_message(self, sid, data):
        print(f"[client_message] {sid}: {data}")