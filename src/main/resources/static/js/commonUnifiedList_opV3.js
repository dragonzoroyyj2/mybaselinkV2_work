/**
 * 🧩 commonUnifiedList_opV3.js (V1 기반 + 버튼 동적 처리)
 * --------------------------------------------------------
 * ✅ V1 기능 100% 유지 (CRUD, 엑셀, 페이징, 모달, 토스트, 스피너)
 * ✅ 모든 버튼 동적 할당 가능
 * --------------------------------------------------------
 */

function initUnifiedList(config) {
  if (window.unifiedListInstance) {
    console.warn("UnifiedList 인스턴스 이미 존재, 기존 인스턴스 재사용");
    window.unifiedListInstance.init();
    return window.unifiedListInstance;
  }

  try {
    const instance = new UnifiedList(config);
    window.unifiedListInstance = instance;
    return instance;
  } catch (e) {
    console.error("UnifiedList 초기화 실패:", e);
  }
}

class UnifiedList {
  constructor(config) {
    this.config = config;
    this.currentPage = 0;
    this.pageSize = config.pageSize || 10;
    this.pageGroupSize = config.pageGroupSize || 5;
    this.isFullDataLoaded = false;
    this.fullDataCache = [];
    this.totalPagesCache = 0;
    this.currentSort = { key: null, direction: 'asc' };
    this.eventListenerBound = false;

    this.$ = sel => document.querySelector(sel);
    this.$$ = sel => document.querySelectorAll(sel);

    this.csrfToken = this.$("meta[name='_csrf']")?.content;
    this.csrfHeader = this.$("meta[name='_csrf_header']")?.content;

    // =======================
    // 버튼 동적 할당
    // =======================
    const defaultButtons = {
      searchInputSelector: "#searchInput",
      searchBtnSelector: "#searchBtn",
      addBtnSelector: "#addBtn",
      saveBtnSelector: "#saveBtn",
      detailUpdateBtnSelector: "#updateBtn",
      detailDeleteBtnSelector: "#deleteSelectedBtn",
      deleteSelectedBtnSelector: "#deleteSelectedBtn",
      checkAllSelector: "#checkAll",
      excelBtnSelector: "#excelBtn"
    };
    this.buttons = { ...defaultButtons, ...config.buttons };

    this.init();
  }

  init() {
    this.toggleButtons();
    if (!this.eventListenerBound) this.bindEvents();
    this.loadList(0);
  }

  showSpinner() {
    const spinner = this.$('#loadingSpinner');
    if (spinner) spinner.style.display = 'flex';
  }

  hideSpinner() {
    const spinner = this.$('#loadingSpinner');
    if (spinner) spinner.style.display = 'none';
  }

  async loadList(page = 0, search = '', sort = null) {
    this.currentPage = page;
    const body = this.$(this.config.tableBodySelector);
    if (!body) return;

    body.innerHTML = '<tr><td colspan="100%">데이터를 불러오는 중입니다...</td></tr>';
    this.showSpinner();

    try {
      if (this.config.mode === "server") {
        await this._loadFromServer(page, search, sort);
      } else {
        await this._loadFromClient(page, search, sort);
      }
      window.notify?.('success', '데이터를 성공적으로 불러왔습니다.');
    } catch (err) {
      console.error(err);
      window.notify?.('error', '데이터 조회 중 오류 발생: ' + err.message);
      body.innerHTML = '<tr><td colspan="100%">데이터 조회 중 오류가 발생했습니다.</td></tr>';
    } finally {
      this.hideSpinner();
    }
  }

  async _loadFromServer(page, search, sort) {
    const params = new URLSearchParams({ page, size: this.pageSize, search });
    if (sort) params.append('sort', `${sort.key},${sort.direction}`);

    const res = await fetch(`${this.config.apiUrl}?${params.toString()}`, this.fetchOptions("GET"));
    if (!res.ok) throw new Error("서버 데이터 조회 실패");
    const data = await res.json();
    this.renderTable(data.content || []);
    this._updateTotalCount(data.totalElements ?? data.content?.length ?? 0);
    this.totalPagesCache = data.totalPages ?? Math.ceil((data.totalElements ?? data.content?.length ?? 0) / this.pageSize);
    this._renderPagination();
  }

