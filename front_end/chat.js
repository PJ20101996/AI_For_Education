const BACKEND_URL = "http://127.0.0.1:8000";
const email = localStorage.getItem("userEmail");
const filename = localStorage.getItem("filename");

const chatBox = document.getElementById("chat-box");

function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender === "user" ? "user-msg" : "bot-msg");
  msg.innerText = text;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const userInput = document.getElementById("user-input");
  const question = userInput.value.trim();
  if (!question) return;

  addMessage(question, "user");
  userInput.value = "";

  const res = await fetch(`${BACKEND_URL}/chat/query`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ email, filename, question })
  });

  const data = await res.json();
  addMessage(data.answer, "bot");
}

function goBack() {
  window.location.href = "summary_view.html";
}
