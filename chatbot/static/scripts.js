// chatbot static/script.js
// Make sure this file is saved at chatbot/static/script.js

// Helper: get CSRF token from cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');


// Elements
const fileInput = document.getElementById('fileInput');
const chooseLabel = document.getElementById('chooseLabel');
const fileList = document.getElementById('fileList');
const uploadConfirmBtn = document.getElementById('uploadConfirmBtn');
const uploadStatus = document.getElementById('uploadStatus');

const chatBox = document.getElementById('chatBox');
const userQuery = document.getElementById('userQuery');
const chatBtn = document.getElementById('chatBtn');

// chosen files array
let selectedFiles = [];

// Open file dialog when label clicked
chooseLabel.addEventListener('click', () => fileInput.click());

// When user selects files, show filenames and enable upload
fileInput.addEventListener('change', (e) => {
  selectedFiles = Array.from(e.target.files);
  if (selectedFiles.length === 0) {
    fileList.innerText = 'No files chosen';
    uploadConfirmBtn.disabled = true;
    return;
  }

  fileList.innerHTML = selectedFiles.map(f => `<div class="file-item">${f.name} <span class="file-size">(${(f.size/1024|0)} KB)</span></div>`).join('');
  uploadConfirmBtn.disabled = false;
});

// Upload selected files
uploadConfirmBtn.addEventListener('click', async () => {
  if (selectedFiles.length === 0) return;
  uploadConfirmBtn.disabled = true;
  uploadStatus.innerText = 'Uploading...';

  const form = new FormData();
  for (const f of selectedFiles) form.append('files', f);

  try {
    const res = await fetch('/upload/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken
      },
      body: form
    });

    // If server returns HTML error page, handle gracefully
    const text = await res.text();
    try {
      const data = JSON.parse(text);
      if (data.status === 'success') {
        uploadStatus.innerText = `✅ Processed ${data.chunks} chunks`;
        // clear selection
        selectedFiles = [];
        fileInput.value = '';
        fileList.innerText = 'No files chosen';
      } else {
        uploadStatus.innerText = `❌ ${data.message || 'Upload failed'}`;
      }
    } catch (err) {
      uploadStatus.innerText = '❌ Unexpected server response';
      console.error('Upload response not JSON:', text);
    }
  } catch (err) {
    uploadStatus.innerText = '❌ Network error';
    console.error(err);
  } finally {
    uploadConfirmBtn.disabled = false;
  }
});

// Utility: append message
function appendMessage(role, text) {
  const el = document.createElement('div');
  el.className = 'msg ' + (role === 'user' ? 'user' : 'bot');
  el.innerText = text;
  chatBox.appendChild(el);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// show typing indicator (returns element)
function showTyping() {
  const el = document.createElement('div');
  el.className = 'msg bot';
  const dots = document.createElement('span');
  dots.className = 'typing';
  dots.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
  el.appendChild(dots);
  chatBox.appendChild(el);
  chatBox.scrollTop = chatBox.scrollHeight;
  return el;
}

// Chat send
chatBtn.addEventListener('click', sendQuery);
userQuery.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendQuery();
});

async function sendQuery() {
  const q = userQuery.value.trim();
  if (!q) return;

  appendMessage('user', q);
  userQuery.value = '';
  
  const typingEl = showTyping();

  try {
    const res = await fetch('/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ query: q })
    });

    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch (err) {
      // server returned HTML (error page)
      data = { status: 'error', message: 'Server error' };
      console.error('Chat response not JSON:', text);
    }

    // remove typing
    typingEl.remove();

    if (data.status === 'success') {
      appendMessage('bot', data.answer);
    } else {
      appendMessage('bot', `Error: ${data.message || 'No response'}`);
    }
  } catch (err) {
    typingEl.remove();
    appendMessage('bot', 'Network error: cannot contact server');
    console.error(err);
  }
}
