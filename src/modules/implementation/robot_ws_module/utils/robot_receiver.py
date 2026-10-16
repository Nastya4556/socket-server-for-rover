# -*- coding: utf-8 -*-
"""
ARTIFICIAL INTELLIGENCE RESEARCH CENTER

Running in ВЬЮГА
@author: STARK

Created in Oct 2025
"""


import asyncio
from fastapi import WebSocket

class Robot_Receiver_mixin:

    async def robot_auth(self, websocket: WebSocket, environ, auth) -> bool:
        return True

    async def robot_proccess_connection(self, websocket: WebSocket, auth):
        sid = websocket.scope["sid"]

        await asyncio.gather(
            self.db.robot_registry(sid, auth),
            self.robot_proccess_token(websocket)
        )

    async def robot_proccess_disconnection(self, websocket: WebSocket):
        sid = websocket.scope["sid"]
        await self.db.robot_delete(sid)
        await self.emitter.emit_client_overview()

    async def robot_proccess_token(self, websocket: WebSocket):
        sid = websocket.scope["sid"]

        old_sess_token = await self.emitter.emit_robot_token_ask(sid, timeout=5)

        if old_sess_token == "NRp":
            await self.emitter.disconnect(sid)
            return

        if old_sess_token is not None:
            print(f"[INFO] reconnect from - {old_sess_token} : to - {sid}(token upgrade)")

        await self.robot_heartbeat(websocket, keys=["Ready"])

    async def robot_heartbeat(self, websocket: WebSocket, keys=[]):
        sid = websocket.scope["sid"]
        heartbeat_response = await self.emitter.emit_robot_heartbeat(sid, ["d_meta"] + keys, timeout=5)
        if heartbeat_response == "NRp":
            await self.emitter.disconnect(sid)
            return

        asyncio.create_task(
            self.db.robot_set_dmeta(sid, heartbeat_response.pop("d_meta"))
        )

        asyncio.create_task(
            self.emitter.emit_client_overview()
        )

        return heartbeat_response

    async def robot_pass_telem(self, websocket: WebSocket, data):
        sid = websocket.scope["sid"]
        await self.db.robot_set_telem(sid, data)
        await asyncio.gather(
            self.emitter.emit_client_telem(sid)
        )

    async def robot_pass_video(self, websocket: WebSocket, data):
        sid = websocket.scope["sid"]
        await self.db.robot_set_video(sid, data)
        await asyncio.gather(
            self.emitter.emit_client_video(sid)
        )

    async def robot_pass_file(self, websocket: WebSocket, data):
        sid = websocket.scope["sid"]
        await asyncio.gather(
            self.emitter.emit_client_file(sid, data)
        )