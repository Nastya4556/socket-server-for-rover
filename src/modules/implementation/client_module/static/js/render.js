let sidebarItems = {}; // Храним элементы сайдбара: {ip: element}
let notCheck = true;

function renderSidebar(devices, currentIP, showClient, robotsData) {
  const sidebarEl = document.getElementById('sidebar');
  const currentIPs = new Set(Object.keys(devices));
  const existingIPs = new Set(Object.keys(sidebarItems));

  // Удаляем устройства, которых больше нет
  existingIPs.forEach(ip => {
    if (!currentIPs.has(ip)) {
      sidebarItems[ip].remove();
      delete sidebarItems[ip];
    }
  });

  // Добавляем новые устройства или обновляем существующие
  Object.entries(devices).forEach(([ip, info]) => {

    const robot = robotsData[ip];

    if (!sidebarItems[ip]) {
      // Создаем новый элемент
      const div = document.createElement('div');
      div.className = 'sidebar_item';
      
      const ipSpan = document.createElement('span');
      ipSpan.className = 'sidebar_ip'
      ipSpan.textContent = info[0]; 

      const nameSpan = document.createElement('span');
      nameSpan.textContent = robot.type; 
      nameSpan.className = 'sidebar_name';

      div.appendChild(ipSpan);
      div.appendChild(nameSpan);

      div.onclick = () => {
        // Снимаем активный класс со всех элементов
        Object.values(sidebarItems).forEach(el => el.classList.remove('active'));
        div.classList.add('active');
        showClient(ip, robotsData[ip]);
      };

      sidebarEl.appendChild(div);
      sidebarItems[ip] = div;
    } else {
      // Обновляем имя существующего элемента, если изменилось
      const nameSpan = sidebarItems[ip].querySelector('span:last-child');
      if (nameSpan.textContent !== robot.type) {
        nameSpan.textContent = robot.type;
      }
    }

    // Обновляем активное состояние
    sidebarItems[ip].classList.toggle('active', ip === currentIP);
  });
}

const wordForms = ['подключение', 'подключения', 'подключений'];

function declOfNum(number, words) {
          let number100 = number % 100;
          if (number100 >= 11 && number100 <= 19) {
            return words[2];
          }
          let number10 = number % 10;
          if (number10 === 1) {
            return words[0];
          }
          if (number10 >= 2 && number10 <= 4) {
            return words[1];
          }
          return words[2];
        }

function updateTotalCount(count) {
  const wordForms = ['подключение', 'подключения', 'подключений'];
  totalEl.textContent = `${count} ${declOfNum(count, wordForms)}`;
  if (count == 0){
    robotsEl.textContent = 0;
  }
}

function renderOverviewTable(clients, robotsData) {
  const connRowsEl = document.getElementById('conn-rows');
  connRowsEl.innerHTML = '';

  Object.entries(clients).forEach(([ip, [name, , battery]], idx) => {
    const tr = document.createElement('tr');

    const robot = robotsData[ip];
    let telemetryIcon = '';
    let videoIcon = '';

    if (robot && robot.posibilities) {
      if (robot.posibilities.telemetry === true) {
        telemetryIcon = '<img class="vtk_check vtk_telemetry" src="/static/images/true_check.png" title="Телеметрия">';
      } else if (robot.posibilities.telemetry === false){
        telemetryIcon = '<img class="vtk_check vtk_telemetry" src="/static/images/false_check.png" title="Телеметрия">';
      } else {
        telemetryIcon = '<img class="vtk_check vtk_telemetry" src="/static/images/error_check.png" title="Телеметрия">';
      }
      
      if (robot.posibilities.video === true) {
        videoIcon = '<img class="vtk_check vtk_video" src="/static/images/true_check.png" title="Видео">';
      } else if (robot.posibilities.video === false){
        videoIcon = '<img class="vtk_check vtk_video" src="/static/images/false_check.png" title="Видео">';
      } else {
        videoIcon = '<img class="vtk_check vtk_video" src="/static/images/error_check.png" title="Видео">';
      }
    } else {
      telemetryIcon = '<img class="vtk_check vtk_telemetry" src="/static/images/error_check.png" title="Телеметрия">';
      videoIcon = '<img class="vtk_check vtk_video" src="/static/images/error_check.png" title="Видео">';
    }
    
    const vtkCell = `${telemetryIcon}&nbsp;${videoIcon}`;

    tr.innerHTML = `<td>${idx+1}</td><td class="font-mono">${ip}</td><td>${name}</td><td>${robot.type}</td><td>${vtkCell}</td><td>${battery}</td>`;
    connRowsEl.appendChild(tr);
  });
}

