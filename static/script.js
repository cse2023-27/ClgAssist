// FORMAT BOT REPLY (CLEAN & STRUCTURED)
function formatBotReply(text) {
    return text
        .replace(/\n/g, "<br>")              // new lines
        .replace(/•/g, "<br>•")             // bullet points
        .replace(/🎓/g, "<br>🎓")           // heading spacing
        .replace(/⚠️/g, "<br><br>⚠️")      // warning section
        .replace(/💡/g, "<br><br>💡")      // tip section
        .replace(/^(<br>)+/, "");           // remove extra top space
}


// ADD MESSAGE (WITH AVATAR + FORMAT)
function addMessage(text, sender) {
    let chatBox = document.getElementById("chat-box");

    let msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);

    let avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.innerHTML = sender === "bot" ? "🎓" : "👤";

    let bubble = document.createElement("div");
    bubble.classList.add("bubble");

    if (sender === "bot") {
        bubble.innerHTML = formatBotReply(text);
    } else {
        bubble.innerText = text;
    }

    if (sender === "bot") {
        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
    } else {
        msgDiv.appendChild(bubble);
        msgDiv.appendChild(avatar);
    }

    chatBox.appendChild(msgDiv);

    // auto scroll
    chatBox.scrollTop = chatBox.scrollHeight;

    return msgDiv; // needed for typing
}


// SEND MESSAGE
async function sendMessage() {
    let input = document.getElementById("user-input");
    let msg = input.value.trim();

    if (!msg) return;

    addMessage(msg, "user");

    // typing indicator
    let typingMsg = addMessage("Typing...", "bot");

    try {
        let res = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ message: msg })
        });

        let data = await res.json();

        // remove typing
        typingMsg.remove();

        addMessage(data.reply, "bot");

    } catch (error) {
        typingMsg.remove();
        addMessage("⚠️ Server error. Try again.", "bot");
    }

    input.value = "";
}


// ENTER KEY SUPPORT
function handleKey(e) {
    if (e.key === "Enter") {
        sendMessage();
    }
}


// QUICK BUTTON (SIDEBAR)
function quickMsg(text) {
    document.getElementById("user-input").value = text;
    sendMessage();
}


// AUTO FOCUS INPUT
window.onload = function () {
    document.getElementById("user-input").focus();
};
function toggleSidebar() {
    let sidebar = document.querySelector(".sidebar");
    sidebar.classList.toggle("active");
}
