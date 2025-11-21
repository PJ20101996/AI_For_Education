const BACKEND_URL = "https://ai-for-education-2.onrender.com";
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
    previewSelectedFile();
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
    previewBox.innerHTML = `<embed src="${fileURL}" type="application/pdf" width="100%" height="100%">`;

  } else if (["png", "jpg", "jpeg"].includes(fileType)) {
    previewBox.innerHTML = `
      <img src="${fileURL}" 
           alt="Image Preview" 
           style="max-width:100%; height:auto; display:block; margin:auto; border-radius:10px;" />
    `;

  } else if (["txt", "csv"].includes(fileType)) {
    previewBox.innerHTML = `<iframe src="${fileURL}" width="100%" height="100%"></iframe>`;

  } else if (["doc", "docx"].includes(fileType)) {
    previewBox.innerHTML = `
      <p style="color:#fff;">📄 Word file selected</p>
      <p style="color:#aaa;">Preview not supported here. Upload to get summary.</p>
    `;

  } else {
    previewBox.innerHTML = `<p style="color:#fff;">❌ Preview not supported for ${fileType}</p>`;
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
    const res = await fetch(`${BACKEND_URL}/file/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    console.log("Upload Response:", data);

    uploadMessage.textContent = data.message || "✅ Upload successful.";

    if (data.summary && (data.fileurl || data.file_url)) {
      const fileUrl = data.fileurl || data.file_url;

      localStorage.setItem("summary", data.summary);
      localStorage.setItem("fileurl", fileUrl);
      localStorage.setItem("filename", fileInput.files[0].name);
      localStorage.setItem("tokens", data.tokens || "N/A");
      localStorage.setItem("mode", data.message.includes("RAG") ? "RAG" : "Normal");

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
