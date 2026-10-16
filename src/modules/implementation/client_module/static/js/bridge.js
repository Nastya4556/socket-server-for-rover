let currentIP = null;

const overviewEl = document.getElementById('overview');
const clientViewEl = document.getElementById('client-view');
const clientIpEl = document.getElementById('client-ip');
const totalEl = document.getElementById('total');
const robotsEl = document.getElementById('robots');


function showOverview() {
  if (currentIP) {
    window.client.unsubscribe(currentIP);
  }
  currentIP = null;
  clientViewEl.classList.add('hidden');
  overviewEl.classList.remove('hidden');
  // Снимаем активный класс со всех элементов сайдбара
  Object.values(sidebarItems).forEach(el => el.classList.remove('active'));
}

function showClient(ip, robot_data) {
  clientIpEl.textContent = ip;
  overviewEl.classList.add('hidden');
  clientViewEl.classList.remove('hidden');

  if (currentIP) {
    window.client.unsubscribe(currentIP);
  }
  currentIP = ip;
  window.client.subscribe(currentIP);


  renderTelemetry({});
  renderVideo({});
  updateIP(ip);
  controllerShow(robot_data);
  //document.getElementById('telem-table').innerHTML = '';
  //document.getElementById('video-list').innerHTML = {};
  

}

function on_overview(data){
  // Извлекаем robots и stats из нового формата данных
  const robots = data.robots || {};
  const stats = data.stats || {};
  
  // Преобразуем robots в формат clients для совместимости со старым кодом
  const clients = {};
  Object.entries(robots).forEach(([ip, robotData]) => {
    // Используем name из данных робота, тип по умолчанию - 'robot'
    clients[ip] = [robotData.name || 'Unknown', 'robot'];
  });

  // Подсчет типов динамически
  const typeCounts = {};
  Object.entries(clients).forEach(([ip, [name, type]]) => {
    if (!typeCounts[type]) typeCounts[type] = 0;
    typeCounts[type] += 1;
  });

  const typeCounts2 = {};
  Object.entries(robots).forEach(([ip, robotData]) => {
    const type = robotData.type || 'unknown'; // Берем тип из данных робота
    if (!typeCounts2[type]) typeCounts2[type] = 0;
    typeCounts2[type] += 1;
  });
  
  // Добавляем viewers из stats
  typeCounts.viewers = stats.viewers || 0;

  updateTotalCount(Object.keys(clients).length);

  renderSidebar(clients, currentIP, showClient, robots);
  renderOverviewTable(clients, robots);
  renderTypeCounters(typeCounts, typeCounts2);
}


function sendCommand(command) {
  if (currentIP) {
    console.log(currentIP, command)
    window.client.sendCommand(currentIP, command);
  }
}

function sendFileCommand(command) {
  if (currentIP) {
    console.log(currentIP, command)
    window.client.sendFileCommand(currentIP, command);
  }
}

function sendCommandArgs(command, args) {
  if (currentIP) {
    console.log(currentIP, command, args);
    window.client.sendCommandArgs(currentIP, command, args);
  }
}

function downloadFile(content, filename) {
    const blob = new Blob([content], { type: 'text/plain' });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    // Настраиваем ссылку
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    
    // Добавляем на страницу и кликаем
    document.body.appendChild(a);
    a.click();
    
    // Очищаем
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}