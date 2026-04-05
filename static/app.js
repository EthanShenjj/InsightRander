document.addEventListener('DOMContentLoaded', () => {
    const updatesFeed = document.getElementById('updates-feed');
    const refreshBtn = document.getElementById('refresh-btn');
    const productFilter = document.getElementById('product-filter');
    const typeFilter = document.getElementById('type-filter');
    const dateRangeFilter = document.getElementById('date-range-filter');
    const customDateRange = document.getElementById('custom-date-range');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');

    let currentUpdates = [];

    // 设置默认日期（今天）
    const today = new Date().toISOString().split('T')[0];
    endDateInput.value = today;
    
    // 日期范围选择器变化事件
    dateRangeFilter.addEventListener('change', () => {
        if (dateRangeFilter.value === 'custom') {
            customDateRange.style.display = 'flex';
        } else {
            customDateRange.style.display = 'none';
            fetchUpdates();
        }
    });
    
    // 自定义日期变化事件
    startDateInput.addEventListener('change', fetchUpdates);
    endDateInput.addEventListener('change', fetchUpdates);

    async function fetchUpdates() {
        showLoading();
        const product = productFilter.value;
        const type = typeFilter.value;
        const dateRange = dateRangeFilter.value;
        
        let url = '/api/updates';
        const params = new URLSearchParams();
        
        if (product) params.append('product', product);
        if (type) params.append('type', type);
        
        // 添加日期范围参数
        if (dateRange === 'custom') {
            if (startDateInput.value) params.append('start_date', startDateInput.value);
            if (endDateInput.value) params.append('end_date', endDateInput.value);
        } else if (dateRange !== 'all') {
            params.append('days', dateRange);
        }
        // dateRange === 'all' 时不传日期参数，后端返回全部数据
        
        if (params.toString()) url += `?${params.toString()}`;

        try {
            const response = await fetch(url);
            currentUpdates = await response.json();
            renderUpdates(currentUpdates);
        } catch (error) {
            console.error('Error fetching updates:', error);
            updatesFeed.innerHTML = `<div class="error-state">Failed to load updates. Please check backend connection.</div>`;
        }
    }

    function renderUpdates(updates) {
        if (!updates || updates.length === 0) {
            updatesFeed.innerHTML = `<div class="empty-state">No updates found matching your filters.</div>`;
            return;
        }

        updatesFeed.innerHTML = '';
        updates.forEach(update => {
            const card = createUpdateCard(update);
            updatesFeed.appendChild(card);
        });
    }

    function createUpdateCard(update) {
        const div = document.createElement('div');
        div.className = 'glass-card';
        
        const date = new Date(update.publish_time).toLocaleDateString('en-US', {
            month: 'short', day: 'numeric', year: 'numeric'
        });

        const productClass = `tag-${update.product.toLowerCase()}`;
        
        div.innerHTML = `
            <div class="card-header">
                <span class="card-tag ${productClass}">${update.product}</span>
                <p class="update-date">${date}</p>
            </div>
            <h3 class="update-title">${update.title}</h3>
            <p class="update-summary">${update.summary || update.content || 'No description available.'}</p>
            <div class="card-footer">
                <a href="${update.source_url}" target="_blank" class="btn-link">Read Source ↗</a>
                <span class="source-icon">${getSourceIcon(update.source_type)}</span>
            </div>
        `;
        return div;
    }

    function getSourceIcon(type) {
        switch (type) {
            case 'blog': return '📝';
            case 'github': return '🐙';
            case 'changelog': return '🔄';
            default: return '🔗';
        }
    }

    function showLoading() {
        updatesFeed.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Loading the latest insights...</p>
            </div>
        `;
    }

    refreshBtn.addEventListener('click', async () => {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<span class="icon">⌛</span> 采集中...';

        // 显示进度面板
        updatesFeed.innerHTML = `
            <div class="loading-state" id="collect-progress">
                <div class="spinner"></div>
                <p id="progress-title">正在启动采集任务...</p>
                <ul id="progress-list" style="list-style:none; margin-top:1rem; text-align:left; font-size:0.9rem; color:var(--text-dim);"></ul>
            </div>
        `;

        try {
            // 启动后台任务
            const startRes = await fetch('/api/collect', { method: 'POST' });
            const { job_id } = await startRes.json();

            // 轮询进度
            let lastProgressLen = 0;
            const poll = setInterval(async () => {
                try {
                    const statusRes = await fetch(`/api/collect/status/${job_id}`);
                    const job = await statusRes.json();

                    // 更新进度列表
                    const list = document.getElementById('progress-list');
                    if (list) {
                        const newItems = job.progress.slice(lastProgressLen);
                        newItems.forEach(msg => {
                            const li = document.createElement('li');
                            li.textContent = msg;
                            li.style.padding = '2px 0';
                            list.appendChild(li);
                        });
                        lastProgressLen = job.progress.length;
                    }

                    if (job.status === 'done') {
                        clearInterval(poll);

                        const title = document.getElementById('progress-title');
                        if (title) title.textContent = `采集完成！总耗时 ${job.total_time_seconds} 秒`;

                        // 刷新数据列表
                        await fetchUpdates();

                        refreshBtn.disabled = false;
                        refreshBtn.innerHTML = '<span class="icon">🔄</span> Scan Sources';
                    }
                } catch (e) {
                    clearInterval(poll);
                    refreshBtn.disabled = false;
                    refreshBtn.innerHTML = '<span class="icon">🔄</span> Scan Sources';
                }
            }, 1500); // 每 1.5 秒轮询一次

        } catch (error) {
            console.error('Error triggering collection:', error);
            updatesFeed.innerHTML = `<div class="error-state">采集失败，请检查后端连接</div>`;
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<span class="icon">🔄</span> Scan Sources';
        }
    });

    productFilter.addEventListener('change', fetchUpdates);
    typeFilter.addEventListener('change', fetchUpdates);

    // Initial load
    fetchUpdates();
});
