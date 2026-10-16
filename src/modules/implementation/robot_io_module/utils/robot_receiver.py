# -*- coding: utf-8 -*-
"""
ARTIFICIAL INTELLIGENCE RESEARCH CENTER

Running in ВЬЮГА
@author: STARK

Created in Oct 2025
"""

import asyncio


class Robot_Receiver_mixin:

    async def robot_auth(self, sid, environ, auth):
        return True

    async def robot_proccess_connection(self, sid, auth):

        await asyncio.gather(
            self.db.robot_registry(sid, auth),
            self.robot_proccess_token(sid)
        )

    async def robot_proccess_disconnection(self, sid):
        # await asyncio.sleep(60)
        await self.db.robot_delete(sid)
        await self.emitter.emit_client_overview()

    async def robot_proccess_token(self, sid):

        old_sess_token = await self.emitter.emit_robot_token_ask(sid, timeout=5)

        if old_sess_token == "NRp":
            await self.emitter.disconnect(sid)
            return

        elif old_sess_token is not None:
            print(f"[INFO] reconnect from - {old_sess_token} : to - {sid}(token upgrade)")
            # TODO Reconnecting logic

        await self.robot_heartbeat(sid, keys=["Ready"])

    async def robot_heartbeat(self, sid, keys=[]):
        heartbeat_response = await self.emitter.emit_robot_heartbeat(sid, ["d_meta"] + keys, timeout=5)
        if heartbeat_response == "NRp":
            await self.emitter.disconnect(sid)
            return

        asyncio.create_task(
            self.db.robot_set_dmeta(sid, heartbeat_response.pop("d_meta")))

        asyncio.create_task(
            self.emitter.emit_client_overview())

        return heartbeat_response

    async def robot_pass_telem(self, sid, data):
        await self.db.robot_set_telem(sid, data)
        await asyncio.gather(
            self.emitter.emit_client_telem(sid)
        )

    async def robot_pass_video(self, sid, data):
        await self.db.robot_set_video(sid, data)
        await asyncio.gather(
            self.emitter.emit_client_video(sid)
        )

    async def robot_pass_file(self, sid, data):
        await asyncio.gather(
            self.emitter.emit_client_file(sid, data)
        )
