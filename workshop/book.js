// ------- App state -------
// `books` is the catalog returned by GET /api/books
let books = null;

// The currently-selected book (matches one of the `books[i].id` values)
let currentBookId = null;

// `bookData` holds the currently-selected book's pages.
// Shape: { "1": { en: {pageno,title,body}, as: {pageno,title,body} }, ... }
let bookData = null;

// Current reader state (page number + language)
let currentPage = 1;
let currentLang = 'en';

// Cache previously-loaded books so going back to the list and re-opening a book
// does not always require re-downloading already-fetched windows.
const bookDataByBookId = {};


// Show/hide the two main UI views:
// - book list view:  #/books
// - reader view:     #/book/<id>?page=..&lang=..
function setView(viewName) {
    const listView = document.getElementById('book-list-view');
    const readerView = document.getElementById('reader-view');
    if (!listView || !readerView) {
        // If either element is missing from the HTML, we cannot toggle views.
        return;
    }

    if (viewName === 'list') {
        // Show the list page.
        listView.style.display = '';
        // Hide the reader page.
        readerView.style.display = 'none';
        return;
    }

    // Any non-'list' value means "show the reader".
    listView.style.display = 'none';
    readerView.style.display = '';
}


// Load the list of available books from the backend.
async function loadBooks() {
    // Ask the backend for the catalog of books.
    // The backend returns an array like: [{id, title}, ...]
    const res = await fetch('/api/books');
    if (!res.ok) {
        // Non-2xx HTTP response.
        throw new Error(`Failed to load books: ${res.status}`);
    }
    // Parse JSON from the response body.
    books = await res.json();
}


