const socket = new WebSocket('ws://' + window.location.host + '/ws');
const player = document.getElementById('lottie-avatar');
const statusText = document.getElementById('status-text');
const assistantZone = document.getElementById('assistant-zone');
const bodyElement = document.body;

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    // 1. Hide UI and show assistant on Wake up
    if (data.type === "mirror_show") {
        bodyElement.classList.add('assistant-active');
        assistantZone.classList.add('active');
        assistantZone.classList.remove('hidden');
    } 
    
    // 2. Show UI again when silent
    else if (data.type === "mirror_hide") {
        bodyElement.classList.remove('assistant-active');
        assistantZone.classList.remove('active');
        assistantZone.classList.add('hidden');
    }

    // 3. Switch Animation (Based on Status)
    if (data.type === "status") {
        if (data.state === "listening") {
            if (player.load) player.load('static/listening.json'); else player.setAttribute('src', 'static/listening.json');
            statusText.innerText = "I am listening...";
            statusText.style.color = "#00f2ff";
        } else if (data.state === "thinking") {
            if (player.load) player.load('static/thinking.json'); else player.setAttribute('src', 'static/thinking.json');
            statusText.innerText = "I am thinking...";
            statusText.style.color = "#ffffff";
        } else if (data.state === "idle") {
            if (player.load) player.load('static/Idle.json'); else player.setAttribute('src', 'static/Idle.json');
            statusText.innerText = "Ready...";
            statusText.style.color = "#00ff00";
        }
    }

    // 4. Speaking Animation when talking
    if (data.type === "video" && data.state === "talking") {
        if (player.load) player.load('static/Speaking.json'); else player.setAttribute('src', 'static/Speaking.json');
        statusText.innerText = "Replying...";
        statusText.style.color = "#FFD700";
    }

    // 5. Reminders & Notifications
    if (data.type === "reminder" || data.type === "notification") {
        document.getElementById('reminder-box').innerText = data.message;
    }
};

// Update time and date
function updateTime() {
    const now = new Date();
    
    // Time
    const timeOptions = { hour: '2-digit', minute: '2-digit', hour12: true };
    document.getElementById('clock').innerText = now.toLocaleTimeString('en-US', timeOptions);
    
    // English Date
    const dateEnOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('date-en').innerText = now.toLocaleDateString('en-US', dateEnOptions);


}

setInterval(updateTime, 1000);
updateTime();