function renderTypeCounters(counts, counts2) {
  const viewersElement = document.getElementById('viewers');
  const computersElement = document.getElementById('computers');
  const robotsElement = document.getElementById('robots');
  const typeCountersEl = document.getElementById('type-counters');
  typeCountersEl.innerHTML = '';
  Object.entries(counts).forEach(([k, v]) => {
    if (k=="viewers") {
      viewersElement.textContent = `${v}`;
    }
    else if (k=="pc_clients") {
      computersElement.textContent = `${v}`;
    }
    else {
      robotsElement.textContent = `${v}`;
    }
  });

  Object.entries(counts2).forEach(([k, v]) => {
      const card = document.createElement('div');
      card.className = 'connections_container_item_block';
      card.innerHTML = `<h3 class="connections_container_item_block_title">${k}</h3><p class="connections_container_item_block_number">${v}</p>`;
      typeCountersEl.appendChild(card);  
  });
}

function formatValue(value) {
    if (typeof value === 'object' && value !== null) {
      return `<pre class="text-xs">${JSON.stringify(value, null, 2)}</pre>`;
    } else if (typeof value === 'boolean') {
      return `<span class="${value ? 'text-green-500' : 'text-red-500'}">${value}</span>`;
    } else if (typeof value === 'number') {
      return `<span class="text-blue-500">${value}</span>`;
    } else {
      return value;
    }
  }


function renderTelemetry(obj) {
  const telemTableEl = document.getElementById('telem-table');
  telemTableEl.innerHTML = '';
  Object.entries(obj).forEach(([k,v]) => {
    const tr = document.createElement('tr');
    let displayValue = v;
    if (typeof v === 'object' && v !== null) {
      v = JSON.stringify(v, null, 2);
    }
    tr.innerHTML = `<td class="text-gray-500">${k}</td><td class="font-mono">${formatValue(v)}</td>`;
    telemTableEl.appendChild(tr);
    renderSelectColor(obj);
    if (notCheck){
      renderBrightnessFirst(obj);
      notCheck = !notCheck;
    }
    
  });
}

function renderSelectColor(obj) {
  Object.entries(obj).forEach(([k,v]) => {
    if (k == "Color"){
      v = JSON.stringify(v, null, 2);
      const rgbArray = v.replace("[", "").replace("]", "").split(',');
      newcolor = `rgb(${rgbArray[0]},${rgbArray[1]},${rgbArray[2]})`;
      currentColorDiv.style.background = newcolor;
    }
  });
}

function renderBrightnessFirst(obj){
  Object.entries(obj).forEach(([k,v]) => {
    if (k == "Brightness"){
      v = JSON.stringify(v, null, 2);
      console.log(v);
      const brightTelem = parseFloat(v)*100;
      brightSlider.value = brightTelem;
    }
  });
}

let videoElements = {}; // Храним созданные элементы: {camId: {wrapper, img}}

function renderVideo(data) {
  const videoListEl = document.getElementById('video-list');
  
  Object.entries(data).forEach(([camId, frameData]) => {
    if (!videoElements[camId]) {
      // Создаем новый элемент если его нет
      const wrapper = document.createElement('div');
      wrapper.className = 'video_container_item';
      wrapper.id = `video-${camId}`;
      
      const header = document.createElement('div');
      header.className = 'video_header';
      header.innerHTML = `
        <span class="video_header_left" >Камера: ${camId}</span>
        <span class="video_header_right" id="time-${camId}">${new Date().toLocaleTimeString()}</span>
      `;
      
      const img = document.createElement('img');
      img.className = 'video_img';
      img.alt = `Video from ${camId}`;
      
      wrapper.appendChild(header);
      wrapper.appendChild(img);
      videoListEl.appendChild(wrapper);
      
      videoElements[camId] = { wrapper, img };
    }
    
    // Обновляем только изображение и время
    const { img } = videoElements[camId];
    
    try {
      const blob = new Blob([frameData], { type: 'image/jpeg' });
      const url = URL.createObjectURL(blob);
      
      img.src = url;
      img.onload = () => URL.revokeObjectURL(url);
      
      // Обновляем время
      document.getElementById(`time-${camId}`).textContent = new Date().toLocaleTimeString();
      
    } catch (error) {
      console.error('Error updating video frame:', error);
    }
  });
  
  // Удаляем старые камеры которых нет в новых данных
  Object.keys(videoElements).forEach(camId => {
    if (!data[camId]) {
      videoElements[camId].wrapper.remove();
      delete videoElements[camId];
    }
  });
}

