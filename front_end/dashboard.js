const BACKEND_URL = "http://127.0.0.1:8000";
const userEmail = localStorage.getItem("userEmail");
const userName = localStorage.getItem("userName");

// Redirect to login if no session
if (!userEmail) {
  window.location.href = "index.html";
}

document.getElementById("welcome-msg").textContent = `Hi ${userName} 👋`;

const fileInput = document.getElementById("file-input");
const fileNameEl = document.getElementById("file-name");
const previewBox = document.getElementById("preview-box");
const previewIcon = document.getElementById("preview-icon");
previewIcon.style.display = "none";

// 🌟 When user selects a file
fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    const file = fileInput.files[0];
    fileNameEl.textContent = `Selected file: ${file.name}`;
    previewIcon.style.display = "inline";
  } else {
    fileNameEl.textContent = "No file selected";
    previewIcon.style.display = "none";
    previewBox.innerHTML = `<p>Select a file to preview before uploading</p>`;
  }
});

// 🌟 Preview file before uploading
function previewSelectedFile() {
  const file = fileInput.files[0];
  if (!file) return;

  const fileType = file.name.split(".").pop().toLowerCase();
  const fileURL = URL.createObjectURL(file);

  if (fileType === "pdf") {
    previewBox.innerHTML = `<embed src="${fileURL}" type="application/pdf">`;
  } else if (["txt", "csv"].includes(fileType)) {
    previewBox.innerHTML = `<iframe src="${fileURL}"></iframe>`;
  } else {
    previewBox.innerHTML = `<p style="color:#fff;">⚠️ Preview not supported for ${fileType}. You can upload and view it later.</p>`;
  }
}

// 🌟 Upload File
async function uploadFile() {
  const uploadMessage = document.getElementById("upload-message");

  if (fileInput.files.length === 0) {
    uploadMessage.textContent = "⚠️ Please choose a file first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("email", userEmail);

  uploadMessage.textContent = "⏳ Uploading and summarizing your document...";

  try {
    const res = await fetch(`${BACKEND_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    console.log("Upload Response:", data); // for debugging

    // Show backend response message
    uploadMessage.textContent = data.message || "✅ Upload successful.";

    // ✅ Check for summary and fileurl
    if (data.summary && (data.fileurl || data.file_url)) {
      const fileUrl = data.fileurl || data.file_url;

      // ✅ Store all required info for the summary page
      localStorage.setItem("summary", data.summary);
      localStorage.setItem("fileurl", fileUrl);
      localStorage.setItem("filename", fileInput.files[0].name);
      localStorage.setItem("tokens", data.tokens || "N/A");
      localStorage.setItem("mode", data.message.includes("RAG") ? "RAG" : "Normal");

      // ✅ Redirect to the summary view page
      setTimeout(() => {
        window.location.href = "summary_view.html";
      }, 1000);
    } else {
      uploadMessage.textContent = "❌ Failed to get summary or file URL from backend.";
    }

  } catch (error) {
    console.error("Upload error:", error);
    uploadMessage.textContent = "❌ Upload failed. Please check your server.";
  }
}

// 🌟 Logout
function logout() {
  localStorage.clear();
  window.location.href = "index.html";
}
