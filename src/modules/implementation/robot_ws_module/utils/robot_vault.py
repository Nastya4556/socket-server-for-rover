# -*- coding: utf-8 -*-
"""
ARTIFICIAL INTELLIGENCE RESEARCH CENTER

Running in ВЬЮГА
@author: STARK

Created in Oct 2025
"""


class Robot_Vault_mixin:

    def __init__(self):
        """
        robot_data = {sid : {
                                smeta : {
                                    name : str
                                    type : str
                                    }
                                dmeta : {
                                    ready : bool
                                    telem_can : bool
                                    video_can : bool

                                    telem_run : bool
                                    video_run : bool}

                                telem : {key : val}
                                video : {key : val}
                                }
        """
        self.robot_data = {}

    async def robot_registry(self, sid, smeta=None):

        self.robot_data[sid] = {"smeta": {},
                                "dmeta": {},
                                "telem": {},
                                "video": {}, }

        if smeta is not None:
            await self.robot_set_smeta(sid, smeta)

    async def robot_delete(self, sid):
        if sid not in self.robot_data.keys(): return
        self.robot_data.pop(sid)

    async def robot_set_smeta(self, sid, data):
        self.robot_data[sid]["smeta"] = data

    async def robot_set_dmeta(self, sid, data):
        self.robot_data[sid]["dmeta"] = data

    async def robot_set_telem(self, sid, data):
        self.robot_data[sid]["telem"] = data

    async def robot_set_video(self, sid, data):
        self.robot_data[sid]["video"] = data

    async def robot_get_smeta(self, sid):
        return self.robot_data[sid]["smeta"]

    async def robot_get_dmeta(self, sid):
        return self.robot_data[sid]["dmeta"]

    async def robot_get_telem(self, sid):
        return self.robot_data[sid]["telem"]

    async def robot_get_video(self, sid):
        return self.robot_data[sid]["video"]

    async def get_robot_connections(self):
        return self.robot_data.keys()
