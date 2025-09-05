
// ✅ CSRF token (from <meta name="csrf-token"> in your template)
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

  fileList.innerHTML = selectedFiles
    .map(f => `<div class="file-item">${f.name} <span class="file-size">(${(f.size/1024 | 0)} KB)</span></div>`)
    .join('');
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
      headers: { 'X-CSRFToken': csrftoken },
      body: form
    });

    const text = await res.text();
    try {
      const data = JSON.parse(text);
      if (data.status === 'success') {
        uploadStatus.innerText = `✅ Processed ${data.chunks} chunks`;
        selectedFiles = [];
        fileInput.value = '';
        fileList.innerText = 'No files chosen';
      } else {
        uploadStatus.innerText = `❌ ${data.message || 'Upload failed'}`;
        console.error('Upload error:', data);
      }
    } catch (err) {
      uploadStatus.innerText = '❌ Unexpected server response';
      console.error('Upload response not JSON:', text);
    }
  } catch (err) {
    uploadStatus.innerText = '❌ Network error';
    console.error('Upload fetch failed:', err);
  } finally {
    uploadConfirmBtn.disabled = false;
  }
});


function formatAnswer(text) {
  // Converts **text** to <strong>text</strong>
  const convertBold = (line) => line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Split the whole response into sections based on one or more empty lines
  const sections = text.split(/\n\s*\n/);

  return sections.map(section => {
    // Trim the section and skip if empty
    const trimmedSection = section.trim();
    if (!trimmedSection) return '';

    const lines = trimmedSection.split('\n');

    // Check if all lines in the section look like list items
    const isList = lines.every(l => /^\s*[*\-\d]+\.? /.test(l.trim()));

    if (isList) {
      // Check if it's an ordered (numbered) list
      const isOrdered = /^\s*\d/.test(lines[0].trim());
      let listHtml = isOrdered ? '<ol>' : '<ul>';
      listHtml += lines.map(line => {
        // Remove the list marker (e.g., "1. ", "* ") before processing
        const content = line.trim().replace(/^[*\-\d]+\.?\s*/, '');
        return `<li>${convertBold(content)}</li>`;
      }).join('');
      listHtml += isOrdered ? '</ol>' : '</ul>';
      return `<div class="section">${listHtml}</div>`;
    } else {
      // If not a list, treat as a paragraph, preserving line breaks
      const paragraphHtml = '<p>' + lines.map(line => convertBold(line)).join('<br>') + '</p>';
      return `<div class="section">${paragraphHtml}</div>`;
    }
  }).join('');
}


// Append message to the chat box
function appendMessage(role, text) {
  const el = document.createElement('div');
  el.className = 'msg ' + (role === 'user' ? 'user' : 'bot');

  if (role === 'bot') {
    // Use the new formatting function for bot responses
    el.innerHTML = formatAnswer(text);
  } else {
    // User messages are plain text
    el.innerText = text;
  }

  chatBox.appendChild(el);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Show the typing indicator
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

// Chat send functionality
chatBtn.addEventListener('click', sendQuery);
userQuery.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault(); // Prevents adding a new line
    sendQuery();
  }
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
      data = { status: 'error', message: 'Server error' };
      console.error('Chat response not JSON:', text);
    }

    typingEl.remove();

    if (data.status === 'success') {
      appendMessage('bot', data.answer);
    } else {
      appendMessage('bot', `Error: ${data.message || 'No response'}`);
    }
  } catch (err) {
    typingEl.remove();
    appendMessage('bot', 'Network error: cannot contact server');
    console.error('Chat fetch failed:', err);
  }
}