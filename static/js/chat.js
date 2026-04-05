document.addEventListener("DOMContentLoaded", () => {
    const msgs = document.getElementById("msgs");
    const inp = document.getElementById("inp");
    const sendBtn = document.getElementById("send");

    const persona = document.body.dataset.persona || "AI";
    const initials = persona.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);

    let history = [];
    let locked = false;

    function scroll() {
        msgs.scrollTo({ top: msgs.scrollHeight, behavior: "smooth" });
    }

    function esc(str) {
        let d = document.createElement("div");
        d.textContent = str;
        return d.innerHTML;
    }

    function addRow(role, text) {
        let row = document.createElement("div");
        row.className = "row " + (role === "user" ? "user" : "bot");

        let html = "";
        if (role !== "user") {
            html += `<div class="mini-avatar">${initials}</div>`;
        }
        html += `<div class="bubble">${esc(text)}</div>`;
        row.innerHTML = html;

        msgs.appendChild(row);
        scroll();
        return row;
    }

    function showTyping() {
        let el = document.createElement("div");
        el.className = "typing";
        el.id = "typing-indicator";
        el.innerHTML = `
            <div class="mini-avatar">${initials}</div>
            <div class="dots"><span></span><span></span><span></span></div>
        `;
        msgs.appendChild(el);
        scroll();
    }

    function hideTyping() {
        let el = document.getElementById("typing-indicator");
        if (el) el.remove();
    }

    async function typeOut(text) {
        let row = addRow("bot", "");
        let bubble = row.querySelector(".bubble");
        let words = text.split(" ");

        for (let i = 0; i < words.length; i++) {
            bubble.textContent = words.slice(0, i + 1).join(" ");
            scroll();
            await wait(25 + Math.random() * 30);
        }
    }

    function wait(ms) {
        return new Promise(r => setTimeout(r, ms));
    }

    async function send(text) {
        if (!text.trim() || locked) return;

        addRow("user", text);
        history.push({ role: "user", content: text });
        inp.value = "";
        locked = true;
        sendBtn.disabled = true;
        inp.disabled = true;

        showTyping();

        try {
            let res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, history: history }),
            });

            if (!res.ok) throw new Error(res.status);

            let data = await res.json();
            hideTyping();
            await typeOut(data.reply);
            history.push({ role: "assistant", content: data.reply });
        } catch (err) {
            hideTyping();
            addRow("bot", "Something went wrong — try again?");
            console.error(err);
        }

        locked = false;
        inp.disabled = false;
        sendBtn.disabled = false;
        inp.focus();
    }

    async function greet() {
        await wait(500);
        showTyping();
        await wait(1200);
        hideTyping();

        let msg = `Hey! I'm ${persona}'s AI — ask me anything about skills, projects, or experience.`;
        await typeOut(msg);
    }

    sendBtn.addEventListener("click", () => send(inp.value));

    inp.addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            send(inp.value);
        }
    });

    inp.addEventListener("input", () => {
        sendBtn.disabled = !inp.value.trim();
    });

    greet();
});