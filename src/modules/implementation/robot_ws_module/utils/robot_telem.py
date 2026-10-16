# -*- coding: utf-8 -*-
"""
ARTIFICIAL INTELLIGENCE RESEARCH CENTER

Running in ВЬЮГА
@author: STARK

Created in Oct 2025
"""

import asyncio
from socketio import AsyncNamespace as AN


class RobotTelemetryNS(AN):

    def __init__(self, namespace, receiver):
        super().__init__(namespace)
        self.receiver = receiver

    async def on_connect(self, sid, environ, auth):
        print(f"[connect] {sid} (auth={auth})")
        if not await self.receiver.robot_auth(sid, environ, auth):
            return False

        asyncio.create_task(self.receiver.robot_proccess_connection(sid, auth))

    async def on_disconnect(self, sid):
        print(f"[disconnect] {sid}")
        await self.receiver.robot_proccess_disconnection(sid)
        # TODO 2 min timeout to delete data

    async def on_telem(self, sid, data):
        await self.receiver.robot_pass_telem(sid, data["payload"])

    async def on_video(self, sid, data):
        await self.receiver.robot_pass_video(sid, data["payload"])

    async def on_file(self, sid, data):
        await self.receiver.robot_pass_file(sid, data["payload"])

    async def on_client_message(self, sid, data): ...