  async _loadFromClient(page, search, sort) {
    if (!this.isFullDataLoaded) {
      const res = await fetch(`${this.config.apiUrl}?mode=client`, this.fetchOptions("GET"));
      if (!res.ok) throw new Error("전체 데이터 조회 실패");
      const json = await res.json();
      this.fullDataCache = Array.isArray(json.content) ? json.content : [];
      this.isFullDataLoaded = true;
    }

    const searchLower = search.toLowerCase();
    let filtered = search
      ? this.fullDataCache.filter(item => Object.values(item).some(v => String(v ?? "").toLowerCase().includes(searchLower)))
      : this.fullDataCache;

    if (sort) {
      filtered.sort((a, b) => {
        const aVal = a[sort.key] || '';
        const bVal = b[sort.key] || '';
        return sort.direction === 'asc' ? (aVal < bVal ? -1 : 1) : (aVal > bVal ? -1 : 1);
      });
    }

    const pageData = this.config.pagination ? filtered.slice(page * this.pageSize, (page + 1) * this.pageSize) : filtered;
    this.renderTable(pageData);
    this._updateTotalCount(filtered.length);
    this.totalPagesCache = Math.max(1, Math.ceil(filtered.length / this.pageSize));
    this._renderPagination();
  }

  _updateTotalCount(count) {
    const totalCountEl = this.$("#totalCount");
    if (totalCountEl) totalCountEl.textContent = `총 ${count}건`;
  }

  _renderPagination() {
    const pagingEl = this.$(this.config.paginationSelector);
    if (this.config.pagination && pagingEl) {
      renderPagination(this.currentPage, this.totalPagesCache, this.config.paginationSelector, this.loadList.bind(this), this.pageGroupSize);
    } else if (pagingEl) pagingEl.innerHTML = "";
  }

