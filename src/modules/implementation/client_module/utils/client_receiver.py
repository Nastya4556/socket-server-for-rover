# -*- coding: utf-8 -*-
"""
ARTIFICIAL INTELLIGENCE RESEARCH CENTER

Running in ВЬЮГА
@author: STARK

Created in Oct 2025
"""

import asyncio


class Client_Receiver_mixin:

    async def client_auth(self, sid, environ, auth):
        return True

    async def client_proccess_connection(self, sid, auth):

        await asyncio.gather(
            self.db.client_registry(sid, auth),
            self.client_proccess_token(sid)
        )

    async def client_proccess_disconnection(self, sid):
        type_ = await self.db.client_get_smeta(sid, "type")

        if type_ not in [None, "web"]:
            await asyncio.sleep(60)

        await self.db.client_delete(sid)
        await self.emitter.emit_client_overview()

    async def client_proccess_token(self, sid):

        old_sess_token = await self.emitter.emit_client_token_ask(sid, timeout=5)

        if old_sess_token == "NRp":
            await self.emitter.disconnect(sid)
            return

        elif old_sess_token is not None:
            print(f"[INFO] reconnect from - {old_sess_token} : to - {sid}(token upgrade)")
            # TODO Reconnecting logic

        await self.client_heartbeat(sid, keys=["Ready"])

    async def client_heartbeat(self, sid, keys=[]):
        print(f"[INFO] send heartbeat to - {sid}, keys - {['d_meta'] + keys}")
        heartbeat_response = await self.emitter.emit_client_heartbeat(sid, ["d_meta"] + keys, timeout=5)
        if heartbeat_response == "NRp":
            await self.emitter.disconnect(sid)
            return
        asyncio.create_task(
            self.db.client_set_dmeta(sid, heartbeat_response.pop("d_meta")))
        asyncio.create_task(
            self.emitter.emit_client_overview())
        return heartbeat_response

    async def client_get_connections(self):
        return await self.db.get_robot_connections()

    async def forceload(self, sid):
        await self.emitter.emit_client_telem(sid)

    # async def client_proccess_command(self, to_sid, data, author=None):
    #     await self.emitter.emit_robot_command(to_sid, data, author=author)

    ###
    async def client_subscribe(self, sid, data):
        return await self.parent.client_subscribe(sid, data)

    async def client_unsubscribe(self, sid, data):
        return await self.parent.client_unsubscribe(sid, data)

    async def client_proccess_command(self, to_sid, data, author=None):
        return await self.parent.client_proccess_command(
            to_sid, data, author
        )