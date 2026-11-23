/**
 * Hệ Thống Quản Lý Thư Viện Ứng Dụng AI (Library Management System)
 * Tác giả: Nhóm Thực hành Lab AI / Google AI Studio & Antigravity IDE
 */

// Global State
let currentTab = 'dashboard';
let categoriesData = [];
let booksData = [];
let readersData = [];
let borrowsData = [];
let categoryChartInstance = null;
let searchBookTimeout = null;
let searchReaderTimeout = null;

// Dual Mode: Check if running via HTTP server or local file
const API_BASE = window.location.protocol.startsWith('http') ? '' : 'http://localhost:8080';

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  loadInitialData();
  loadDashboard();

  // Load saved API Key if any
  const savedKey = localStorage.getItem('gemini_api_key');
  if (savedKey) {
    const input = document.getElementById('gemini-api-key-input');
    if (input) input.value = savedKey;
  }
});

// ==========================================
// 1. NAVIGATION & TAB SWITCHING
// ==========================================
function initNavigation() {
  const navLinks = document.querySelectorAll('.nav-link[data-tab]');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = link.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });

  // Handle Hash change
  window.addEventListener('hashchange', () => {
    const hash = window.location.hash.replace('#', '');
    if (hash) switchTab(hash);
  });
}

function switchTab(tabName) {
  currentTab = tabName;
  document.querySelectorAll('.nav-link[data-tab]').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-tab') === tabName);
  });

  document.querySelectorAll('.tab-content-section').forEach(sec => {
    sec.classList.add('d-none');
  });

  const activeSection = document.getElementById(`tab-${tabName}`);
  if (activeSection) {
    activeSection.classList.remove('d-none');
  }

  // Reload data for specific tab
  if (tabName === 'dashboard') loadDashboard();
  if (tabName === 'books') loadBooks();
  if (tabName === 'readers') loadReaders();
  if (tabName === 'borrows') loadBorrows();
}

// ==========================================
// 2. DASHBOARD & STATS
// ==========================================
async function loadDashboard() {
  try {
    const res = await fetch(`${API_BASE}/api/stats`);
    const json = await res.json();
    if (json.success && json.data) {
      const d = json.data;
      document.getElementById('stat-titles').textContent = d.total_titles;
      document.getElementById('stat-copies').textContent = `${d.total_copies} bản sao`;
      document.getElementById('stat-available').textContent = d.available_copies;
      document.getElementById('stat-borrowed').textContent = `Đang mượn: ${d.borrowed_copies}`;
      document.getElementById('stat-readers').textContent = d.total_readers;
      document.getElementById('stat-overdue').textContent = d.overdue_borrows;

      renderCategoryChart(d.category_stats);
      renderRecentLogs(d.recent_logs);
    }
  } catch (err) {
    console.warn("Không kết nối được server, dùng dữ liệu mẫu offline:", err);
  }
}

function renderCategoryChart(categoryStats) {
  const ctx = document.getElementById('categoryChart');
  if (!ctx) return;

  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  const labels = categoryStats.map(c => c.category);
  const data = categoryStats.map(c => c.count);

  categoryChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: [
          '#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'
        ],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { boxWidth: 14, font: { size: 12 } }
        }
      }
    }
  });
}

function renderRecentLogs(logs) {
  const container = document.getElementById('recent-logs-list');
  if (!container) return;

  if (!logs || logs.length === 0) {
    container.innerHTML = '<div class="text-center text-muted py-4">Chưa có nhật ký hoạt động.</div>';
    return;
  }

  container.innerHTML = logs.map(l => `
    <div class="list-group-item px-0 py-2 border-0 border-bottom d-flex align-items-start gap-2">
      <div class="badge bg-primary bg-opacity-10 text-primary mt-1 p-1">
        <i class="bi bi-activity"></i>
      </div>
      <div class="flex-grow-1">
        <div class="d-flex justify-content-between align-items-center">
          <strong class="small text-dark">${l.action}</strong>
          <span class="text-muted" style="font-size: 11px;">${formatDate(l.created_at)}</span>
        </div>
        <p class="small text-muted mb-0">${l.details}</p>
      </div>
    </div>
  `).join('');
}

