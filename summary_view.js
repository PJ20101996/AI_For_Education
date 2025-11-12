window.onload = () => {
  const summaryBox = document.getElementById("summary-content");
  const docViewer = document.getElementById("doc-viewer");

  const summary = localStorage.getItem("summary");
  const fileurl = localStorage.getItem("fileurl");
  const filename = localStorage.getItem("filename");

  if (!summary || !fileurl) {
    summaryBox.textContent = "⚠️ No summary found. Please upload again.";
    return;
  }

  summaryBox.textContent = summary;

  // Determine file type for proper viewing
  const fileType = filename.split(".").pop().toLowerCase();
  if (fileType === "pdf") {
    docViewer.src = fileurl;
  } else if (["doc", "docx", "ppt", "pptx", "xls", "xlsx"].includes(fileType)) {
    const officeViewer = `https://view.officeapps.live.com/op/embed.aspx?src=${fileurl}`;
    docViewer.src = officeViewer;
  } else if (["txt", "csv"].includes(fileType)) {
    docViewer.src = fileurl;
  } else {
    docViewer.outerHTML = `<p style="color:#fff;">❌ Preview not supported for this file type.</p>`;
  }
};
