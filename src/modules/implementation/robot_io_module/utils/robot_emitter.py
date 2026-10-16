# -*- coding: utf-8 -*-
"""
ARTIFICIAL INTELLIGENCE RESEARCH CENTER

Running in ВЬЮГА
@author: STARK

Created in Oct 2025
"""


class Robot_Emitter_mixin:

    async def emit_robot_token_ask(self, sid, timeout):
        return await self.emit_callback(sid,
                                        "token_ask", {"new_sess_token": sid},
                                        ns=self.robot_ns, timeout=5)

    async def emit_robot_heartbeat(self, sid, payload, timeout):
        return await self.emit_callback(sid,
                                        "heartbeat", payload,
                                        ns=self.robot_ns, timeout=5)

    async def emit_robot_command(self, sid, data, author=None):
        print(f"emit command to - {sid}, payload - {data}")
        await self.emit_to(sid,
                           "command", data,
                           ns=self.robot_ns,
                           author=author)

