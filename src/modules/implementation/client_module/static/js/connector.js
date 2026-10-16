
class ClientConnector {

    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.ns = "/client";

        this.sio = io(this.serverUrl + this.ns, {
            transports: ["websocket"],
            auth: (cb) => this.getAuth(cb)
        });

        this.setupHandlers();

        this.dmeta = {
            sid: null,
            ready: false
        };
    }

    getAuth(cb) {
        cb({
            name: "TODO browser",
            type: "web"
        });
    }

    getStaticAuth() {
        // сюда можно потом впилить токен пользователя
        return {
            name: "TODO browser",
            type: "web"
        };
    }

    setupHandlers() {

        this.sio.on("connect", () => {
            console.log("✅ Client connected:", this.sio.id);
            this.dmeta.sid = this.sio.id;
        });

        this.sio.on("disconnect", () => {
            console.log("⚠️ Client disconnected");
        });

        // === SERVER → CLIENT EVENTS ===

        this.sio.on("overview", (data) => {
            data = data.payload;
            //console.log("📡 OVERVIEW:", data);

            if (currentIP && data.robots) {
                const clientExistsInList = currentIP in data.robots;
                if (!clientExistsInList) {
                    showOverview();
                }
            }

            on_overview(data);
        });

        this.sio.on("telem", (data) => {
            //console.log("📍 TELEMETRY:", data);
            renderTelemetry(data["payload"]);
        });

        this.sio.on("video", (data) => {
            //console.log("🎥 VIDEO FRAME:");
            renderVideo(data["payload"]);
        });

        // === CALLBACK HANDLERS ===

        this.sio.on("token_ask", (data, cb) => {
            //console.log("🔏 token_ask:", data);
            this.dmeta.ready = "ok";
            cb(this.dmeta.sid);
        });

        this.sio.on("heartbeat", (data, cb) => {
            //console.log("❤️ heartbeat request:", data);

            const ans = {};

            for (let key of data) {
                if (key === "d_meta")
                    ans[key] = this.dmeta;

                else if (key === "Ready") {
                    console.log("✅ Client marked ready");
                    ans[key] = "ok";
                } else {
                    console.warn("Unknown HB key:", key);
                }
            }
            //console.log("❤️ heartbeat ans:", ans);
            cb(ans);
        });

        this.sio.on("connect_error", (err) => {
            console.error("❌ Connect error:", err.message);
        });

        this.sio.on('file', (data) => {
            data = data["payload"];
            const type = data["type"];
            const payload = data["content"];
            downloadFile(payload, type+'.txt');

        });
    }

    // CLIENT → SERVER commands

    requestConnections() {
        this.sio.emit("connections_ask", null, (res) => {
            console.log("🌐 Available robots:", res);
        });
    }

    subscribe(robotId) {
        this.sio.emit("subscribe_ask", [robotId], (resp) => {
            //console.log(resp)
        });
        sendCommand("pass")
    }
    unsubscribe(robotId) {
        this.sio.emit("unsubscribe_ask", [robotId], (resp) => {
            //console.log(resp)
        });
    }

    sendCommand(sid, command){
        this.sio.emit("command", {"to_sid":sid, 
                                  "com" : command});
    }

    sendCommandArgs(sid, command, args){
        this.sio.emit("command", {"to_sid":sid, 
                                  "com" : command,
                                  "args" : args});
    }

    sendFileCommand(sid, command){
        this.sio.emit("command", {"to_sid":sid, 
                                  "file" : command});
    }
}

// ===== запускаем =====
window.client = new ClientConnector(location.origin);

