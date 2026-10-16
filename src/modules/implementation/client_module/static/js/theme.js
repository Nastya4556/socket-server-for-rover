class Toast {
    constructor(message, type = 'success', title = '') {
        this.message = message;
        this.type = type;
        this.title = title || this.getDefaultTitle();
        this.element = null;
        this.timeout = null;
        this.init();
    }

    getDefaultTitle() {
        return this.type === 'success' ? 'Успех' : 'Ошибка';
    }

    init() {
        this.createElement();
        this.show();
    }

    createElement() {
        this.element = document.createElement('div');
        this.element.className = `toast toast-${this.type}`;
        this.element.setAttribute('role', 'alert');
        this.element.setAttribute('aria-live', 'assertive');
        this.element.setAttribute('aria-atomic', 'true');

        this.element.innerHTML = `
            <div class="toast-content">
                <div class="toast-title">${this.title}</div>
                <div class="toast-message">${this.message}</div>
            </div>
            <button class="toast-close" aria-label="Закрыть уведомление">×</button>
        `;

        const closeButton = this.element.querySelector('.toast-close');
        closeButton.addEventListener('click', () => this.hide());
    }

    show() {
        const container = document.getElementById('toastContainer');
        container.appendChild(this.element);

        requestAnimationFrame(() => {
            this.element.classList.add('show');
        });

        this.timeout = setTimeout(() => {
            this.hide();
        }, 3000);
    }

    hide() {
        if (this.timeout) {
            clearTimeout(this.timeout);
        }

        this.element.classList.remove('show');
        this.element.classList.add('hide');

        setTimeout(() => {
            if (this.element.parentNode) {
                this.element.parentNode.removeChild(this.element);
            }
        }, 300);

    }
}

window.ToastManager = {
    success: (message, title) => new Toast(message, 'success', title),
    error: (message, title) => new Toast(message, 'error', title)
};

let isLightMode = false;
let rotationAngle = 0;

