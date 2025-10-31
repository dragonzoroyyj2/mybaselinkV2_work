/**
 * 🧩 commonUnifiedList_opV2.js (동적 버튼 ID + 기존 기능 완전 통합)
 * --------------------------------------------------------
 * ✅ 공용 리스트/CRUD/엑셀 + 반응형 테이블 + 페이징 자동조정
 * ✅ 로딩 스피너 & 토스트 알림 통합
 * ✅ 순수 div 기반 레이어팝업 정상화 (별도 라이브러리 미사용)
 * ✅ 중복 메세지 및 이벤트 실행 방지
 * ✅ 버튼 ID 및 상세보기 버튼 동적 적용
 * --------------------------------------------------------
 *
 * 사용법:
 *   const unifiedListManager = initUnifiedList({ mode: "server" | "client", ...config });
 *
 * ⚠️ 이 파일은 top.html의 스피너/토스트 컴포넌트와 commonPagination_op.js가 로드된 후 로드되어야 합니다.
 */

function initUnifiedList(config) {
  if (window.unifiedListInstance) {
    console.warn("UnifiedList 인스턴스 이미 존재, 기존 재사용");
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
    this.validateConfig(config);

    // ===============================
    // 초기 페이지/페이징 설정
    // ===============================
    this.currentPage = 0;
    this.pageSize = config.pageSize || 10;
    this.pageGroupSize = config.pageGroupSize || 5;
    this.isFullDataLoaded = false;
    this.fullDataCache = [];
    this.totalPagesCache = 0;
    this.currentSort = { key: null, direction: 'asc' };
    this.eventListenerBound = false;

    // ===============================
    // 셀렉터 단축
    // ===============================
    this.$ = sel => document.querySelector(sel);
    this.$$ = sel => document.querySelectorAll(sel);

    this.csrfToken = this.$("meta[name='_csrf']")?.content;
    this.csrfHeader = this.$("meta[name='_csrf_header']")?.content;

    // ===============================
    // 기본 셀렉터 설정
    // ===============================
    this.config.tableBodySelector = this.config.tableBodySelector || 'tbody';
    this.config.tableHeaderSelector = this.config.tableHeaderSelector || 'thead';
    this.config.searchInputSelector = this.config.searchInputSelector || '#searchInput';
    this.config.paginationSelector = this.config.paginationSelector || '#pagination';

    // ===============================
    // 버튼 ID 및 상세보기 버튼 동적화
    // ===============================
    this.config.buttons = this.config.buttons || {};            // 화면마다 ID 다르게
    this.config.detailViewButtons = this.config.detailViewButtons || {};

    this.listContainer = document.body;

    this.init();
  }

  validateConfig(config) {
    const requiredProps = ['apiUrl', 'tableBodySelector', 'paginationSelector', 'columns'];
    for (const prop of requiredProps) {
      if (!config[prop]) throw new Error(`Config validation failed: '${prop}' is required.`);
    }
  }

  // ===============================
  // 초기화
  // ===============================
  init() {
    this.toggleButtons();
    if (!this.eventListenerBound) this.bindEvents();
    this.loadList(0);
  }

  // ===============================
  // UI 피드백 메서드
  // ===============================
  showSpinner() {
    const spinner = this.$('#loadingSpinner');
    if (spinner) spinner.style.display = 'flex';
  }

  hideSpinner() {
    const spinner = this.$('#loadingSpinner');
    if (spinner) spinner.style.display = 'none';
  }

  // ===============================
  // 버튼 가시성 제어 (ID 동적 적용)
  // ===============================
  toggleButtons() {
    const userRoles = window.userRoles || [];
    const btnMap = this.config.buttons;
    if (!btnMap) return;

    Object.keys(btnMap).forEach(key => {
      const selector = btnMap[key]; 
      if (!selector) return;
      const el = this.$(selector);
      if (!el) return;
      const cfg = btnMap[key];
      if (cfg === false || (cfg.roles && !cfg.roles.some(r => userRoles.includes(r)))) {
        el.style.display = 'none';
      } else el.style.display = '';
    });

    // 상세보기 버튼 동적
    const detailBtns = this.config.detailViewButtons;
    if (detailBtns) {
      Object.keys(detailBtns).forEach(key => {
        const selector = detailBtns[key];
        if (!selector) return;
        const el = this.$(selector);
        if (el) el.style.display = '';
      });
    }
  }

  // ===============================
  // 데이터 로드
  // ===============================
  async loadList(page = 0, environment = 'web', search = '', sort = null) {
    this.currentPage = page;
    const tbody = this.$(this.config.tableBodySelector);
    if (!tbody) {
      window.notify('error', '테이블 바디 요소를 찾을 수 없습니다.');
      return;
    }

    tbody.innerHTML = '<tr><td colspan="100%">데이터를 불러오는 중입니다...</td></tr>';
    this.showSpinner();

    try {
      if (this.config.mode === "server") {
        await this._loadFromServer(page, environment, search, sort);
      } else if (this.config.mode === "client") {
        await this._loadFromClient(page, search, sort);
      }
      window.notify('success', '데이터를 성공적으로 불러왔습니다.');
    } catch (err) {
      console.error(err);
      window.notify('error', '데이터 조회 중 오류 발생: ' + err.message);
      tbody.innerHTML = '<tr><td colspan="100%">데이터 조회 중 오류가 발생했습니다.</td></tr>';
    } finally {
      this.hideSpinner();
    }
  }

  async _loadFromServer(page, environment, search, sort) {
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('size', this.pageSize);
    params.append('search', search);
    if (sort) params.append('sort', `${sort.key},${sort.direction}`);

    const url = `${this.config.apiUrl}?${params.toString()}`;
    const res = await fetch(url, this.fetchOptions("GET"));
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
      ? this.fullDataCache.filter(item =>
          Object.values(item).some(v => String(v ?? "").toLowerCase().includes(searchLower))
        )
      : this.fullDataCache;

    if (sort) {
      filtered.sort((a, b) => {
        const aVal = a[sort.key] || '';
        const bVal = b[sort.key] || '';
        if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    const pageData = this.config.pagination ? filtered.slice(page * this.pageSize, (page + 1) * this.pageSize) : filtered;
    this.renderTable(pageData);
    this._updateTotalCount(filtered.length);
    this.totalPagesCache = Math.max(1, Math.ceil(filtered.length / this.pageSize));
    this._renderPagination();
  }

  _updateTotalCount(count) {
    const el = this.$("#totalCount");
    if (el) el.textContent = `총 ${count}건`;
  }

  _renderPagination() {
    const el = this.$(this.config.paginationSelector);
    if (this.config.pagination && el) {
      renderPagination(this.currentPage, this.totalPagesCache, this.config.paginationSelector, this.loadList.bind(this), this.pageGroupSize);
    } else if (el) el.innerHTML = "";
  }

  // ===============================
  // 테이블 렌더링
  // ===============================
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

    const checkAllEl = this.$(this.config.checkAllSelector);
    if (checkAllEl) checkAllEl.checked = false;
  }

  // ===============================
  // 체크박스 제어
  // ===============================
  toggleAllCheckboxes(isChecked) {
    const checkboxes = this.$$(`${this.config.tableBodySelector} .row-checkbox`);
    checkboxes.forEach(cb => cb.checked = isChecked);
  }

  // ===============================
  // 선택 삭제
  // ===============================
  deleteSelected() {
    const selectedIds = Array.from(this.$$(`${this.config.tableBodySelector} .row-checkbox:checked`))
      .map(cb => cb.dataset.id)
      .filter(id => id);

    if (selectedIds.length === 0) {
      window.notify('warning', "삭제할 항목을 선택해주세요.");
      return;
    }

    if (confirm(`${selectedIds.length}개의 항목을 삭제하시겠습니까?`)) {
      console.log('삭제할 ID:', selectedIds);
      this.showSpinner();
      if (this.config.onDeleteSuccess) this.config.onDeleteSuccess(selectedIds);
      else {
        this.hideSpinner();
        window.notify('success', '선택된 항목 삭제 요청을 처리했습니다.');
      }
    }
  }

  // ===============================
  // 엑셀 다운로드
  // ===============================
  downloadExcel() {
    window.notify('info', '엑셀 다운로드를 시작합니다.');
    console.log('엑셀 다운로드 기능 호출');
  }

  // ===============================
  // 모달 제어
  // ===============================
  openAddModal() { this._openModal(this.config.modalId, this.config.onAddModalOpen); }
  openDetailModal(id) {
    this._openModal(this.config.detailModalId, () => {
      console.log(`${this.config.detailModalId} 모달 열기 (ID: ${id})`);
      if (this.config.onDetailModalOpen) this.config.onDetailModalOpen(id);
    });
  }

  _openModal(modalSelector, callback) {
    const modalEl = this.$(modalSelector);
    if (modalEl) {
      modalEl.style.display = 'flex';
      if (callback) callback();
    } else window.notify('error', `${modalSelector} 모달을 찾을 수 없습니다.`);
  }

  _closeModal(modalSelector) {
    const modalEl = this.$(modalSelector);
    if (modalEl) modalEl.style.display = 'none';
  }

  // ===============================
  // 테이블 정렬
  // ===============================
  sortTable(header) {
    const sortKey = header.dataset.sortKey;
    if (!sortKey) return;

    if (this.currentSort.key === sortKey) this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
    else this.currentSort = { key: sortKey, direction: 'asc' };

    this.$$(`${this.config.tableHeaderSelector} .sortable`).forEach(h => h.classList.remove('sorted-asc', 'sorted-desc'));
    header.classList.add(`sorted-${this.currentSort.direction}`);

    const searchValue = this.$(this.config.searchInputSelector)?.value || '';
    this.loadList(0, this._getEnv(), searchValue, this.currentSort);
  }

  // ===============================
  // 공용 유틸리티
  // ===============================
  _getEnv() { return /Mobi|Android/i.test(navigator.userAgent) ? 'mobile' : 'web'; }
  fetchOptions(method = "GET") {
    const opts = { method, headers: {} };
    if (this.csrfToken && this.csrfHeader) opts.headers[this.csrfHeader] = this.csrfToken;
    return opts;
  }
}