function updateIP(ip) {
  document.getElementById('currentIP').textContent = ip;
}

function controllerShow(robot_data){
  if (robot_data["type"] == "Robot"){
    document.getElementById('controllerR').classList.remove('hidden');
    document.getElementById('controllerD').classList.add('hidden');
    document.getElementById('controllerL').classList.add('hidden');
    document.getElementById('secondControl').classList.remove('hidden');
  }
  else if(robot_data["type"] == "Drone"){
    document.getElementById('controllerR').classList.add('hidden');
    document.getElementById('controllerD').classList.remove('hidden');
    document.getElementById('controllerL').classList.add('hidden');
    document.getElementById('secondControl').classList.remove('hidden');
  }
  else if(robot_data["type"] == "LED"){
    document.getElementById('controllerR').classList.add('hidden');
    document.getElementById('controllerD').classList.add('hidden');
    document.getElementById('controllerL').classList.remove('hidden');
    document.getElementById('secondControl').classList.add('hidden');
  }
}


//LED

const svg = document.getElementById("palette");
const currentColorDiv = document.getElementById("currentColor");
const hoverColorDiv = document.getElementById("hoverColor");
const brightSlider = document.getElementById("slider");

// ----------------------
// HEX TILE PARAMETERS
// ----------------------
const bigRadius = 180;
const smallR = 12;
const cx = 190;
const cy = 190;

// ----------------------
// ВЕРШИНЫ БОЛЬШОГО ШЕСТИГРАННИКА
// ----------------------
function hexPoint(cx, cy, r, i) {
    const angle = Math.PI/3 * i - Math.PI/6;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
}

let vertices = [];
for (let i=0; i<6; i++) vertices.push(hexPoint(cx, cy, bigRadius, i));

const anchors = {
    R: { x: vertices[0].x, y: vertices[0].y, color: [255, 0, 0] },
    Y: { x: vertices[1].x, y: vertices[1].y, color: [255, 255, 0] },
    G: { x: vertices[2].x, y: vertices[2].y, color: [0, 255, 0] },
    C: { x: vertices[3].x, y: vertices[3].y, color: [0, 255, 255] },
    B: { x: vertices[4].x, y: vertices[4].y, color: [0, 0, 255] },
    M: { x: vertices[5].x, y: vertices[5].y, color: [255, 0, 255] }
};

// ----------------------
// ФУНКЦИЯ СМЕШИВАНИЯ ЦВЕТА
// ----------------------
function mixColor(x, y) {
    const k = 60;
    let weights = [];
    let sum = 0;

    for (const key in anchors) {
        const a = anchors[key];
        const dx = x - a.x;
        const dy = y - a.y;
        const d = Math.sqrt(dx*dx + dy*dy);
        const w = Math.exp(-d/k);
        weights.push({ w, color: a.color });
        sum += w;
    }

    let R=0, G=0, B=0;
    for (const p of weights) {
        const factor = p.w / sum;
        R += p.color[0] * factor;
        G += p.color[1] * factor;
        B += p.color[2] * factor;
    }

    const dCenter = Math.hypot(x - cx, y - cy);
    const boost = Math.max(0, 1 - (dCenter / bigRadius));
    const maxC = Math.max(R, G, B);
    if (maxC > 0) {
        const scale = 1 + (255 / maxC - 1) * boost;
        R *= scale; G *= scale; B *= scale;
        R = Math.min(R, 255); G = Math.min(G, 255); B = Math.min(B, 255);
    }

    R = Math.max(0, R-18);
    G = Math.max(0, G-18);
    B = Math.max(0, B-18);

    let m = Math.max(R, G, B);

    R = Math.floor(R * (255/m));
    G = Math.floor(G * (255/m));
    B = Math.floor(B * (255/m)); 



    return `rgb(${R|0},${G|0},${B|0})`;
}

