import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from pathlib import Path


class WebManagerInterface:

    def __init__(self, manager):

        self.manager = manager
        self.app = FastAPI()

        folder_path = Path(__file__).parent
        self.static_dir = folder_path / "static"

        self.app.mount(
            "/static",
            StaticFiles(directory=self.static_dir),
            name="static"
        )

        self._setup_routes()
    # ------------------------------------------------

    def _setup_routes(self):

        app = self.app
        manager = self.manager

        # -----------------------------
        # modules
        # -----------------------------

        @app.get("/")
        async def index():
            return FileResponse(
                os.path.join(self.static_dir, "index.html")
            )

        @app.get("/api/modules")
        async def get_modules():
            return manager.get_modules()

        @app.get("/api/modules/available")
        async def get_available_modules():
            return manager.get_available_modules()

        @app.post("/api/modules/create")
        async def create_module(request: Request):

            data = await request.json()

            module_type = data.get("type")
            name = data.get("name")
            config = data.get("config", {})

            if not module_type:
                return JSONResponse(
                    {"error": "type is required"},
                    status_code=400
                )

            if not name:
                return JSONResponse(
                    {"error": "name is required"},
                    status_code=400
                )

            try:

                manager.create_module(
                    module_type=module_type,
                    name=name,
                    **config
                )

                return {"status": "ok"}

            except Exception as e:

                return JSONResponse(
                    {"error": str(e)},
                    status_code=400
                )

        @app.delete("/api/modules/{name}")
        async def delete_module(name: str):

            ok = manager.delete_module(name)

            return {"status": ok}

        # -----------------------------
        # connections
        # -----------------------------

        @app.get("/api/connections")
        async def get_connections():
            return manager.get_connections()

        @app.post("/api/connect")
        async def connect_modules(request: Request):

            data = await request.json()

            sender = data.get("sender")
            receiver = data.get("receiver")
            signature = data.get("signature")

            if not sender or not receiver or not signature:
                return JSONResponse(
                    {"error": "sender, receiver and signature required"},
                    status_code=400
                )

            try:

                ok = manager.connect(sender, receiver, signature)

                return {"status": ok}

            except Exception as e:

                return JSONResponse(
                    {"error": str(e)},
                    status_code=400
                )

        @app.post("/api/disconnect")
        async def disconnect_modules(request: Request):

            data = await request.json()

            sender = data.get("sender")
            receiver = data.get("receiver")
            signature = data.get("signature")

            if not sender or not receiver or not signature:
                return JSONResponse(
                    {"error": "sender, receiver and signature required"},
                    status_code=400
                )

            ok = manager.disconnect(sender, receiver, signature)

            return {"status": ok}

        # -----------------------------
        # graph
        # -----------------------------

        @app.get("/api/graph")
        async def get_graph():
            return manager.get_graph()

        # -----------------------------
        # threads
        # -----------------------------

        @app.post("/api/start/{name}")
        async def start_module(name: str):

            ok = manager.start_module(name)

            return {"status": ok}

        @app.post("/api/start_all")
        async def start_all():

            manager.start_all_threads()

            return {"status": True}