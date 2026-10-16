let activeCommands = new Set();
let isSending = false;

function sendStopCommand(direction) {
    sendCommand('stop');
}

function sendMovementCommand(command) {
    if (!activeCommands.has(command)) {
        activeCommands.add(command);
        sendCommand(command);
    }
}

document.addEventListener('keydown', function(event) {
    const activeElement = document.activeElement;
    const isInputField = activeElement.tagName === 'INPUT' || 
                         activeElement.tagName === 'TEXTAREA' || 
                         activeElement.isContentEditable;
    
    if (isInputField) {
        return;
    }
    
    const key = event.key.toLowerCase();
    let command = null;
    
    switch(key) {
        case 'w':
            command = 'forward';
            break;
        case 's':
            command = 'back';
            break;
        case 'a':
            command = 'left';
            break;
        case 'd':
            command = 'right';
            break;
        case 'q':
            command = 'down';
            break;
        case 'e':
            command = 'up';
            break;
        default:
            return;
    }
    
    if (command) {
        sendMovementCommand(command);
        event.preventDefault();
    }
});

document.addEventListener('keyup', function(event) {
    const key = event.key.toLowerCase();
    let command = null;
    
    switch(key) {
        case 'w':
            command = 'forward';
            break;
        case 's':
            command = 'back';
            break;
        case 'a':
            command = 'left';
            break;
        case 'd':
            command = 'right';
            break;
        case 'q':
            command = 'down';
            break;
        case 'e':
            command = 'up';
            break;
        default:
            return;
    }
    
    if (command && activeCommands.has(command)) {
        activeCommands.delete(command);
        sendStopCommand(command);
    }
    
    if (['w', 'a', 's', 'd', 'q', 'e'].includes(key)) {
        event.preventDefault();
    }
});

window.addEventListener('blur', function() {
    if (activeCommands.size > 0) {
        activeCommands.clear();
        sendStopCommand('all');
    }
});