# -*- coding: utf-8 -*-
"""
ARTIFICIAL INTELLIGENCE RESEARCH CENTER

Running in ВЬЮГА
@author: STARK

Created in Oct 2025
"""


class Client_Vault_mixin:

    def __init__(self):
        self.robot_connections = set()
        self.robot_telem = {}
        self.robot_video = {}

        self.robot_subscribers = {}

    async def get_robot_connections(self):
        # return set(self.robot_connections)
        return list(self.robot_connections)

    def _ensure_client_data(self):
        if not hasattr(self, "client_data"):
            self.client_data = {}


    async def client_registry(self, sid, smeta={}):
        self._ensure_client_data()

        self.client_data[sid] = {
            "smeta": {},
            "robots": set()
        }

    async def get_robot_subscribers(self, robot_sid):
        return set(self.robot_subscribers.get(robot_sid, []))

    async def client_delete(self, sid):
        self._ensure_client_data()

        info = self.client_data.get(sid)
        if not info:
            return

        # удалить клиента из подписчиков роботов
        for robot_sid in info.get("robots", []):
            subs = self.robot_subscribers.get(robot_sid)
            if subs:
                subs.discard(sid)
                if not subs:
                    del self.robot_subscribers[robot_sid]

        del self.client_data[sid]

    async def client_set_smeta(self, sid, data):
        self.client_data[sid]["smeta"] = data

    async def client_get_smeta(self, sid, key=None):
        if key is None: return self.client_data[sid]["smeta"]
        return self.client_data[sid]["smeta"].get(key, None)

    async def client_set_dmeta(self, sid, data):
        self.client_data[sid]["dmeta"] = data

    async def client_generate_overview(self):
        stats = {
            "robots": len(self.robot_data),
            "pc_clients": 0,
            "viewers": 0
        }

        robots = {}

        # ---- Роботы ----
        for sid, info in self.robot_data.items():
            sm = info.get("smeta") or {}
            dm = info.get("dmeta") or {}

            name = sm.get("name", sid)
            type_ = sm.get("type", sid)
            state = dm.get("ready", "init")

            robots[sid] = {
                "name": name,
                "type": type_,
                "state": state,
                "posibilities": {
                    "telemetry": sm.get("telem_can", "NotProvided"),
                    "video": sm.get("video_can", "NotProvided")
                },
                "streams": {
                    "telemetry": dm.get("telem_run", "NotProvided"),
                    "video": dm.get("video_run", "NotProvided")
                }
            }
            stats["robots"] += 1

        # ---- Клиенты ----
        for sid, info in self.client_data.items():
            sm = info.get("smeta") or {}
            type_ = sm.get("type", "unknown")

            if type_ == "pc":
                stats["pc_clients"] += 1
            elif type_ == "web":
                stats["viewers"] += 1
            # если позже будут mobile / api — тоже учтём

        return {
            "stats": stats,
            "robots": robots
        }

    async def read_telem(self, sid):
        ...

    async def read_video(self, sid):
        ...

    async def robot_get_telem(self, sid):
        return self.robot_data.get(sid, {}).get("telem")

    async def robot_get_video(self, sid):
        return self.robot_data.get(sid, {}).get("video")


    async def subscribe_client_to_robot(self, client_sid, robot_sid):
        # client -> robot
        self.client_data[client_sid]["robots"].add(robot_sid)

        # robot -> clients
        self.robot_subscribers.setdefault(robot_sid, set()).add(client_sid)


    async def unsubscribe_client_from_robot(self, client_sid, robot_sid):
        self.client_data[client_sid]["robots"].discard(robot_sid)

        subs = self.robot_subscribers.get(robot_sid)
        if subs:
            subs.discard(client_sid)
            if not subs:
                del self.robot_subscribers[robot_sid]