// ==========================================
// 3. INITIAL DATA LOAD (Categories, Dropdowns)
// ==========================================
async function loadInitialData() {
  try {
    const res = await fetch(`${API_BASE}/api/categories`);
    const json = await res.json();
    if (json.success) {
      categoriesData = json.data;
      populateCategoryDropdowns();
    }
  } catch (e) {
    console.error("Lỗi tải categories:", e);
  }
}

function populateCategoryDropdowns() {
  const filterSelect = document.getElementById('filter-book-category');
  const modalSelect = document.getElementById('book-category');

  if (filterSelect) {
    filterSelect.innerHTML = '<option value="">-- Tất cả thể loại --</option>' +
      categoriesData.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
  }

  if (modalSelect) {
    modalSelect.innerHTML = categoriesData.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
  }
}

// ==========================================
// 4. BOOKS MANAGEMENT
// ==========================================
async function loadBooks() {
  const q = document.getElementById('search-book-input')?.value || '';
  const cat = document.getElementById('filter-book-category')?.value || '';

  try {
    const res = await fetch(`${API_BASE}/api/books?q=${encodeURIComponent(q)}&category_id=${encodeURIComponent(cat)}`);
    const json = await res.json();
    if (json.success) {
      booksData = json.data;
      renderBooksTable(booksData);
    }
  } catch (e) {
    console.error("Lỗi load books:", e);
  }
}

function debounceSearchBooks() {
  clearTimeout(searchBookTimeout);
  searchBookTimeout = setTimeout(() => {
    loadBooks();
  }, 300);
}