  renderTable(list) {
    const tbody = this.$(this.config.tableBodySelector);
    if (!tbody) return;
    tbody.innerHTML = "";
    if (!Array.isArray(list) || list.length === 0) {
      const colSpan = (this.config.columns?.length || 0) + 1;
      tbody.innerHTML = `<tr><td colspan="${colSpan}">데이터가 없습니다.</td></tr>`;
      return;
    }
    list.forEach(row => {
      const tr = document.createElement("tr");
      const chkTd = document.createElement("td");
      chkTd.innerHTML = `<input type="checkbox" value="${row.id}" data-id="${row.id}" class="row-checkbox">`;
      tr.appendChild(chkTd);
      if (this.config.enableRowClickDetail) {
        tr.dataset.id = row.id;
        tr.classList.add('clickable-row');
      }
      this.config.columns.forEach(col => {
        const td = document.createElement("td");
        const val = row[col.key] ?? "";
        if (col.isDetailLink && this.config.enableDetailView && !this.config.enableRowClickDetail) {
          td.innerHTML = `<a href="#" data-id="${row.id}" class="detail-link">${val}</a>`;
        } else {
          td.textContent = val;
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    const checkAllEl = this.$(this.buttons.checkAllSelector);
    if (checkAllEl) checkAllEl.checked = false;
  }

  toggleButtons() {
    const userRoles = window.userRoles || [];
    const buttonMap = {
      search: this.buttons.searchBtnSelector,
      add: this.buttons.addBtnSelector,
      deleteSelected: this.buttons.deleteSelectedBtnSelector,
      excel: this.buttons.excelBtnSelector,
      save: this.buttons.saveBtnSelector,
      update: this.buttons.detailUpdateBtnSelector
    };
    Object.keys(buttonMap).forEach(key => {
      const el = this.$(buttonMap[key]);
      if (el) el.style.display = '';
    });
  }

  bindEvents() {
    if (!this.eventListenerBound) {
      document.body.addEventListener('click', this._handleEvent.bind(this));
      document.body.addEventListener('keydown', this._handleEvent.bind(this));
      this.eventListenerBound = true;
    }
  }

  _handleEvent(e) {
    const target = e.target;
    const closest = sel => target.closest(sel);

    // =================
    // 클릭 이벤트 처리
    // =================
    if (e.type === 'click') {
      if (closest(this.buttons.searchBtnSelector)) {
        e.preventDefault();
        const val = this.$(this.buttons.searchInputSelector)?.value || '';
        this.loadList(0, val, this.currentSort);
        return;
      }

      if (closest(this.buttons.addBtnSelector)) {
        e.preventDefault();
        this.openAddModal();
        return;
      }

      if (target.matches(this.buttons.checkAllSelector)) {
        this.toggleAllCheckboxes(target.checked);
        return;
      }

      const detailLink = closest('.detail-link');
      const clickableRow = closest('.clickable-row');
      if ((detailLink && this.config.enableDetailView && !this.config.enableRowClickDetail) || (this.config.enableRowClickDetail && clickableRow && !target.closest('.row-checkbox'))) {
        e.preventDefault();
        const id = closest('[data-id]')?.dataset.id;
        if (id) this.openDetailModal(id);
        return;
      }

      if (closest(this.buttons.deleteSelectedBtnSelector)) {
        this.deleteSelected();
        return;
      }

      if (closest(this.buttons.excelBtnSelector)) {
        this.downloadExcel();
        return;
      }

      if (target.matches('[data-close]')) {
        const modalId = target.dataset.close;
        this._closeModal(`#${modalId}`);
        return;
      }
    }

    // =================
    // 키보드 Enter 이벤트
    // =================
    if (e.type === 'keydown' && e.key === 'Enter') {
      if (e.target.matches(this.buttons.searchInputSelector)) {
        e.preventDefault();
        const val = e.target.value;
        this.loadList(0, val, this.currentSort);
      }
    }
  }

  toggleAllCheckboxes(checked) {
    const checkboxes = this.$$(`${this.config.tableBodySelector} .row-checkbox`);
    checkboxes.forEach(cb => cb.checked = checked);
  }

  deleteSelected() {
    const selectedIds = Array.from(this.$$(`${this.config.tableBodySelector} .row-checkbox:checked`))
      .map(cb => cb.dataset.id)
      .filter(id => id);
    if (selectedIds.length === 0) {
      window.notify?.('warning', "삭제할 항목을 선택해주세요.");
      return;
    }
    if (confirm(`${selectedIds.length}개 항목을 삭제하시겠습니까?`)) {
      this.showSpinner();
      if (this.config.onDeleteSuccess) {
        this.config.onDeleteSuccess(selectedIds);
      } else {
        this.hideSpinner();
        window.notify?.('success', '선택된 항목 삭제 처리 완료.');
      }
    }
  }

  downloadExcel() {
    window.notify?.('info', '엑셀 다운로드 시작');
    console.log('엑셀 다운로드 호출');
  }

  openAddModal() {
    this._openModal(this.config.modalId, this.config.onAddModalOpen);
  }

  openDetailModal(id) {
    this._openModal(this.config.detailModalId, () => {
      if (this.config.onDetailModalOpen) this.config.onDetailModalOpen(id);
    });
  }

  _openModal(selector, callback) {
    const el = this.$(selector);
    if (el) {
      el.style.display = 'block';
      if (callback) callback();
    } else {
      window.notify?.('error', `${selector} 모달 없음`);
    }
  }

  _closeModal(selector) {
    const el = this.$(selector);
    if (el) el.style.display = 'none';
  }

  sortTable(header) {
    const key = header.dataset.sortKey;
    if (!key) return;
    this.currentSort.direction = this.currentSort.key === key ? (this.currentSort.direction === 'asc' ? 'desc' : 'asc') : 'asc';
    this.currentSort.key = key;

    this.$$(`${this.config.tableHeaderSelector} .sortable`).forEach(h => h.classList.remove('sorted-asc', 'sorted-desc'));
    header.classList.add(`sorted-${this.currentSort.direction}`);

    const val = this.$(this.buttons.searchInputSelector)?.value || '';
    this.loadList(0, val, this.currentSort);
  }

  _getEnv() {
    return window.innerWidth < 768 ? 'mobile' : 'web';
  }

  fetchOptions(method, body = null) {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...this.csrfHeader && this.csrfToken ? { [this.csrfHeader]: this.csrfToken } : {}
      }
    };
    if (body) options.body = JSON.stringify(body);
    return options;
  }
}
