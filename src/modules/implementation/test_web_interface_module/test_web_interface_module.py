from src.modules.base.base_module.base_module import BaseModule
from flask import Flask, render_template_string
from flask_socketio import SocketIO
import threading


class WebInterfaceModule(BaseModule):
    """
    При получении сигнатуры "raw_car_data" обновляет internal positions
    и отправляет через websocket только обновлённую позицию.
    Также служит HTTP-хостом для простой страницы с canvas.
    """
    INDEX_HTML = """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>Cars map</title>
        <style>
          html,body { height:100%; margin:0; }
          #map { width:100%; height:100%; background:#111; display:block; }
          .label { font: 12px monospace; fill: #fff; }
        </style>
      </head>
      <body>
        <canvas id="map"></canvas>
        <script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
        <script>
          const socket = io();
          const canvas = document.getElementById('map');
          const ctx = canvas.getContext('2d');
          function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            draw(); 
          }
          window.addEventListener('resize', resize);
          const cars = {}; // name -> {x,y}
          function draw() {
            ctx.clearRect(0,0,canvas.width,canvas.height);
            // простая система координат: центр центр, масштаб 20 px per unit
            const scale = 2;
            const cx = canvas.width/2;
            const cy = canvas.height/2;
            // оси
            ctx.strokeStyle = '#333';
            ctx.beginPath();
            ctx.moveTo(0, cy); ctx.lineTo(canvas.width, cy);
            ctx.moveTo(cx, 0); ctx.lineTo(cx, canvas.height);
            ctx.stroke();
            // машины
            for (const name in cars) {
              const p = cars[name];
              const sx = cx + p.x * scale;
              const sy = cy - p.y * scale;
              // circle
              ctx.fillStyle = '#2fd';
              ctx.beginPath();
              ctx.arc(sx, sy, 8, 0, Math.PI*2);
              ctx.fill();
              // label
              ctx.font = '12px monospace';
              ctx.fillStyle = '#fff';
              ctx.fillText(name + ` (${p.x},${p.y})`, sx + 10, sy + 4);
            }
          }
          function updateCar(data) {
            // data: {name: "...", position: {x:..., y:...}}
            cars[data.name] = { x: data.position.x, y: data.position.y };
            draw();
          }
          socket.on('connect', () => { console.log('connected'); });
          socket.on('position_update', (data) => { updateCar(data); });
          // initial canvas sizing
          resize();
        </script>
      </body>
    </html>
    """

    def __init__(self, *args, host='0.0.0.0', port=5000, socket_path='/', **kwargs):
        super().__init__(*args, **kwargs)
        self._positions = {}           # name -> position dict
        self._lock = threading.Lock()
        self.host = host
        self.port = port

        # Flask + SocketIO (async_mode 'threading' — не требует eventlet/gevent)
        self.flask_app = Flask(self.name)
        self.socketio = SocketIO(self.flask_app, async_mode='threading', cors_allowed_origins="*")

        # HTTP route: главная страница с canvas
        @self.flask_app.route('/')
        def index():
            return render_template_string(self.INDEX_HTML)

        # подключение клиента — можно обработать при необходимости
        @self.socketio.on('connect')
        def _on_connect():
            # при подключении можно отправить текущие позиции
            with self._lock:
                for name, pos in self._positions.items():
                    self.socketio.emit('position_update', {'name': name, 'position': pos})

        # Запуск SocketIO в отдельном потоке, чтобы не блокировать основной механизм модулей
        t = threading.Thread(target=self._run_socketio, daemon=True)
        t.start()

    def _run_socketio(self):
        # use_reloader=False чтобы не создавать двойной процесса при автоперезагрузке
        self.socketio.run(
            self.flask_app,
            host=self.host,
            port=self.port,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )

    # override process_message: ожидается signature == "raw_car_data"
    def process_message(self, signature, message):
        if signature != "raw_car_data":
            return
        # message должен содержать 'name' и 'position' с x,y
        try:
            name = message['name']
            pos = message['position']
        except Exception:
            return
        with self._lock:
            self._positions[name] = {'x': pos.get('x', 0), 'y': pos.get('y', 0)}
        # отправляем только обновлённую позицию клиентам
        try:
            self.socketio.emit('position_update', {'name': name, 'position': self._positions[name]})
        except Exception:
            # если SocketIO ещё не поднят — просто пропустить
            pass

    # main_loop оставляем пустым — вся работа идёт через receive_message/process_message
    def main_loop(self):
        pass