function renderBooksTable(books) {
  const tbody = document.getElementById('books-table-body');
  const countLabel = document.getElementById('books-count-label');
  if (countLabel) countLabel.textContent = `Hiển thị: ${books.length} sách`;

  if (!tbody) return;

  if (books.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Không tìm thấy sách nào phù hợp.</td></tr>';
    return;
  }

  tbody.innerHTML = books.map(b => {
    const isAvail = b.available_copies > 0;
    const badgeClass = isAvail ? 'badge-available' : 'badge-borrowed';
    const badgeText = isAvail ? `Còn ${b.available_copies} cuốn` : 'Đã mượn hết';

    return `
      <tr>
        <td><code>${b.isbn}</code></td>
        <td>
          <div class="fw-bold text-dark">${b.title}</div>
          <small class="text-muted"><i class="bi bi-person me-1"></i>${b.author} (${b.publish_year || 'N/A'})</small>
        </td>
        <td><span class="badge bg-light text-dark border">${b.category_name || 'Khác'}</span></td>
        <td class="text-center"><span class="badge bg-primary bg-opacity-10 text-primary">${b.location || 'Chưa xếp'}</span></td>
        <td class="text-center fw-medium">${b.available_copies} / ${b.total_copies}</td>
        <td class="text-center"><span class="badge ${badgeClass} px-2 py-1">${badgeText}</span></td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-info me-1" title="Xem chi tiết & Tóm tắt AI" onclick="viewBookDetail(${b.id})">
            <i class="bi bi-eye"></i>
          </button>
          <button class="btn btn-sm btn-outline-secondary me-1" title="Sửa sách" onclick="editBook(${b.id})">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger" title="Xóa sách" onclick="deleteBook(${b.id}, '${escapeQuote(b.title)}')">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function openAddBookModal() {
  document.getElementById('bookForm').reset();
  document.getElementById('book-edit-id').value = '';
  document.getElementById('bookModalTitle').textContent = 'Thêm Sách Mới';
  document.getElementById('book-isbn').value = `978-604-${Math.floor(10 + Math.random() * 90)}`;
  const modal = new bootstrap.Modal(document.getElementById('bookModal'));
  modal.show();
}

function editBook(id) {
  const book = booksData.find(b => b.id === id);
  if (!book) return;

  document.getElementById('book-edit-id').value = book.id;
  document.getElementById('book-isbn').value = book.isbn;
  document.getElementById('book-title').value = book.title;
  document.getElementById('book-author').value = book.author;
  document.getElementById('book-category').value = book.category_id || 1;
  document.getElementById('book-year').value = book.publish_year || 2024;
  document.getElementById('book-copies').value = book.total_copies || 1;
  document.getElementById('book-publisher').value = book.publisher || '';
  document.getElementById('book-location').value = book.location || '';
  document.getElementById('book-summary').value = book.summary || '';

  document.getElementById('bookModalTitle').textContent = 'Cập Nhật Thông Tin Sách';
  const modal = new bootstrap.Modal(document.getElementById('bookModal'));
  modal.show();
}

async function handleSaveBook(e) {
  e.preventDefault();
  const id = document.getElementById('book-edit-id').value;
  const payload = {
    isbn: document.getElementById('book-isbn').value,
    title: document.getElementById('book-title').value,
    author: document.getElementById('book-author').value,
    category_id: parseInt(document.getElementById('book-category').value),
    publish_year: parseInt(document.getElementById('book-year').value),
    total_copies: parseInt(document.getElementById('book-copies').value),
    publisher: document.getElementById('book-publisher').value,
    location: document.getElementById('book-location').value,
    summary: document.getElementById('book-summary').value
  };

  const url = id ? `${API_BASE}/api/books/${id}` : `${API_BASE}/api/books`;
  const method = id ? 'PUT' : 'POST';

  try {
    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (json.success) {
      bootstrap.Modal.getInstance(document.getElementById('bookModal')).hide();
      Swal.fire({ icon: 'success', title: 'Thành công!', text: json.message || 'Đã lưu sách thành công!', timer: 1500, showConfirmButton: false });
      loadBooks();
      loadDashboard();
    } else {
      Swal.fire({ icon: 'error', title: 'Lỗi', text: json.error || 'Không thể lưu sách' });
    }
  } catch (err) {
    Swal.fire({ icon: 'error', title: 'Lỗi máy chủ', text: err.message });
  }
}

async function deleteBook(id, title) {
  const result = await Swal.fire({
    title: 'Xác nhận xóa sách?',
    text: `Bạn có chắc muốn xóa cuốn sách "${title}" không?`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#dc2626',
    cancelButtonColor: '#64748b',
    confirmButtonText: 'Đồng ý xóa',
    cancelButtonText: 'Hủy'
  });

  if (result.isConfirmed) {
    try {
      const res = await fetch(`${API_BASE}/api/books/${id}`, { method: 'DELETE' });
      const json = await res.json();
      if (json.success) {
        Swal.fire({ icon: 'success', title: 'Đã xóa!', text: json.message, timer: 1500, showConfirmButton: false });
        loadBooks();
        loadDashboard();
      } else {
        Swal.fire({ icon: 'error', title: 'Không thể xóa', text: json.error });
      }
    } catch (err) {
      Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: err.message });
    }
  }
}

function viewBookDetail(id) {
  const book = booksData.find(b => b.id === id);
  if (!book) return;

  document.getElementById('detail-title').textContent = book.title;
  document.getElementById('detail-author').textContent = book.author;
  document.getElementById('detail-category').textContent = book.category_name || 'Khác';
  document.getElementById('detail-location').textContent = book.location || 'Chưa xếp vị trí';
  document.getElementById('detail-copies').textContent = `${book.available_copies} có sẵn (Tổng ${book.total_copies} cuốn)`;
  document.getElementById('detail-summary').textContent = book.summary || 'Chưa có thông tin tóm tắt cho cuốn sách này.';

  const modal = new bootstrap.Modal(document.getElementById('bookDetailModal'));
  modal.show();
}

async function autoGenerateSummaryAI() {
  const title = document.getElementById('book-title').value.trim();
  const author = document.getElementById('book-author').value.trim();
  const catText = document.getElementById('book-category').selectedOptions[0]?.text || '';

  if (!title) {
    Swal.fire({ icon: 'info', title: 'Chưa đủ thông tin', text: 'Vui lòng nhập Tên sách trước khi yêu cầu AI tóm tắt!' });
    return;
  }

  Swal.fire({
    title: 'AI đang phân tích...',
    text: 'Đang kết nối Google AI Studio (Gemini) để sinh tóm tắt nội dung sách...',
    allowOutsideClick: false,
    didOpen: () => { Swal.showLoading(); }
  });

  try {
    const res = await fetch(`${API_BASE}/api/ai/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, author, category: catText })
    });
    const json = await res.json();
    Swal.close();
    if (json.success && json.summary) {
      document.getElementById('book-summary').value = json.summary;
      Swal.fire({ icon: 'success', title: 'Hoàn tất!', text: 'AI đã tạo đoạn tóm tắt thành công!', timer: 1200, showConfirmButton: false });
    }
  } catch (err) {
    Swal.close();
    console.error(err);
  }
}