// Функция для применения темы
function applyTheme(theme) {
    const root = document.documentElement;
    const connectionsBar = document.querySelector('.connections_bar');
    const connectionsBarTitle = document.querySelector('.connections_bar_title');
    const connectionsBarSpan = document.querySelector('.connections_bar_span');
    const headContainer = document.querySelector('.head_container');
    const infoImg1 = document.querySelector('.info_img_1');
    const infoImg2 = document.querySelector('.info_img_2');
    const infoImg3 = document.querySelector('.info_img_3');
    const styleChange = document.querySelector('.style_change_img');
    const logo = document.querySelector('.logo');
    const logoAdd = document.querySelector('.logo_add');
    const infoText = document.querySelectorAll('.info_text');
    const sidebarIp = document.querySelectorAll('.sidebar_ip');
    const sidebarName = document.querySelectorAll('.sidebar_name');
    const containerCard = document.querySelectorAll('.connections_container_card');
    const containerCard2 = document.querySelectorAll('.connections_container_card_2');
    const containerTitle = document.querySelectorAll('.connections_container_title');
    const containerTitle2 = document.querySelectorAll('.connections_container_title_2');
    const arrow2 = document.querySelectorAll('.arrow_2');
    const arrow3 = document.querySelectorAll('.arrow_3');
    const arrow4 = document.querySelectorAll('.arrow_4');
    const arrow6 = document.querySelectorAll('.arrow_6');
    const arrow7 = document.querySelectorAll('.arrow_7');
    const arrow8 = document.querySelectorAll('.arrow_8');
    const droneUp = document.querySelector('.drone_arrow_up');
    const droneDown = document.querySelector('.drone_arrow_down');
    const inputArea = document.querySelector('.command_input_area');
    const sendButton = document.querySelector('.send-button');
    const send = document.querySelector('.command_input_area_but');
    const dropZoneOverlay = document.getElementById('dropZoneOverlay');
    const drag = document.querySelector('.drag_icon_img');
    const inter = document.querySelectorAll('.interaction_img');
    const inter_u = document.querySelector('.interaction_img_u');

    // Применяем переходы только если это не первая загрузка страницы
    if (!theme.firstLoad) {
        document.body.style.transition = 'background-color 0.9s linear';
        connectionsBar.style.transition = 'border-right 0.9s linear, background-color 0.9s linear';
        connectionsBarTitle.style.transition = 'color 0.9s linear';
        connectionsBarSpan.style.transition = 'color 0.9s linear, border-top 0.9s linear';
        headContainer.style.transition = 'background-color 0.9s linear';
        infoImg1.style.transition = 'opacity 0.9s ease';
        infoImg2.style.transition = 'opacity 0.9s ease';
        infoImg3.style.transition = 'opacity 0.9s ease';
        inputArea.style.transition = 'color 0.9s linear, background-color 0.9s linear, border 0.9s linear';
        sendButton.style.transition = 'background-color 0.9s linear, border 0.9s linear';
        styleChange.style.transition = 'transform 0.9s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
        logo.style.transition = 'color 0.9s linear';
        logoAdd.style.transition = 'color 0.9s linear';
        drag.style.transition = 'opacity 0.9s ease';
        inter_u.style.transition = 'opacity 0.9s ease';
        inter.forEach(text => {
            text.style.transition = 'opacity 0.9s ease';
        });
        infoText.forEach(text => {
            text.style.transition = 'color 0.9s linear';
        });
        sidebarIp.forEach(text => {
            text.style.transition = 'color 0.9s linear';
        });
        sidebarName.forEach(text => {
            text.style.transition = 'color 0.9s linear';
        });
        containerCard.forEach(text => {
            text.style.transition = 'border 0.9s linear';
        });
        containerTitle.forEach(text => {
            text.style.transition = 'color 0.4s linear';
        });
        containerCard2.forEach(text => {
            text.style.transition = 'border 0.9s linear';
        });
        containerTitle2.forEach(text => {
            text.style.transition = 'color 0.4s linear';
        });
        arrow2.forEach(img => {
            img.style.transition = 'opacity 0.9s ease';
        });
        arrow3.forEach(img => {
            img.style.transition = 'opacity 0.9s ease';
        });
        arrow4.forEach(img => {
            img.style.transition = 'opacity 0.9s ease';
        });
        arrow6.forEach(img => {
            img.style.transition = 'opacity 0.9s ease';
        });
        arrow7.forEach(img => {
            img.style.transition = 'opacity 0.9s ease';
        });
        arrow8.forEach(img => {
            img.style.transition = 'opacity 0.9s ease';
        });
        droneUp.style.transition = 'opacity 0.9s ease';
        droneDown.style.transition = 'opacity 0.9s ease';
        send.style.transition = 'opacity 0.9s ease';
    }

    // Вращение иконки только при ручном переключении
    if (!theme.firstLoad) {
        rotationAngle += 360;
        styleChange.style.transform = `rotate(${rotationAngle}deg)`;
    }

    if (theme.isLight) {
        // Светлая тема
        root.style.setProperty('--sidebar-hover-color', '#45658dff');
        document.body.style.backgroundColor = '#F9FAFB';
        connectionsBar.style.backgroundColor = '#354E6C';
        connectionsBar.style.borderRight = '3px solid #C7E0FE';
        connectionsBarTitle.style.color = '#C7E0FE';
        connectionsBarSpan.style.color = '#C7E0FE';
        connectionsBarSpan.style.borderTop = '3px solid #C7E0FE';
        headContainer.style.backgroundColor = '#354E6C';
        infoImg1.src = '/static/images/viewers_l.png';
        infoImg2.src = '/static/images/computers_l.png';
        infoImg3.src = '/static/images/robots_l.png';
        styleChange.src = '/static/images/style_l.png';
        droneUp.src = '/static/images/drone_up_l.png';
        droneDown.src = '/static/images/drone_down_l.png';
        logo.style.color = '#C7E0FE';
        logoAdd.style.color = '#C7E0FE';
        arrow2.forEach(text => {
            text.src = '/static/images/arrow_l.png';
        });
        arrow3.forEach(text => {
            text.src = '/static/images/arrow_turn_l.png';
        });
        arrow4.forEach(text => {
            text.src = '/static/images/arrow_l.png';
        });
        arrow6.forEach(text => {
            text.src = '/static/images/arrow_l.png';
        });
        arrow7.forEach(text => {
            text.src = '/static/images/arrow_turn_l.png';
        });
        arrow8.forEach(text => {
            text.src = '/static/images/arrow_l.png';
        });
        infoText.forEach(text => {
            text.style.color = '#C7E0FE';
        });
        containerCard.forEach(text => {
            text.style.border = '3px solid #354E6C';
        });
        containerTitle.forEach(text => {
            text.style.color = '#354E6C';
        });
        containerCard2.forEach(text => {
            text.style.border = '3px solid #354E6C';
        });
        containerTitle2.forEach(text => {
            text.style.color = '#354E6C';
        });
        root.style.setProperty('--connections-bg', 'url(/static/images/connections_bg_l.png)');
        root.style.setProperty('--table-text-color', '#354E6C');
        root.style.setProperty('--table-border-color', '3px solid #354E6C');
        root.style.setProperty('--table-border-color-2', '1px solid #354E6C');
        root.style.setProperty('--grid-item-color', '#C7E0FE');
        root.style.setProperty('--grid-item-color-hover', '#9ac5faff');
        root.style.setProperty('--but1-bg-color', '#354E6C');
        root.style.setProperty('--but1-color', '#C7E0FE');
        root.style.setProperty('--stop-bg-color', '#354E6C');
        root.style.setProperty('--stop-color', '#C7E0FE');
        root.style.setProperty('--stop-border', '2px solid #354E6C');
        root.style.setProperty('--stop-bg-color-hover', '#C7E0FE');
        root.style.setProperty('--stop-color-hover', '#354E6C');
        root.style.setProperty('--input-bg-color', '#C7E0FE');
        root.style.setProperty('--input-color', '#354E6C');
        root.style.setProperty('--input-border', '2px solid #354E6C');
        root.style.setProperty('--input-placeholder', '#354E6C');
        sendButton.style.backgroundColor = '#C7E0FE';
        sendButton.style.border = '2px solid #354E6C';
        root.style.setProperty('--but1-bg-color-hover', '#C7E0FE');
        root.style.setProperty('--but1-color-hover', '#354E6C');
        send.src = '/static/images/send_l.png';
        root.style.setProperty('--item-color', '#C7E0FE');
        root.style.setProperty('--number-color', '#C7E0FE');
        root.style.setProperty('--video-bg', '#354E6C');
        root.style.setProperty('--video-left', '#C7E0FE');
        root.style.setProperty('--video-right', '#C7E0FE');
        root.style.setProperty('--sidebar-ip-color', '#C7E0FE');
        root.style.setProperty('--sidebar-name-color', '#C7E0FE');
        root.style.setProperty('--drag-content-bg', '#354E6C');
        root.style.setProperty('--drag-content-border', '3px solid #C7E0FE');
        root.style.setProperty('--drag-text', '#C7E0FE');
        drag.src = '/static/images/download_l.png';
        inter_u.src = '/static/images/interaction_l_u.png';
        inter.forEach(text => {
            text.src = '/static/images/interaction_l_d.png';
        });
        if (dropZoneOverlay) {
            dropZoneOverlay.style.transition = 'opacity 0.3s ease, background 0.9s linear';
        }
        document.body.classList.add('light-theme');
    } else {
        // Темная тема
        root.style.setProperty('--sidebar-hover-color', '#53468bff');
        document.body.style.backgroundColor = '#272E43';
        connectionsBar.style.backgroundColor = '#413770';
        connectionsBar.style.borderRight = '3px solid #8D77B0';
        connectionsBarTitle.style.color = '#CBD5E0';
        connectionsBarSpan.style.color = '#CBD5E0';
        connectionsBarSpan.style.borderTop = '3px solid #8D77B0';
        headContainer.style.backgroundColor = '#413770';
        infoImg1.src = '/static/images/viewers_b.png';
        infoImg2.src = '/static/images/computers_b.png';
        infoImg3.src = '/static/images/robots_b.png';
        styleChange.src = '/static/images/style_b.png';
        droneUp.src = '/static/images/drone_up_b.png';
        droneDown.src = '/static/images/drone_down_b.png';
        logo.style.color = '#CBD5E0';
        logoAdd.style.color = '#8D77B0';
        arrow2.forEach(text => {
            text.src = '/static/images/arrow_b.png';
        });
        arrow3.forEach(text => {
            text.src = '/static/images/arrow_turn_b.png';
        });
        arrow4.forEach(text => {
            text.src = '/static/images/arrow_b.png';
        });
        arrow6.forEach(text => {
            text.src = '/static/images/arrow_b.png';
        });
        arrow7.forEach(text => {
            text.src = '/static/images/arrow_turn_b.png';
        });
        arrow8.forEach(text => {
            text.src = '/static/images/arrow_b.png';
        });
        infoText.forEach(text => {
            text.style.color = '#8D77B0';
        });
        containerCard.forEach(text => {
            text.style.border = '3px solid #413770';
        });
        containerTitle.forEach(text => {
            text.style.color = '#CBD5E0';
        });
        containerCard2.forEach(text => {
            text.style.border = '3px solid #413770';
        });
        containerTitle2.forEach(text => {
            text.style.color = '#CBD5E0';
        });
        root.style.setProperty('--connections-bg', 'url(/static/images/connections_bg_b.png)');
        root.style.setProperty('--table-text-color', '#CBD5E0');
        root.style.setProperty('--table-border-color', '3px solid #413770');
        root.style.setProperty('--table-border-color-2', '1px solid #413770');
        root.style.setProperty('--grid-item-color', '#8D77B0');
        root.style.setProperty('--grid-item-color-hover', '#CBD5E0');
        root.style.setProperty('--but1-bg-color', '#413770');
        root.style.setProperty('--but1-color', '#CBD5E0');
        root.style.setProperty('--stop-bg-color', '#8D77B0');
        root.style.setProperty('--stop-color', '#CBD5E0');
        root.style.setProperty('--stop-border', '2px solid #413770');
        root.style.setProperty('--stop-bg-color-hover', '#CBD5E0');
        root.style.setProperty('--stop-color-hover', '#8D77B0');
        root.style.setProperty('--input-bg-color', '#8D77B0');
        root.style.setProperty('--input-color', '#413770');
        root.style.setProperty('--input-border', '2px solid #413770');
        root.style.setProperty('--input-placeholder', '#CBD5E0');
        sendButton.style.backgroundColor = '#8D77B0';
        sendButton.style.border = '2px solid #413770';
        root.style.setProperty('--but1-bg-color-hover', '#CBD5E0');
        root.style.setProperty('--but1-color-hover', '#413770');
        send.src = '/static/images/send_b.png';
        root.style.setProperty('--item-color', '#8D77B0');
        root.style.setProperty('--number-color', '#CBD5E0');
        root.style.setProperty('--video-bg', '#413770');
        root.style.setProperty('--video-left', '#8D77B0');
        root.style.setProperty('--video-right', '#8D77B0');
        root.style.setProperty('--sidebar-ip-color', '#CBD5E0');
        root.style.setProperty('--sidebar-name-color', '#8D77B0');
        root.style.setProperty('--drag-content-bg', '#413770');
        root.style.setProperty('--drag-content-border', '3px solid #8D77B0');
        root.style.setProperty('--drag-text', '#CBD5E0');
        drag.src = '/static/images/download_b.png';
        inter_u.src = '/static/images/interaction_b_u.png';
        if (dropZoneOverlay) {
            dropZoneOverlay.style.transition = 'opacity 0.3s ease, background 0.9s linear';
        }
        inter.forEach(text => {
            text.src = '/static/images/interaction_b_d.png';
        });
        document.body.classList.remove('light-theme');
    }
    
    // Обновляем глобальную переменную
    isLightMode = theme.isLight;
    
    // Сохраняем в localStorage только при ручном переключении
    if (!theme.firstLoad) {
        localStorage.setItem('theme', isLightMode ? 'light' : 'dark');
    }
}

