let bookData = null;

let currentPage = 1;
let currentLang = 'en';

function updateSidebarActiveState() {
    const links = document.querySelectorAll('.page-link');
    links.forEach(link => {
        link.classList.remove('active');
        if (parseInt(link.innerText) === currentPage) link.classList.add('active');
    });
}

function renderSidebar() {
    const container = document.getElementById('page-links');
    if (!container || !bookData) {
        return;
    }

    container.innerHTML = '';

    const pages = Object.keys(bookData)
        .map((k) => parseInt(k, 10))
        .filter((n) => Number.isFinite(n))
        .sort((a, b) => a - b);

    pages.forEach((pageNo) => {
        const el = document.createElement('div');
        el.className = 'page-link';
        el.innerText = String(pageNo);
        el.onclick = () => setPage(pageNo);
        container.appendChild(el);
    });

    updateSidebarActiveState();
}

function setPage(num) {
    currentPage = num;
    updateDisplay();

    updateSidebarActiveState();
}

function setLanguage(lang) {
    currentLang = lang;

    document.getElementById('btn-en').classList.remove('active');
    document.getElementById('btn-as').classList.remove('active');
    document.getElementById(`btn-${lang}`).classList.add('active');

    updateDisplay();
}

function updateDisplay() {
    if (!bookData) {
        return;
    }

    const data = bookData[currentPage][currentLang];
    const titleEl = document.getElementById('page-title');
    const bodyEl = document.getElementById('page-body');

    titleEl.innerText = data.pageno;
    bodyEl.innerText = data.body;

    // Apply special class for Assamese to improve readability
    if(currentLang === 'as') {
        bodyEl.classList.add('assamese-text');
    } else {
        bodyEl.classList.remove('assamese-text');
    }

    document.getElementById('content-container').scrollTop = 0;
}

async function init() {
    const res = await fetch('/api/book-data');
    if (!res.ok) {
        throw new Error(`Failed to load book data: ${res.status}`);
    }

    const data = await res.json();
    bookData = data;
    console.log("bookData:", bookData);
    console.log("bookData JSON:", JSON.stringify(bookData, null, 2)); // pretty print

    renderSidebar();
    updateDisplay();
}

init();