// ==========================================
// 5. READERS MANAGEMENT
// ==========================================
async function loadReaders() {
  const q = document.getElementById('search-reader-input')?.value || '';
  try {
    const res = await fetch(`${API_BASE}/api/readers?q=${encodeURIComponent(q)}`);
    const json = await res.json();
    if (json.success) {
      readersData = json.data;
      renderReadersTable(readersData);
    }
  } catch (e) {
    console.error("Lỗi load readers:", e);
  }
}

function debounceSearchReaders() {
  clearTimeout(searchReaderTimeout);
  searchReaderTimeout = setTimeout(() => {
    loadReaders();
  }, 300);
}

function renderReadersTable(readers) {
  const tbody = document.getElementById('readers-table-body');
  if (!tbody) return;

  if (readers.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Không tìm thấy độc giả nào.</td></tr>';
    return;
  }

  tbody.innerHTML = readers.map(r => {
    const typeBadge = r.reader_type === 'GIANG_VIEN' ? '<span class="badge bg-primary">Giảng Viên</span>' : '<span class="badge bg-info text-dark">Sinh Viên</span>';
    const statusBadge = r.status === 'ACTIVE' ? '<span class="badge badge-available">Hoạt động</span>' : '<span class="badge badge-overdue">Đã khóa</span>';

    return `
      <tr>
        <td><code>${r.card_number}</code></td>
        <td class="fw-bold text-dark">${r.full_name} (${r.gender})</td>
        <td>${typeBadge}</td>
        <td>
          <div><i class="bi bi-telephone text-muted me-1"></i>${r.phone || 'N/A'}</div>
          <small class="text-muted"><i class="bi bi-envelope text-muted me-1"></i>${r.email || 'N/A'}</small>
        </td>
        <td><small class="text-muted">${r.address || 'N/A'}</small></td>
        <td class="text-center">${statusBadge}</td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-secondary me-1" onclick="editReader(${r.id})">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteReader(${r.id}, '${escapeQuote(r.full_name)}')">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function openAddReaderModal() {
  document.getElementById('readerForm').reset();
  document.getElementById('reader-edit-id').value = '';
  document.getElementById('readerModalTitle').textContent = 'Đăng Ký Độc Giả Mới';
  document.getElementById('reader-card').value = `DG${Math.floor(100 + Math.random() * 900)}`;
  const modal = new bootstrap.Modal(document.getElementById('readerModal'));
  modal.show();
}

function editReader(id) {
  const reader = readersData.find(r => r.id === id);
  if (!reader) return;

  document.getElementById('reader-edit-id').value = reader.id;
  document.getElementById('reader-card').value = reader.card_number;
  document.getElementById('reader-name').value = reader.full_name;
  document.getElementById('reader-type').value = reader.reader_type;
  document.getElementById('reader-gender').value = reader.gender;
  document.getElementById('reader-phone').value = reader.phone || '';
  document.getElementById('reader-email').value = reader.email || '';
  document.getElementById('reader-address').value = reader.address || '';

  document.getElementById('readerModalTitle').textContent = 'Cập Nhật Hồ Sơ Độc Giả';
  const modal = new bootstrap.Modal(document.getElementById('readerModal'));
  modal.show();
}

async function handleSaveReader(e) {
  e.preventDefault();
  const id = document.getElementById('reader-edit-id').value;
  const payload = {
    card_number: document.getElementById('reader-card').value,
    full_name: document.getElementById('reader-name').value,
    reader_type: document.getElementById('reader-type').value,
    gender: document.getElementById('reader-gender').value,
    phone: document.getElementById('reader-phone').value,
    email: document.getElementById('reader-email').value,
    address: document.getElementById('reader-address').value
  };

  const url = id ? `${API_BASE}/api/readers/${id}` : `${API_BASE}/api/readers`;
  const method = id ? 'PUT' : 'POST';

  try {
    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (json.success) {
      bootstrap.Modal.getInstance(document.getElementById('readerModal')).hide();
      Swal.fire({ icon: 'success', title: 'Thành công!', text: json.message, timer: 1500, showConfirmButton: false });
      loadReaders();
      loadDashboard();
    } else {
      Swal.fire({ icon: 'error', title: 'Lỗi', text: json.error });
    }
  } catch (err) {
    Swal.fire({ icon: 'error', title: 'Lỗi máy chủ', text: err.message });
  }
}

async function deleteReader(id, name) {
  const result = await Swal.fire({
    title: 'Xóa độc giả?',
    text: `Bạn có chắc muốn xóa độc giả "${name}" không?`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#dc2626',
    cancelButtonText: 'Hủy',
    confirmButtonText: 'Đồng ý xóa'
  });

  if (result.isConfirmed) {
    try {
      const res = await fetch(`${API_BASE}/api/readers/${id}`, { method: 'DELETE' });
      const json = await res.json();
      if (json.success) {
        Swal.fire({ icon: 'success', title: 'Đã xóa!', text: json.message, timer: 1500, showConfirmButton: false });
        loadReaders();
        loadDashboard();
      } else {
        Swal.fire({ icon: 'error', title: 'Không thể xóa', text: json.error });
      }
    } catch (err) {
      Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: err.message });
    }
  }
}

// ==========================================
// 6. BORROW & RETURN MANAGEMENT
// ==========================================
let currentBorrowStatusFilter = '';

async function loadBorrows() {
  try {
    const res = await fetch(`${API_BASE}/api/borrows?status=${encodeURIComponent(currentBorrowStatusFilter)}`);
    const json = await res.json();
    if (json.success) {
      borrowsData = json.data;
      renderBorrowsTable(borrowsData);
    }
  } catch (e) {
    console.error("Lỗi load borrows:", e);
  }
}

function filterBorrows(status) {
  currentBorrowStatusFilter = status;
  document.querySelectorAll('.borrow-filter-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-status') === status);
  });
  loadBorrows();
}

function renderBorrowsTable(borrows) {
  const tbody = document.getElementById('borrows-table-body');
  if (!tbody) return;

  if (borrows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">Không có phiếu mượn nào.</td></tr>';
    return;
  }

  tbody.innerHTML = borrows.map(b => {
    let statusBadge = '<span class="badge badge-borrowed">Đang mượn</span>';
    if (b.status === 'RETURNED') {
      statusBadge = '<span class="badge badge-available">Đã trả</span>';
    } else if (b.is_overdue || b.status === 'OVERDUE') {
      statusBadge = `<span class="badge badge-overdue"><i class="bi bi-clock-history me-1"></i>Trễ ${b.days_overdue} ngày</span>`;
    }

    const booksListHtml = b.books.map(bk => `
      <div class="small">
        <i class="bi bi-bookmark-fill text-primary me-1"></i><strong>${bk.book_title}</strong> 
        <span class="text-muted">(${bk.location})</span>
      </div>
    `).join('');

    const fineHtml = (b.estimated_fine && b.estimated_fine > 0)
      ? `<strong class="text-danger">${Number(b.estimated_fine).toLocaleString('vi-VN')} đ</strong>`
      : '<span class="text-muted">0 đ</span>';

    const canReturn = b.status !== 'RETURNED';

    return `
      <tr>
        <td><code>${b.record_code}</code></td>
        <td>
          <div class="fw-bold">${b.reader_name}</div>
          <small class="text-muted">Thẻ: ${b.card_number} | ${b.reader_type}</small>
        </td>
        <td>${booksListHtml}</td>
        <td><small>${formatDate(b.borrow_date)}</small></td>
        <td><small class="${b.is_overdue ? 'text-danger fw-bold' : ''}">${formatDate(b.due_date)}</small></td>
        <td class="text-center">${statusBadge}</td>
        <td class="text-end">${fineHtml}</td>
        <td class="text-end">
          ${canReturn ? `
            <button class="btn btn-sm btn-success me-1" onclick="handleReturnBook(${b.id}, '${b.record_code}')">
              <i class="bi bi-check-lg me-1"></i> Trả sách
            </button>
            <button class="btn btn-sm btn-outline-warning" onclick="handleRenewBook(${b.id}, '${b.record_code}')" title="Gia hạn thêm 7 ngày">
              <i class="bi bi-arrow-clockwise"></i>
            </button>
          ` : '<span class="badge bg-light text-muted">Hoàn tất</span>'}
        </td>
      </tr>
    `;
  }).join('');
}

async function openBorrowModal() {
  document.getElementById('borrowForm').reset();

  // Load readers list into dropdown
  const resReaders = await fetch(`${API_BASE}/api/readers`);
  const jsonReaders = await resReaders.json();
  const readerSelect = document.getElementById('borrow-reader-select');
  if (jsonReaders.success) {
    readerSelect.innerHTML = '<option value="">-- Chọn độc giả mượn sách --</option>' +
      jsonReaders.data.map(r => `<option value="${r.id}">${r.full_name} (${r.card_number} - ${r.reader_type})</option>`).join('');
  }

  // Load available books into checklist
  const resBooks = await fetch(`${API_BASE}/api/books`);
  const jsonBooks = await resBooks.json();
  const bookChecklist = document.getElementById('borrow-books-checklist');
  if (jsonBooks.success) {
    const availableBooks = jsonBooks.data.filter(b => b.available_copies > 0);
    if (availableBooks.length === 0) {
      bookChecklist.innerHTML = '<div class="text-danger small p-2">Hiện tại không còn sách nào khả dụng trong kho!</div>';
    } else {
      bookChecklist.innerHTML = availableBooks.map(b => `
        <div class="form-check py-1 border-bottom">
          <input class="form-check-input borrow-book-chk" type="checkbox" value="${b.id}" id="chk-book-${b.id}">
          <label class="form-check-label small" for="chk-book-${b.id}">
            <strong>${b.title}</strong> - <em>${b.author}</em> 
            <span class="badge bg-success bg-opacity-10 text-success ms-1">Còn ${b.available_copies} cuốn</span>
            <span class="text-muted ms-1">(${b.location})</span>
          </label>
        </div>
      `).join('');
    }
  }

  const modal = new bootstrap.Modal(document.getElementById('borrowModal'));
  modal.show();
}

async function handleCreateBorrow(e) {
  e.preventDefault();
  const readerId = parseInt(document.getElementById('borrow-reader-select').value);
  const dueDays = parseInt(document.getElementById('borrow-due-days').value);
  const notes = document.getElementById('borrow-notes').value;

  const selectedBooks = [];
  document.querySelectorAll('.borrow-book-chk:checked').forEach(chk => {
    selectedBooks.push(parseInt(chk.value));
  });

  if (selectedBooks.length === 0) {
    Swal.fire({ icon: 'warning', title: 'Chưa chọn sách', text: 'Vui lòng tích chọn ít nhất 1 cuốn sách để mượn!' });
    return;
  }

  if (selectedBooks.length > 5) {
    Swal.fire({ icon: 'error', title: 'Vượt giới hạn', text: 'Mỗi lần chỉ được mượn tối đa 5 cuốn sách!' });
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/borrows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reader_id: readerId, book_ids: selectedBooks, due_days: dueDays, notes })
    });
    const json = await res.json();
    if (json.success) {
      bootstrap.Modal.getInstance(document.getElementById('borrowModal')).hide();
      Swal.fire({ icon: 'success', title: 'Lập phiếu thành công!', text: `Mã phiếu: ${json.record_code}`, timer: 1800, showConfirmButton: false });
      loadBorrows();
      loadDashboard();
      loadBooks();
    } else {
      Swal.fire({ icon: 'error', title: 'Không thể mượn sách', text: json.error });
    }
  } catch (err) {
    Swal.fire({ icon: 'error', title: 'Lỗi', text: err.message });
  }
}

async function handleReturnBook(recordId, recordCode) {
  const result = await Swal.fire({
    title: 'Xác nhận trả sách?',
    text: `Thực hiện nhận lại sách cho phiếu mượn ${recordCode}?`,
    icon: 'question',
    showCancelButton: true,
    confirmButtonColor: '#16a34a',
    cancelButtonText: 'Hủy',
    confirmButtonText: 'Xác nhận trả'
  });

  if (result.isConfirmed) {
    try {
      const res = await fetch(`${API_BASE}/api/borrows/${recordId}/return`, { method: 'POST' });
      const json = await res.json();
      if (json.success) {
        let text = json.message;
        if (json.fine_amount > 0) {
          text += `\n⚠️ Lưu ý: Thu phí phạt trễ hạn ${Number(json.fine_amount).toLocaleString('vi-VN')} VNĐ`;
        }
        Swal.fire({ icon: 'success', title: 'Trả sách thành công!', text: text });
        loadBorrows();
        loadDashboard();
        loadBooks();
      } else {
        Swal.fire({ icon: 'error', title: 'Lỗi', text: json.error });
      }
    } catch (err) {
      Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: err.message });
    }
  }
}

async function handleRenewBook(recordId, recordCode) {
  try {
    const res = await fetch(`${API_BASE}/api/borrows/${recordId}/renew`, { method: 'POST' });
    const json = await res.json();
    if (json.success) {
      Swal.fire({ icon: 'success', title: 'Gia hạn thành công!', text: json.message, timer: 1500, showConfirmButton: false });
      loadBorrows();
      loadDashboard();
    } else {
      Swal.fire({ icon: 'error', title: 'Không thể gia hạn', text: json.error });
    }
  } catch (err) {
    Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: err.message });
  }
}

// ==========================================
// 7. AI ASSISTANT CHATBOT (Google AI Studio)
// ==========================================
async function handleSendAIMessage(e) {
  e.preventDefault();
  const input = document.getElementById('ai-message-input');
  const msg = input.value.trim();
  if (!msg) return;

  appendChatMessage('user', msg);
  input.value = '';

  const sendBtn = document.getElementById('ai-send-btn');
  sendBtn.disabled = true;
  sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

  // AI Loading bubble
  const loadingBubble = appendChatMessage('ai', '<div class="spinner-grow spinner-grow-sm text-primary"></div> Trợ lý AI đang suy nghĩ...');

  try {
    const res = await fetch(`${API_BASE}/api/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    const json = await res.json();
    loadingBubble.remove();

    if (json.success && json.data) {
      appendChatMessage('ai', json.data.message, json.data.source);
    } else {
      appendChatMessage('ai', 'Xin lỗi, hiện tại tôi chưa thể xử lý yêu cầu này. Vui lòng thử lại sau!');
    }
  } catch (err) {
    loadingBubble.remove();
    appendChatMessage('ai', 'Lỗi kết nối tới AI Service: ' + err.message);
  } finally {
    sendBtn.disabled = false;
    sendBtn.innerHTML = '<i class="bi bi-send-fill me-1"></i> Gửi';
  }
}

function appendChatMessage(sender, content, source) {
  const container = document.getElementById('chat-messages-box');
  const div = document.createElement('div');
  div.className = `chat-bubble ${sender}`;

  let html = '';
  if (sender === 'ai' && source) {
    html += `<div class="source-tag"><i class="bi bi-stars"></i> ${source}</div>`;
  }

  // Parse markdown for AI responses if marked is loaded
  if (sender === 'ai' && typeof marked !== 'undefined' && !content.includes('spinner')) {
    html += marked.parse(content);
  } else {
    html += content.replace(/\n/g, '<br>');
  }

  div.innerHTML = html;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function sendQuickPrompt(promptText) {
  document.getElementById('ai-message-input').value = promptText;
  document.getElementById('ai-chat-form').dispatchEvent(new Event('submit'));
}

function clearAIChat() {
  const container = document.getElementById('chat-messages-box');
  container.innerHTML = `
    <div class="chat-bubble ai">
      <div class="source-tag"><i class="bi bi-stars"></i> Smart Library AI</div>
      Đoạn hội thoại đã được làm mới! Bạn cần mình hỗ trợ tìm kiếm tài liệu hay giải đáp điều gì?
    </div>
  `;
}

// ==========================================
// 8. SETTINGS & GEMINI API KEY
// ==========================================
async function saveApiKey() {
  const key = document.getElementById('gemini-api-key-input').value.trim();
  localStorage.setItem('gemini_api_key', key);

  try {
    const res = await fetch(`${API_BASE}/api/ai/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key })
    });
    const json = await res.json();
    if (json.success) {
      Swal.fire({ icon: 'success', title: 'Thành công', text: 'Đã lưu cấu hình Google AI Studio API Key!' });
    }
  } catch (err) {
    Swal.fire({ icon: 'info', title: 'Đã lưu cục bộ', text: 'API Key đã được lưu trên trình duyệt!' });
  }
}

async function testApiKey() {
  const key = document.getElementById('gemini-api-key-input').value.trim();
  if (!key) {
    Swal.fire({ icon: 'warning', title: 'Chưa nhập key', text: 'Vui lòng nhập Google AI Studio API Key trước khi kiểm tra!' });
    return;
  }

  Swal.fire({
    title: 'Đang kiểm tra kết nối...',
    text: 'Gửi gói tin thử nghiệm tới Google AI Studio...',
    allowOutsideClick: false,
    didOpen: () => { Swal.showLoading(); }
  });

  try {
    const res = await fetch(`${API_BASE}/api/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'Xin chào, đây là kiểm tra kết nối Gemini API từ Antigravity IDE.' })
    });
    const json = await res.json();
    Swal.close();
    if (json.success) {
      Swal.fire({ icon: 'success', title: 'Kết nối thành công!', text: `Nguồn phản hồi: ${json.data.source}` });
    }
  } catch (err) {
    Swal.close();
    Swal.fire({ icon: 'error', title: 'Kết nối thất bại', text: err.message });
  }
}

async function confirmResetDatabase() {
  const res = await Swal.fire({
    title: 'Khôi phục dữ liệu mẫu?',
    text: 'Thao tác này sẽ nạp lại toàn bộ sách, độc giả và lịch sử mượn mẫu.',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#dc2626',
    cancelButtonText: 'Hủy',
    confirmButtonText: 'Đồng ý nạp lại'
  });

  if (res.isConfirmed) {
    location.reload();
  }
}

// Utility Helpers
function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('vi-VN');
  } catch {
    return dateStr;
  }
}

function escapeQuote(str) {
  return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