// Функция для переключения темы
function changeTheme() {
    applyTheme({ isLight: !isLightMode, firstLoad: false });
}

// Функция для загрузки сохраненной темы
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme === 'light') {
        applyTheme({ isLight: true, firstLoad: true });
    } else {
        // Если тема не сохранена или 'dark', применяем темную тему
        applyTheme({ isLight: false, firstLoad: true });
    }
}

function initDragDrop() {
    const dragContainer = document.querySelector('.drag_container');
    const currentIPElement = document.getElementById('currentIP');
    
    // Обработчик начала перетаскивания над документом
    document.addEventListener('dragover', function(e) {
        e.preventDefault();
        
        // Проверяем, что currentIP не null и не пустой
        if (currentIP && currentIP !== '') {
            dragContainer.classList.remove('hidden');
        }
    });
    
    // Обработчик ухода перетаскивания из документа
    document.addEventListener('dragleave', function(e) {
        // Проверяем, что курсор вышел за пределы документа
        if (e.clientX <= 0 || e.clientY <= 0 || 
            e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) {
            dragContainer.classList.add('hidden');
        }
    });
    
    // Обработчик отмены перетаскивания
    document.addEventListener('drop', function(e) {
        e.preventDefault();
        dragContainer.classList.add('hidden');
        
        // Обработка загруженных файлов
        if (e.dataTransfer.files.length > 0 && currentIP) {
            const file = e.dataTransfer.files[0];
            
            // Проверяем что файл имеет расширение .py
            if (!file.name.toLowerCase().endsWith('.py')) {
                new Toast(`Неправильный формат файла. Необходим .py`, 'error', 'Файл не загружен');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const fileContent = e.target.result;
                // Отправляем команду с содержимым файла
                sendCommandArgs('uploadFile', fileContent);
                new Toast(`Загрузка произведена успешно`, 'success', 'Файл загружен');
                console.log('Файл загружен:', file.name);
            };
            reader.onerror = function() {
                alert('Ошибка чтения файла');
            };
            reader.readAsText(file);
        }
    });
    
    // Предотвращаем стандартное поведение браузера
    document.addEventListener('drop', function(e) {
        e.preventDefault();
    });
}

function initFileInput() {
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file && currentIP) {
                // Проверяем что файл имеет расширение .py
                if (!file.name.toLowerCase().endsWith('.py')) {
                    new Toast(`Неправильный формат файла. Необходим .py`, 'error', 'Файл не загружен');
                    event.target.value = ''; // Сбрасываем input
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    const fileContent = e.target.result;
                    sendCommandArgs('uploadFile', fileContent);
                    new Toast(`Загрузка произведена успешно`, 'success', 'Файл загружен');
                    console.log('Файл загружен через input:', file.name);
                };
                reader.onerror = function() {
                    alert('Ошибка чтения файла');
                };
                reader.readAsText(file);
            }
            // Сбрасываем input
            event.target.value = '';
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Сначала загружаем сохраненную тему
    loadSavedTheme();
    initDragDrop();
    initFileInput();
    
    // Затем назначаем обработчик для кнопки смены темы
    const styleChangeButton = document.querySelector('.style_change');
    if (styleChangeButton) {
        styleChangeButton.addEventListener('click', changeTheme);
    }
});