// ----------------------
// МАЛЕНЬКИЙ ШЕСТИУГОЛЬНИК
// ----------------------
function smallHex(x, y, r) {
    let pts = [];
    for (let i=0; i<6; i++) {
        const angle = Math.PI/3 * i;
        pts.push((x + r*Math.cos(angle)) + "," + (y + r*Math.sin(angle)));
    }
    return pts.join(" ");
}

// ----------------------
// ПРОВЕРКА — ТОЧКА ВНУТРИ БОЛЬШОГО ШЕСТИГРАННИКА
// ----------------------
function insideBigHex(x, y) {
    let intersections = 0;
    for (let i=0; i<6; i++) {
        const j = (i+1)%6;
        const x1 = vertices[i].x, y1 = vertices[i].y;
        const x2 = vertices[j].x, y2 = vertices[j].y;
        if (((y1 > y) !== (y2 > y)) &&
            (x < (x2-x1)*(y-y1)/(y2-y1) + x1))
            intersections++;
    }
    return intersections % 2 === 1;
}

// ----------------------
// ТАЙЛИНГ
// ----------------------
const h = smallR * Math.sqrt(3);

for (let row = -30; row <= 30; row++) {
    for (let col = -30; col <= 30; col++) {
        const x = cx + col * (smallR * 1.5);
        const y = cy + row * h + (col % 2 ? h/2 : 0);
        if (!insideBigHex(x, y)) continue;

        const c = mixColor(x, y);
        const tile = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        tile.setAttribute("points", smallHex(x, y, smallR));
        tile.setAttribute("fill", c);
        tile.setAttribute("stroke", "none");
        svg.appendChild(tile);

        tile.addEventListener("click", () => {
            rgb_str = c;
            result = rgb_str.replace("rgb(", "").replace(")", "").replace(",", ".").replace(",", ".");
            sendCommand({"color": result});
        });
    }
}

function isValidHex(hex) {
    hex = hex.replace(/^#/, '');
    return /^[0-9A-Fa-f]{6}$/.test(hex);
}

// Конвертация HEX в формат 255.255.255
function hexToRgbString(hex) {
    hex = hex.replace(/^#/, '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return `${r}.${g}.${b}`;
}

// Инициализация обработчиков
function initHexInput() {
    const hexInput = document.getElementById('hexInput');
    const sendHexBtn = document.getElementById('sendHexBtn');
    const hexError = document.getElementById('hexError');
    
    // Очистка ошибки
    function clearError() {
        hexError.textContent = '';
        hexError.classList.remove('show');
    }
    
    // Показать ошибку
    function showError(message) {
        hexError.textContent = message;
        hexError.classList.add('show');
    }
    
    // Отправка цвета
    function sendColor() {
        const hexValue = hexInput.value.trim();
        
        if (!isValidHex(hexValue)) {
            showError('Введите 6 символов HEX (0-9, A-F)');
            return;
        }
        
        clearError();
        const rgbString = hexToRgbString(hexValue);
        
        // Вызов вашей функции sendCommand
        sendCommand({"color": rgbString});
        
        // Обновление отображения
    }
    
    // Обработчики событий
    sendHexBtn.addEventListener('click', sendColor);
    
    hexInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendColor();
    });
    
    hexInput.addEventListener('input', function() {
        // Убираем # если есть
        if (this.value.startsWith('#')) {
            this.value = this.value.substring(1);
        }
        
        // Автоматическая валидация
        const val = this.value.toUpperCase();
        this.value = val;
        
        if (val.length === 0) {
            clearError();
        } else if (val.length === 6) {
            if (!isValidHex(val)) {
                showError('Неверный HEX формат');
            } else {
                clearError();
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', initHexInput);

const slider = document.getElementById('slider');
let isDragging = false;

slider.addEventListener('mousedown', function() {
    isDragging = true;
});

slider.addEventListener('mouseup', function() {
    if (isDragging) {
        const brightness = (this.value / 100).toFixed(2);
        sendCommand({brightness});
        isDragging = false;
    }
});

document.addEventListener('mouseup', function() {
    if (isDragging) {
        const brightness = (slider.value / 100).toFixed(2);
        sendCommand({brightness});
        isDragging = false;
    }
});