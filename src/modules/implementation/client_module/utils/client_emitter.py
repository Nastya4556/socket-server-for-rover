# -*- coding: utf-8 -*-
"""
ARTIFICIAL INTELLIGENCE RESEARCH CENTER

Running in ВЬЮГА
@author: STARK

Created in Oct 2025
"""

import asyncio

class Client_Emitter_mixin:

    async def emit_client_token_ask(self, sid, timeout):
        return await self.emit_callback(sid,
                                        "token_ask", {"new_sess_token": sid},
                                        ns=self.client_ns, timeout=5)

    async def emit_client_heartbeat(self, sid, payload, timeout):
        return await self.emit_callback(sid,
                                        "heartbeat", payload,
                                        ns=self.client_ns, timeout=5)

    async def emit_client_overview(self):
        overview = await self.db.client_generate_overview()

        await self.emit_all('overview', overview,
                            ns=self.client_ns)

    async def emit_client_telem(self, sid):
        telem = await self.db.robot_get_telem(sid)

        # await self.emit_client_overview()

        await self.emit_room(sid,
                             'telem', telem,
                             ns=self.client_ns)

    async def emit_client_video(self, sid):
        video = await self.db.robot_get_video(sid)
        await self.emit_room(sid,
                             'video', video,
                             ns=self.client_ns)

    async def emit_client_file(self, sid, data):
        await self.emit_room(sid,
                             'file', data,
                             ns=self.client_ns)



class ClientEmitter(Client_Emitter_mixin):

    def __init__(self, vault, sio, client_ns):
        self.db = vault
        self.sio = sio
        self.client_ns = client_ns

    async def emit_to(self, sid, name, payload, ns, author=None):
        await self.sio.emit(
            name,
            {"payload": payload, "author": author},
            to=sid,
            namespace=ns
        )

    async def emit_room(self, room, name, payload, ns):
        await self.sio.emit(
            name,
            {"payload": payload, "author": room},
            room=room,
            namespace=ns
        )

    async def emit_all(self, name, payload, ns):
        await self.sio.emit(
            name,
            {"payload": payload},
            namespace=ns
        )

    async def emit_callback(self, sid, name, payload, ns, timeout):
        try:
            return await self.sio.call(
                name,
                payload,
                to=sid,
                namespace=ns,
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return "NRp"

    async def disconnect(self, sid):
        await self.sio.disconnect(sid)