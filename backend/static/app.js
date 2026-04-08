document.addEventListener('DOMContentLoaded', () => {
    // Translations
    const translations = {
        zh: {
            nav_updates: '动态追踪',
            nav_trends: '趋势分析',
            nav_reports: '每周简报',
            nav_health: '数据源状态',
            status_online: '系统在线',
            search_placeholder: '搜索动态、标签、产品...',
            btn_scan: '采集数据',
            feed_title: '竞品情报追踪',
            feed_subtitle: '实时监控市场领导者的最新动态。',
            filter_date: '日期范围',
            date_all: '全部时间',
            date_1: '最近 24 小时',
            date_7: '近 7 天',
            date_30: '近 30 天',
            date_90: '近 90 天',
            date_custom: '自定义范围',
            filter_product: '产品名称',
            product_all: '所有产品',
            product_sensors: '神策数据',
            filter_type: '情报类型',
            type_all: '所有类型',
            type_feature: '功能发布',
            type_blog: '博客文章',
            type_github: 'GitHub 动态',
            loading_insights: '正在加载最新洞察...',
            trends_coming_soon: '趋势分析即将上线',
            trends_desc: '识别竞品格局中的模式和热点区域。',
            reports_coming_soon: '每周简报即将上线',
            reports_desc: '自动化总结和竞品情报报告。',
            health_coming_soon: '数据源状态即将上线',
            health_desc: '监控竞品数据源的状态和可靠性。',
            btn_view_source: '查看原始出处',
            conn_error: '连接错误',
            conn_error_desc: '加载更新失败，请检查后端连接。',
            retry: '重试',
            no_insights: '未发现洞察',
            no_insights_desc: '尝试调整过滤器或搜索关键词。',
            scanning: '正在采集...',
            starting_task: '正在启动采集任务...',
            completed_in: '采集完成，耗时 ',
            seconds: ' 秒',
            collect_settings_title: '采集任务配置',
            btn_start_scan: '开始采集任务',
            btn_batch_delete: '批量删除',
            btn_cancel: '取消',
            btn_confirm: '确认删除',
            confirm_delete_title: '确认删除？',
            confirm_delete_msg: '此操作无法撤销，确定要删除选中的记录吗？',
            confirm_single_delete_msg: '确定要删除这条记录吗？',
            delete_success: '删除成功',
            delete_error: '删除失败'
        },
        en: {
            nav_updates: 'Updates Feed',
            nav_trends: 'Trends Analysis',
            nav_reports: 'Weekly Reports',
            nav_health: 'Source Health',
            status_online: 'System Online',
            search_placeholder: 'Search updates, tags, products...',
            btn_scan: 'Scan Sources',
            feed_title: 'Product Intelligence Feed',
            feed_subtitle: 'Tracking the latest moves from market leaders.',
            filter_date: 'Date Range',
            date_all: 'All Time',
            date_1: 'Last 24 Hours',
            date_7: 'Last 7 Days',
            date_30: 'Last 30 Days',
            date_90: 'Last 90 Days',
            date_custom: 'Custom Range',
            filter_product: 'Product',
            product_all: 'All Products',
            product_sensors: 'SensorsData',
            filter_type: 'Type',
            type_all: 'All Types',
            type_feature: 'Features',
            type_blog: 'Blog Posts',
            type_github: 'GitHub',
            loading_insights: 'Loading latest insights...',
            trends_coming_soon: 'Trends Analysis Coming Soon',
            trends_desc: 'Identify patterns and hotspots across competitive landscape.',
            reports_coming_soon: 'Weekly Reports Coming Soon',
            reports_desc: 'Automated summaries and competitive intelligence reports.',
            health_coming_soon: 'Source Health Coming Soon',
            health_desc: 'Monitor status and reliability of competitive data sources.',
            btn_view_source: 'View Original Source',
            conn_error: 'Connection Error',
            conn_error_desc: 'Failed to load updates. Please check backend connection.',
            retry: 'Retry',
            no_insights: 'No Insights Found',
            no_insights_desc: 'Try adjusting your filters or search keywords.',
            scanning: 'Scanning...',
            starting_task: 'Starting collection task...',
            completed_in: 'Completed in ',
            seconds: 's',
            collect_settings_title: 'Collection Task Settings',
            btn_start_scan: 'Start Collection Task',
            btn_batch_delete: 'Delete Selected',
            btn_cancel: 'Cancel',
            btn_confirm: 'Confirm Delete',
            confirm_delete_title: 'Confirm Delete?',
            confirm_delete_msg: 'This action cannot be undone. Are you sure you want to delete selected records?',
            confirm_single_delete_msg: 'Are you sure you want to delete this record?',
            delete_success: 'Deleted successfully',
            delete_error: 'Failed to delete'
        }
    };

    // State management
    const state = {
        currentView: 'updates',
        updates: [],
        selectedIds: new Set(),
        theme: localStorage.getItem('theme') || 'light',
        lang: localStorage.getItem('lang') || 'zh',
        filters: {
            product: '',
            type: '',
            dateRange: '30',
            startDate: '',
            endDate: '',
            search: ''
        }
    };

    // DOM Elements
    const elements = {
        navItems: document.querySelectorAll('.nav-item'),
        views: document.querySelectorAll('.view'),
        updatesFeed: document.getElementById('updates-feed'),
        refreshBtn: document.getElementById('refresh-btn'),
        themeToggle: document.getElementById('theme-toggle'),
        themeIcon: document.getElementById('theme-icon'),
        langToggle: document.getElementById('lang-toggle'),
        langText: document.getElementById('lang-text'),
        productFilter: document.getElementById('product-filter'),
        typeFilter: document.getElementById('type-filter'),
        dateRangeFilter: document.getElementById('date-range-filter'),
        customDateRange: document.getElementById('custom-date-range'),
        startDateInput: document.getElementById('start-date'),
        endDateInput: document.getElementById('end-date'),
        globalSearch: document.getElementById('global-search'),
        modal: document.getElementById('modal'),
        modalBody: document.getElementById('modal-body'),
        modalSourceLink: document.getElementById('modal-source-link'),
        modalBadgeContainer: document.getElementById('modal-badge-container'),
        closeModalBtn: document.querySelector('.close-btn'),
        modalBackdrop: document.querySelector('.modal-backdrop'),
        
        collectModal: document.getElementById('collect-modal'),
        closeCollectModalBtn: document.getElementById('close-collect-modal'),
        startCollectBtn: document.getElementById('start-collect-btn'),
        collectDays: document.getElementById('collect-days'),
        platformChecks: document.querySelectorAll('.platform-check'),

        batchDeleteBtn: document.getElementById('batch-delete-btn'),
        confirmModal: document.getElementById('confirm-modal'),
        confirmTitle: document.getElementById('confirm-title'),
        confirmMessage: document.getElementById('confirm-message'),
        confirmOkBtn: document.getElementById('confirm-ok-btn'),
        confirmCancelBtn: document.getElementById('confirm-cancel-btn')
    };

    // Initialize Lucide Icons
    const refreshIcons = () => {
        if (window.lucide) {
            window.lucide.createIcons();
        }
    };

    // Initialize Theme
    const initTheme = () => {
        document.documentElement.setAttribute('data-theme', state.theme);
        updateThemeIcon();
    };

    const updateThemeIcon = () => {
        if (state.theme === 'dark') {
            elements.themeIcon.setAttribute('data-lucide', 'moon');
        } else {
            elements.themeIcon.setAttribute('data-lucide', 'sun');
        }
        refreshIcons();
    };

    const toggleTheme = () => {
        state.theme = state.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', state.theme);
        document.documentElement.setAttribute('data-theme', state.theme);
        updateThemeIcon();
    };

    // Initialize Language
    const initLang = () => {
        updateLanguage();
    };

    const updateLanguage = () => {
        const t = translations[state.lang];
        
        // Update all elements with data-i18n
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (t[key]) el.textContent = t[key];
        });

        // Update placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (t[key]) el.placeholder = t[key];
        });

        // Update toggle text
        elements.langText.textContent = state.lang === 'zh' ? 'EN' : '中';
        
        // Update HTML lang attribute
        document.documentElement.lang = state.lang;
    };

    const toggleLang = () => {
        state.lang = state.lang === 'zh' ? 'en' : 'zh';
        localStorage.setItem('lang', state.lang);
        updateLanguage();
        // Re-render current updates if any to localize some dynamic parts
        if (state.updates.length > 0) renderUpdates(filterLocalUpdates(state.updates));
    };

    // Confirmation Modal Handlers
    let onConfirmOk = null;

    const showConfirm = (titleKey, messageKey, onOk) => {
        const t = translations[state.lang];
        elements.confirmTitle.textContent = t[titleKey] || titleKey;
        elements.confirmMessage.textContent = t[messageKey] || messageKey;
        onConfirmOk = onOk;
        elements.confirmModal.classList.add('active');
    };

    const closeConfirm = () => {
        elements.confirmModal.classList.remove('active');
        onConfirmOk = null;
    };

    elements.confirmOkBtn.addEventListener('click', () => {
        if (onConfirmOk) onConfirmOk();
        closeConfirm();
    });

    elements.confirmCancelBtn.addEventListener('click', closeConfirm);

    // Batch Delete Action
    elements.batchDeleteBtn.addEventListener('click', () => {
        if (state.selectedIds.size === 0) return;
        
        showConfirm('confirm_delete_title', 'confirm_delete_msg', async () => {
            try {
                const response = await fetch('/api/updates/batch-delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids: Array.from(state.selectedIds) })
                });
                const result = await response.json();
                if (result.status === 'success') {
                    state.selectedIds.clear();
                    updateBatchDeleteVisibility();
                    fetchUpdates();
                }
            } catch (error) {
                console.error('Batch delete error:', error);
            }
        });
    });

    const updateBatchDeleteVisibility = () => {
        if (state.selectedIds.size > 0) {
            elements.batchDeleteBtn.style.display = 'flex';
            elements.batchDeleteBtn.querySelector('span').textContent = 
                `${translations[state.lang].btn_batch_delete} (${state.selectedIds.size})`;
        } else {
            elements.batchDeleteBtn.style.display = 'none';
        }
    };

    elements.themeToggle.addEventListener('click', toggleTheme);
    elements.langToggle.addEventListener('click', toggleLang);
    
    initTheme();
    initLang();

    // Navigation Logic
    elements.navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.getAttribute('data-view');
            switchView(view);
        });
    });

    function switchView(viewId) {
        state.currentView = viewId;
        
        // Update Nav UI
        elements.navItems.forEach(nav => {
            nav.classList.toggle('active', nav.getAttribute('data-view') === viewId);
        });

        // Update View UI
        elements.views.forEach(view => {
            view.classList.toggle('active', view.id === `${viewId}-view`);
        });

        if (viewId === 'updates') {
            fetchUpdates();
        }
        
        refreshIcons();
    }

    // Filters & Search Logic
    const updateFilters = () => {
        state.filters.product = elements.productFilter.value;
        state.filters.type = elements.typeFilter.value;
        state.filters.dateRange = elements.dateRangeFilter.value;
        state.filters.startDate = elements.startDateInput.value;
        state.filters.endDate = elements.endDateInput.value;
        state.filters.search = elements.globalSearch.value.toLowerCase();
        
        if (state.filters.dateRange === 'custom') {
            elements.customDateRange.style.display = 'flex';
        } else {
            elements.customDateRange.style.display = 'none';
        }
        
        if (state.currentView === 'updates') {
            fetchUpdates();
        }
    };

    elements.productFilter.addEventListener('change', updateFilters);
    elements.typeFilter.addEventListener('change', updateFilters);
    elements.dateRangeFilter.addEventListener('change', updateFilters);
    elements.startDateInput.addEventListener('change', updateFilters);
    elements.endDateInput.addEventListener('change', updateFilters);
    
    // Debounced search
    let searchTimeout;
    elements.globalSearch.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.filters.search = elements.globalSearch.value.toLowerCase();
            renderUpdates(filterLocalUpdates(state.updates));
        }, 300);
    });

    // API Calls
    async function fetchUpdates() {
        showLoading();
        
        let url = '/api/updates';
        const params = new URLSearchParams();
        
        if (state.filters.product) params.append('product', state.filters.product);
        if (state.filters.type) params.append('type', state.filters.type);
        
        if (state.filters.dateRange === 'custom') {
            if (state.filters.startDate) params.append('start_date', state.filters.startDate);
            if (state.filters.endDate) params.append('end_date', state.filters.endDate);
        } else if (state.filters.dateRange !== 'all') {
            params.append('days', state.filters.dateRange);
        }
        
        if (params.toString()) url += `?${params.toString()}`;

        try {
            const response = await fetch(url);
            state.updates = await response.json();
            renderUpdates(filterLocalUpdates(state.updates));
        } catch (error) {
            console.error('Error fetching updates:', error);
            const t = translations[state.lang];
            elements.updatesFeed.innerHTML = `
                <div class="placeholder-state">
                    <i data-lucide="alert-circle" class="placeholder-icon" style="color:var(--accent-red)"></i>
                    <h3>${t.conn_error}</h3>
                    <p>${t.conn_error_desc}</p>
                    <button class="btn btn-secondary" onclick="location.reload()" style="margin-top:1rem">${t.retry}</button>
                </div>
            `;
            refreshIcons();
        }
    }

    function filterLocalUpdates(updates) {
        if (!state.filters.search) return updates;
        return updates.filter(u => 
            u.title.toLowerCase().includes(state.filters.search) || 
            (u.summary && u.summary.toLowerCase().includes(state.filters.search)) ||
            u.product.toLowerCase().includes(state.filters.search) ||
            (u.tags && u.tags.some(t => t.toLowerCase().includes(state.filters.search)))
        );
    }

    function renderUpdates(updates) {
        if (!updates || updates.length === 0) {
            const t = translations[state.lang];
            elements.updatesFeed.innerHTML = `
                <div class="placeholder-state">
                    <i data-lucide="inbox" class="placeholder-icon"></i>
                    <h3>${t.no_insights}</h3>
                    <p>${t.no_insights_desc}</p>
                </div>
            `;
            refreshIcons();
            return;
        }

        elements.updatesFeed.innerHTML = '';
        updates.forEach(update => {
            const card = createUpdateCard(update);
            elements.updatesFeed.appendChild(card);
        });
        refreshIcons();
    }

    function createUpdateCard(update) {
        const div = document.createElement('div');
        div.className = `glass-card ${state.selectedIds.has(update.id) ? 'selected' : ''}`;
        div.setAttribute('data-id', update.id);
        
        const date = new Date(update.publish_time).toLocaleDateString(state.lang === 'zh' ? 'zh-CN' : 'en-US', {
            month: 'short', day: 'numeric', year: 'numeric'
        });

        const productClass = `tag-${update.product.toLowerCase().replace(/\s+/g, '')}`;
        const typeBadge = update.update_type ? `<span class="card-tag tag-type">${update.update_type}</span>` : '';
        const engagementBadge = update.engagement > 0 ? `<div class="engagement-badge"><i data-lucide="zap"></i> ${update.engagement}</div>` : '';
        const sourceIcon = getSourceIconName(update.source_type);
        const isSelected = state.selectedIds.has(update.id);
        
        div.innerHTML = `
            <div class="card-selection">
                <label class="checkbox-container">
                    <input type="checkbox" class="update-check" ${isSelected ? 'checked' : ''}>
                    <span class="checkmark"></span>
                </label>
            </div>
            <div class="card-header">
                <div class="header-badges">
                    <span class="card-tag ${productClass}">${update.product}</span>
                    ${typeBadge}
                </div>
                <p class="update-date">${date}</p>
            </div>
            <h3 class="update-title">${update.title}</h3>
            <p class="update-summary">${update.summary || update.content || 'No description available.'}</p>
            <div class="card-footer">
                <div class="footer-left">
                    <div class="card-tags-mini">
                        ${(update.tags || []).slice(0, 2).map(t => `<span class="mini-tag">#${t}</span>`).join('')}
                    </div>
                    ${engagementBadge}
                </div>
                <div class="footer-actions">
                    <button class="btn-icon delete-btn" title="Delete">
                        <i data-lucide="trash-2"></i>
                    </button>
                    <div class="source-icon">
                        <i data-lucide="${sourceIcon}"></i>
                    </div>
                </div>
            </div>
        `;

        // Selection handling
        const checkbox = div.querySelector('.update-check');
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            if (checkbox.checked) {
                state.selectedIds.add(update.id);
                div.classList.add('selected');
            } else {
                state.selectedIds.delete(update.id);
                div.classList.remove('selected');
            }
            updateBatchDeleteVisibility();
        });

        // Delete button handling
        const deleteBtn = div.querySelector('.delete-btn');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            showConfirm('confirm_delete_title', 'confirm_single_delete_msg', async () => {
                try {
                    const response = await fetch(`/api/updates/${update.id}`, { method: 'DELETE' });
                    const result = await response.json();
                    if (result.status === 'success') {
                        state.selectedIds.delete(update.id);
                        updateBatchDeleteVisibility();
                        fetchUpdates();
                    }
                } catch (error) {
                    console.error('Delete error:', error);
                }
            });
        });

        div.addEventListener('click', () => showDetailModal(update));
        return div;
    }

    function getSourceIconName(type) {
        switch (type) {
            case 'blog': return 'book-open';
            case 'github': return 'github';
            case 'changelog': return 'history';
            case 'social': return 'share-2';
            default: return 'link';
        }
    }

    function showDetailModal(update) {
        const date = new Date(update.publish_time).toLocaleDateString(state.lang === 'zh' ? 'zh-CN' : 'en-US', {
            weekday: 'long', month: 'long', day: 'numeric', year: 'numeric'
        });
        
        const productClass = `tag-${update.product.toLowerCase().replace(/\s+/g, '')}`;
        
        elements.modalBadgeContainer.innerHTML = `
            <span class="card-tag ${productClass}">${update.product}</span>
            <span class="update-date" style="margin-left: 1rem">${date}</span>
        `;
        
        elements.modalBody.innerHTML = `
            <h1 class="update-title" style="-webkit-line-clamp: none; font-size: 2rem; margin-bottom: 1.5rem;">${update.title}</h1>
            <div class="modal-meta" style="margin-bottom: 2rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                ${(update.tags || []).map(t => `<span class="card-tag" style="background:var(--glass-bg); border:1px solid var(--glass-border); color:var(--text-dim); text-transform:none;">${t}</span>`).join('')}
            </div>
            <div class="content-body" style="color: var(--text-main); font-size: 1.1rem; line-height: 1.7;">
                ${(update.content || update.summary || 'No detailed content available.').replace(/\n/g, '<br>')}
            </div>
        `;
        
        const sourceUrl = update.source_url || '#';
        elements.modalSourceLink.href = sourceUrl;
        
        if (!update.source_url || update.source_url === '#') {
            elements.modalSourceLink.style.opacity = '0.5';
            elements.modalSourceLink.style.pointerEvents = 'none';
        } else {
            elements.modalSourceLink.style.opacity = '1';
            elements.modalSourceLink.style.pointerEvents = 'auto';
        }
        
        elements.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        refreshIcons();
    }

    function closeModal() {
        elements.modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }

    elements.closeModalBtn.addEventListener('click', closeModal);
    elements.modalBackdrop.addEventListener('click', closeModal);

    function showLoading() {
        const t = translations[state.lang];
        elements.updatesFeed.innerHTML = `
            <div class="loading-state" style="grid-column: 1/-1; padding: 5rem 0; text-align: center;">
                <div class="spinner"></div>
                <p style="color:var(--text-dim)">${t.loading_insights}</p>
            </div>
        `;
    }

    // Collection Modal Handlers
    const openCollectModal = () => {
        elements.collectModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    };

    const closeCollectModal = () => {
        elements.collectModal.classList.remove('active');
        document.body.style.overflow = 'auto';
    };

    elements.refreshBtn.addEventListener('click', openCollectModal);
    elements.closeCollectModalBtn.addEventListener('click', closeCollectModal);

    // Collection Action
    elements.startCollectBtn.addEventListener('click', async () => {
        const t = translations[state.lang];
        const days = parseInt(elements.collectDays.value);
        const products = Array.from(elements.platformChecks)
            .filter(check => check.checked)
            .map(check => check.value);

        if (products.length === 0) {
            alert(state.lang === 'zh' ? '请至少选择一个平台' : 'Please select at least one platform');
            return;
        }

        closeCollectModal();
        
        elements.refreshBtn.disabled = true;
        const originalContent = elements.refreshBtn.innerHTML;
        elements.refreshBtn.innerHTML = `<i data-lucide="loader-2" class="icon animate-spin"></i><span>${t.scanning}</span>`;
        refreshIcons();

        // Progress UI in feed
        elements.updatesFeed.innerHTML = `
            <div class="placeholder-state" id="collect-progress">
                <div class="spinner"></div>
                <h3 id="progress-title">${t.starting_task}</h3>
                <div id="progress-list" style="margin-top:1.5rem; text-align:left; max-width:400px; width:100%; font-size:0.9rem;"></div>
            </div>
        `;

        try {
            const startRes = await fetch('/api/collect', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ days, products })
            });
            const { job_id } = await startRes.json();

            let lastProgressLen = 0;
            const poll = setInterval(async () => {
                try {
                    const statusRes = await fetch(`/api/collect/status/${job_id}`);
                    const job = await statusRes.json();

                    const list = document.getElementById('progress-list');
                    if (list) {
                        const newItems = job.progress.slice(lastProgressLen);
                        newItems.forEach(msg => {
                            const item = document.createElement('div');
                            item.style.padding = '0.5rem';
                            item.style.borderBottom = '1px solid var(--glass-border)';
                            item.style.color = 'var(--text-dim)';
                            item.innerHTML = `<i data-lucide="check-circle-2" style="width:14px; height:14px; margin-right:8px; color:var(--accent-green); vertical-align:middle;"></i> ${msg}`;
                            list.appendChild(item);
                        });
                        lastProgressLen = job.progress.length;
                        refreshIcons();
                    }

                    if (job.status === 'done') {
                        clearInterval(poll);
                        const title = document.getElementById('progress-title');
                        if (title) title.textContent = `${t.completed_in}${job.total_time_seconds}${t.seconds}`;
                        
                        setTimeout(() => {
                            fetchUpdates();
                            elements.refreshBtn.disabled = false;
                            elements.refreshBtn.innerHTML = originalContent;
                            refreshIcons();
                        }, 1000);
                    }
                } catch (e) {
                    clearInterval(poll);
                    elements.refreshBtn.disabled = false;
                    elements.refreshBtn.innerHTML = originalContent;
                    refreshIcons();
                }
            }, 1000);

        } catch (error) {
            console.error('Error triggering collection:', error);
            elements.refreshBtn.disabled = false;
            elements.refreshBtn.innerHTML = originalContent;
            refreshIcons();
        }
    });

    // Initial Load
    fetchUpdates();
    
    // Periodically update system status (fake for now)
    setInterval(() => {
        const dot = document.querySelector('.pulse-dot');
        if (dot) {
            dot.style.background = Math.random() > 0.05 ? 'var(--accent-green)' : 'var(--accent-amber)';
        }
    }, 5000);
});