// Render clickable book links into #book-list.
// Each link navigates via URL hash (so the browser back/forward buttons work).
function renderBookList() {
    const container = document.getElementById('book-list');
    if (!container || !books) {
        // If we have no container in the DOM or books are not loaded yet, do nothing.
        return;
    }

    // Clear anything previously rendered.
    container.innerHTML = '';

    // Header content above the table.
    const h2 = document.createElement('h2');
    h2.innerText = 'Buranji References';
    container.appendChild(h2);

    const p = document.createElement('p');
    p.innerText = 'List of some well-cited books pertinent to the history of Assam.';
    container.appendChild(p);

    // Build table structure.
    const table = document.createElement('table');
    table.className = 'table table-striped table-hover';

    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');
    ['No.', 'Title', 'Author', 'Publisher'].forEach((label) => {
        const th = document.createElement('th');
        th.innerText = label;
        headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    books.forEach((b) => {
        const tr = document.createElement('tr');

        const tdNum = document.createElement('td');
        tdNum.innerText = String(b.num ?? '');
        tr.appendChild(tdNum);

        const tdTitle = document.createElement('td');
        if (b.book_id) {
            // Internal link opens the reader view for this book.
            const a = document.createElement('a');
            a.href = `#/book/${encodeURIComponent(b.book_id)}?page=1&lang=en`;
            a.innerText = b.title || b.book_id;
            tdTitle.appendChild(a);
        } else {
            // Not all TSV entries are wired into our reader backend yet.
            tdTitle.innerText = b.title || '';
        }
        tr.appendChild(tdTitle);

        const tdAuthor = document.createElement('td');
        tdAuthor.innerText = b.author || '';
        tr.appendChild(tdAuthor);

        const tdPublisher = document.createElement('td');
        tdPublisher.innerText = b.publisher || '';
        tr.appendChild(tdPublisher);

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}

// Load a +/- 5 page window around `referencePage` from the backend.
// The server returns ALL pages, but only the pages inside the window include non-null bodies.
// We merge the newly-returned bodies into `bookData` so we gradually "fill in" content as needed.
async function loadBookDataWindow(referencePage) {
    if (!currentBookId) {
        // We cannot fetch book pages without knowing which book.
        throw new Error('No book selected');
    }

    // Fetch book page data.
    // - `book_id` selects which book.
    // - `reference_page` tells the server which +/- 5 pages should include bodies.
    const res = await fetch(
        `/api/book-data?book_id=${encodeURIComponent(currentBookId)}&reference_page=${encodeURIComponent(referencePage)}`
    );
    if (!res.ok) {
        throw new Error(`Failed to load book data: ${res.status}`);
    }

    // Parse the returned JSON.
    const data = await res.json();
    if (!bookData) {
        // If nothing is loaded yet for this book, accept the whole object.
        bookData = data;

        // Save to cache so we can come back to this book later without losing already-fetched data.
        bookDataByBookId[currentBookId] = bookData;
        return;
    }

    // Merge: only overwrite language blocks where the incoming body is non-null.
    // This prevents us from wiping out already-loaded content with "null" bodies.
    Object.keys(data).forEach((pageNo) => {
        // `pageNo` is a string key like "1", "2", ...
        const incomingEn = data[pageNo]?.en;
        const incomingAs = data[pageNo]?.as;

        if (!bookData[pageNo]) {
            // If this page did not exist in our local data yet, copy it in.
            bookData[pageNo] = data[pageNo];
            return;
        }

        if (incomingEn && incomingEn.body != null) {
            // Only overwrite if the server actually sent us the body.
            bookData[pageNo].en = incomingEn;
        }
        if (incomingAs && incomingAs.body != null) {
            // Only overwrite if the server actually sent us the body.
            bookData[pageNo].as = incomingAs;
        }
    });

    // Update cache.
    bookDataByBookId[currentBookId] = bookData;
}


// Keep the URL in sync with the current reader state.
// Example: #/book/political-history-of-assam?page=15&lang=en
function updateHash() {
    if (!currentBookId) {
        // No book selected => go to book list route.
        window.location.hash = '#/books';
        return;
    }

    // Create query parameters for page + language.
    const params = new URLSearchParams();
    params.set('page', String(currentPage));
    params.set('lang', currentLang);

    // Push state into URL hash. This makes the URL shareable.
    window.location.hash = `#/book/${encodeURIComponent(currentBookId)}?${params.toString()}`;
}

function updateSidebarActiveState() {
    // Find all page links currently displayed in the sidebar.
    const links = document.querySelectorAll('.page-link');
    links.forEach(link => {
        // Remove the 'active' highlight from every link...
        link.classList.remove('active');

        // ...then add it back only for the currently selected page.
        if (parseInt(link.innerText) === currentPage) link.classList.add('active');
    });
}

function renderSidebar() {
    const container = document.getElementById('page-links');
    if (!container || !bookData) {
        // If there is nowhere to render or no data loaded yet, do nothing.
        return;
    }

    // Remove previous sidebar links.
    container.innerHTML = '';

    // Build a sorted list of numeric page numbers from the keys.
    const pages = Object.keys(bookData)
        .map((k) => parseInt(k, 10))
        .filter((n) => Number.isFinite(n))
        .sort((a, b) => a - b);

    pages.forEach((pageNo) => {
        // Build a clickable <div> for each page.
        const el = document.createElement('div');
        el.className = 'page-link';
        el.innerText = String(pageNo);

        // When clicked, switch to that page.
        el.onclick = () => setPage(pageNo);
        container.appendChild(el);
    });

    // Ensure the current page is visually highlighted.
    updateSidebarActiveState();
}

// Change current page. If the page isn't loaded yet (body is null), fetch its window first.
async function setPage(num) {
    // Update the in-memory current page.
    currentPage = num;

    // Attempt to read the current page content for the current language.
    const current = bookData?.[currentPage]?.[currentLang];
    if (!current || current.body == null) {
        // If it's missing (null), fetch a new window centered on this page.
        await loadBookDataWindow(currentPage);
    }

    // Re-render the reader.
    updateDisplay();

    // Update sidebar highlighting.
    updateSidebarActiveState();

    // Update the URL to reflect the new page.
    updateHash();
}

function setLanguage(lang) {
    // Update the in-memory current language.
    currentLang = lang;

    // Update button visual state.
    document.getElementById('btn-en').classList.remove('active');
    document.getElementById('btn-as').classList.remove('active');
    document.getElementById(`btn-${lang}`).classList.add('active');

    // Re-render with the new language.
    updateDisplay();

    // Update the URL to reflect the new language.
    updateHash();
}

// Update the main reading panel (page number, title, body) to reflect current state.
function updateDisplay() {
    if (!bookData) {
        // Data not loaded yet.
        return;
    }

    // Select the content object for the current page + language.
    const data = bookData[currentPage][currentLang];

    // Find the DOM elements that we will update.
    const pageNumberEl = document.getElementById('page-number');
    const titleEl = document.getElementById('page-title');
    const bodyEl = document.getElementById('page-body');

    if (pageNumberEl) {
        // Display the current page number.
        pageNumberEl.innerText = `${data.pageno}`;
    }

    // Display the book title.
    titleEl.innerText = data.title;

    // Display the page body. (If outside window, body may be null.)
    bodyEl.innerText = data.body;

    // Apply special class for Assamese to improve readability
    if(currentLang === 'as') {
        // Add a CSS class for Assamese to improve readability.
        bodyEl.classList.add('assamese-text');
    } else {
        // Remove Assamese styling for English.
        bodyEl.classList.remove('assamese-text');
    }

    // Scroll the reading container to the top whenever we change page/language.
    document.getElementById('content-container').scrollTop = 0;
}

// Entry point. We:
// 1) Wire up the Back button
// 2) Load the book catalog
// 3) Start a small hash router so navigation is driven by the URL
async function init() {
    // Back button returns to the book list.
    const backBtn = document.getElementById('btn-back');
    if (backBtn) {
        backBtn.onclick = () => {
            // Clear current selection.
            currentBookId = null;
            bookData = null;

            // Update URL first, then show the list view.
            updateHash();
            setView('list');
        };
    }

    // Load the catalog and render it.
    await loadBooks();
    renderBookList();

    // Hash router: reads the URL and updates in-memory state + UI.
    const onRoute = async () => {
        // `window.location.hash` is the part after # in the URL.
        // Examples:
        // - "#/books"
        // - "#/book/an-account-of-assam?page=10&lang=en"
        const hash = window.location.hash || '#/books';
        if (hash === '#/books' || hash === '#') {
            // Book list route.
            currentBookId = null;
            bookData = null;
            setView('list');
            return;
        }

        const match = hash.match(/^#\/book\/([^?]+)(?:\?(.*))?$/);
        if (!match) {
            // Unknown route -> force back to list.
            window.location.hash = '#/books';
            return;
        }

        const bookId = decodeURIComponent(match[1]);
        const qs = match[2] || '';
        const params = new URLSearchParams(qs);
        const page = parseInt(params.get('page') || '1', 10);
        const lang = params.get('lang') || 'en';

        currentBookId = bookId;
        currentPage = Number.isFinite(page) ? page : 1;
        currentLang = lang === 'as' ? 'as' : 'en';

        // Use cached book data if we already opened this book earlier.
        bookData = bookDataByBookId[currentBookId] || null;

        document.getElementById('btn-en').classList.remove('active');
        document.getElementById('btn-as').classList.remove('active');
        document.getElementById(`btn-${currentLang}`).classList.add('active');

        setView('reader');

        // Ensure we have the current page window loaded.
        await loadBookDataWindow(currentPage);

        // Render reader UI.
        renderSidebar();
        updateDisplay();
        updateSidebarActiveState();
    };

    window.addEventListener('hashchange', () => {
        // Re-run router whenever the hash changes.
        onRoute().catch((e) => console.error(e));
    });

    // Run router once on initial page load.
    await onRoute();
}

init();
