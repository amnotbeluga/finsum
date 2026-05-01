// frontend/js/dashboard.js
class Dashboard {
    constructor() {
        this.apiUrl = 'http://localhost:8000/api';
        this.checkAuth();
        this.init();
    }

    async checkAuth() {
        if (!window.auth.isAuthenticated()) {
            window.location.href = '/';
            return;
        }
        
        const isValid = await window.auth.verifyToken();
        if (!isValid) {
            window.auth.logout();
        }
    }

    init() {
        this.displayUserInfo();
        this.setupEventListeners();
        this.loadSampleData();
        this.loadChatHistory();
    }

    displayUserInfo() {
        const user = window.auth.getUser();
        if (user) {
            const displayName = document.getElementById('userDisplayName');
            if (displayName) {
                displayName.textContent = user.fullName || user.email || 'User';
            }
        }
    }

    setupEventListeners() {
        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.auth.logout();
            });
        }

        // File upload
        const uploadBtn = document.getElementById('uploadBtn');
        const fileInput = document.getElementById('fileInput');
        
        if (uploadBtn && fileInput) {
            uploadBtn.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }

        // View all history
        const viewAllHistory = document.getElementById('viewAllHistory');
        if (viewAllHistory) {
            viewAllHistory.addEventListener('click', (e) => {
                e.preventDefault();
                alert('History feature coming soon!');
            });
        }

        // Chat widget
        this.setupChatWidget();
    }

    setupChatWidget() {
        const chatButton = document.getElementById('chatButton');
        const chatBox = document.getElementById('chatBox');
        const closeChat = document.getElementById('closeChat');
        const sendBtn = document.getElementById('widgetSendBtn');
        const chatInput = document.getElementById('widgetChatInput');

        if (chatButton && chatBox) {
            chatButton.addEventListener('click', () => {
                chatBox.classList.toggle('open');
            });
        }

        if (closeChat && chatBox) {
            closeChat.addEventListener('click', () => {
                chatBox.classList.remove('open');
            });
        }

        if (sendBtn && chatInput) {
            sendBtn.addEventListener('click', () => this.sendChatMessage());
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
        }
    }

    async sendChatMessage() {
        const input = document.getElementById('widgetChatInput');
        const message = input.value.trim();
        
        if (!message) return;

        const messages = document.getElementById('chatMessages');
        
        // Add user message
        messages.innerHTML += `
            <div class="message user-message">
                <div class="message-content">${this.escapeHtml(message)}</div>
            </div>
        `;
        
        input.value = '';
        messages.scrollTop = messages.scrollHeight;

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${window.auth.token}`
                },
                body: JSON.stringify({ message: message })
            });

            this.hideTypingIndicator();

            const data = await response.json();
            
            if (response.ok) {
                messages.innerHTML += `
                    <div class="message ai-message">
                        <div class="message-content">${this.escapeHtml(data.response)}</div>
                    </div>
                `;
            } else {
                messages.innerHTML += `
                    <div class="message ai-message">
                        <div class="message-content">${this.escapeHtml(data.response || 'FinSum AI is processing your request. Please try again.')}</div>
                    </div>
                `;
            }
        } catch (error) {
            this.hideTypingIndicator();
            messages.innerHTML += `
                <div class="message ai-message">
                    <div class="message-content">Connection issue. Please check your network and try again.</div>
                </div>
            `;
            console.error('Chat error:', error);
        }
        
        messages.scrollTop = messages.scrollHeight;
    }

    showTypingIndicator() {
        const messages = document.getElementById('chatMessages');
        if (!messages) return;
        
        if (document.getElementById('typing-indicator')) return;
        
        const indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'message ai-message';
        indicator.innerHTML = `
            <div class="message-content">
                <i class="fas fa-circle-notch fa-spin"></i> FinSum AI is thinking...
            </div>
        `;
        messages.appendChild(indicator);
        messages.scrollTop = messages.scrollHeight;
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }

    async loadChatHistory() {
        if (!window.auth.isAuthenticated()) return;

        try {
            const response = await fetch(`${this.apiUrl}/chat/history`, {
                headers: {
                    'Authorization': `Bearer ${window.auth.token}`
                }
            });

            if (response.ok) {
                const history = await response.json();
                if (history.length > 0) {
                    const messages = document.getElementById('chatMessages');
                    messages.innerHTML = '';
                    
                    history.slice(0, 10).reverse().forEach(msg => {
                        messages.innerHTML += `
                            <div class="message user-message">
                                <div class="message-content">${this.escapeHtml(msg.message)}</div>
                            </div>
                            <div class="message ai-message">
                                <div class="message-content">${this.escapeHtml(msg.response)}</div>
                            </div>
                        `;
                    });
                    messages.scrollTop = messages.scrollHeight;
                }
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    async handleFileUpload(event) {
        const files = event.target.files;
        if (files.length > 0) {
            const file = files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            // Show loading state
            const uploadBtn = document.getElementById('uploadBtn');
            const originalText = uploadBtn.innerHTML;
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
            uploadBtn.disabled = true;
            
            try {
                const response = await fetch(`${this.apiUrl}/analyze`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${window.auth.token}`
                    },
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    this.updateDashboardWithResults(data);
                } else {
                    this.showNotification(`Error: ${data.message || 'Failed to analyze document'}`, 'error');
                }
            } catch (error) {
                console.error('Upload error:', error);
                this.showNotification('Connection error while uploading document.', 'error');
            } finally {
                uploadBtn.innerHTML = originalText;
                uploadBtn.disabled = false;
                event.target.value = ''; // Reset file input
            }
        }
    }

    showNotification(message, type = 'success') {
        const container = document.getElementById('alertContainer');
        if (container) {
            container.className = `alert alert-${type}`;
            container.textContent = message;
            container.style.display = 'block';
            setTimeout(() => { container.style.display = 'none'; }, 5000);
        }
    }

    updateDashboardWithResults(data) {
        // Show success notification
        this.showNotification(`✅ Analysis complete for ${data.company_name || 'document'}!`);

        // Hide sample card, show results
        const sampleCard = document.getElementById('sampleCard');
        if (sampleCard) sampleCard.style.display = 'none';

        const results = document.getElementById('analysisResults');
        if (results) results.style.display = 'block';

        // Company info
        const companyEl = document.getElementById('resultCompany');
        if (companyEl) companyEl.textContent = data.company_name || 'Unknown Company';

        const symbolEl = document.getElementById('resultSymbol');
        if (symbolEl) symbolEl.textContent = data.trading_symbol || 'N/A';

        // Document info
        const textLenEl = document.getElementById('resultTextLen');
        if (textLenEl && data.document_processing) {
            const chars = data.document_processing.text_length || 0;
            textLenEl.textContent = `${(chars / 1000).toFixed(1)}K characters`;
        }

        const tablesEl = document.getElementById('resultTables');
        if (tablesEl && data.document_processing) {
            tablesEl.textContent = data.document_processing.tables_extracted || 0;
        }

        // Sentiment
        if (data.sentiment) {
            const cls = data.sentiment.classification || 'Neutral';
            const score = data.sentiment.score || 0;

            const classEl = document.getElementById('sentimentClass');
            if (classEl) {
                classEl.textContent = cls;
                classEl.style.color = cls === 'Positive' ? '#10b981' : cls === 'Negative' ? '#ef4444' : '#f59e0b';
            }

            const scoreEl = document.getElementById('sentimentScore');
            if (scoreEl) scoreEl.textContent = `Score: ${score}`;

            // Components
            const compEl = document.getElementById('sentimentComponents');
            if (compEl && data.sentiment.components) {
                const c = data.sentiment.components;
                compEl.innerHTML = `
                    FinBERT: ${c.finbert}<br>
                    VADER: ${c.vader}<br>
                    TextBlob: ${c.textblob}<br>
                    Keyword: ${c.keyword}
                `;
            }

            // Bar
            const bar = document.getElementById('sentimentBar');
            if (bar) {
                const pct = Math.round((score + 1) / 2 * 100);
                bar.style.width = `${pct}%`;
                bar.style.background = cls === 'Positive' ? '#10b981' : cls === 'Negative' ? '#ef4444' : '#f59e0b';
            }
        }

        // Summaries
        const sumEl = document.getElementById('summariesContent');
        if (sumEl && data.summaries) {
            let html = '';
            for (const [category, text] of Object.entries(data.summaries)) {
                const label = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                html += `
                    <div style="margin-bottom:15px;padding:15px;background:white;border-radius:12px;">
                        <div style="font-weight:600;color:#1b6ef3;margin-bottom:6px;font-size:13px;text-transform:uppercase;letter-spacing:0.5px;">${this.escapeHtml(label)}</div>
                        <div style="color:#1a2639;">${this.escapeHtml(text)}</div>
                    </div>
                `;
            }
            sumEl.innerHTML = html || '<div style="color:#8a9bb5;">No summaries generated.</div>';
        }

        // Risk Analysis — always show section
        const riskSection = document.getElementById('riskSection');
        if (riskSection) riskSection.style.display = 'block';
        if (data.risk_analysis && !data.risk_analysis.error) {
            const r = data.risk_analysis;
            const riskEl = document.getElementById('riskContent');
            if (riskEl) {
                const metrics = [
                    { label: 'Market Price', value: r.market_price ? `₹${r.market_price.toLocaleString()}` : 'N/A' },
                    { label: 'P/E Ratio', value: r.pe_ratio ? r.pe_ratio.toFixed(2) : 'N/A' },
                    { label: 'ROE', value: r.roe ? `${r.roe.toFixed(1)}%` : 'N/A' },
                    { label: 'Debt/Equity', value: r.debt_to_equity ? r.debt_to_equity.toFixed(1) : 'N/A' },
                    { label: 'Volatility', value: r.volatility_annualized ? `${(r.volatility_annualized * 100).toFixed(1)}%` : 'N/A' },
                    { label: 'VaR (95%)', value: r.var_95 ? `${(r.var_95 * 100).toFixed(2)}%` : 'N/A' },
                    { label: 'Altman Z-Score', value: r.altman_z_score ? `${r.altman_z_score.toFixed(2)} (${r.altman_zone})` : 'N/A' },
                    { label: 'SMA 50', value: r.sma_50 ? `₹${r.sma_50.toFixed(2)}` : 'N/A' },
                    { label: 'SMA 200', value: r.sma_200 ? `₹${r.sma_200.toFixed(2)}` : 'N/A' },
                ];
                riskEl.innerHTML = metrics.map(m => `
                    <div style="background:white;padding:12px;border-radius:10px;text-align:center;">
                        <div style="color:#8a9bb5;font-size:11px;text-transform:uppercase;">${m.label}</div>
                        <div style="font-weight:700;font-size:16px;margin-top:4px;color:#0a1a2b;">${m.value}</div>
                    </div>
                `).join('');
            }

            const recEl = document.getElementById('riskRecommendation');
            if (recEl && r.recommendation) {
                const colors = { 'Strong Buy': '#10b981', 'Buy': '#34d399', 'Accumulate on Dips': '#6ee7b7', 'Hold': '#f59e0b', 'Reduce': '#fb923c', 'Sell': '#ef4444' };
                recEl.textContent = `Recommendation: ${r.recommendation}`;
                recEl.style.background = (colors[r.recommendation] || '#8a9bb5') + '22';
                recEl.style.color = colors[r.recommendation] || '#8a9bb5';
            }
        } else {
            const riskEl = document.getElementById('riskContent');
            if (riskEl) riskEl.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:#8a9bb5;padding:20px;">No trading symbol detected — risk analysis unavailable for this document.</div>';
            const recEl = document.getElementById('riskRecommendation');
            if (recEl) recEl.style.display = 'none';
        }

        // News — always show section
        const newsSection = document.getElementById('newsSection');
        if (newsSection) newsSection.style.display = 'block';
        if (data.news && data.news.length > 0) {
            const newsEl = document.getElementById('newsContent');
            if (newsEl) {
                newsEl.innerHTML = data.news.slice(0, 8).map(n => `
                    <div style="padding:12px 0;border-bottom:1px solid #eef2f6;display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <a href="${n.link}" target="_blank" style="color:#1a2639;text-decoration:none;font-weight:500;">${this.escapeHtml(n.title)}</a>
                            <div style="color:#8a9bb5;font-size:12px;margin-top:4px;">${n.source} • ${n.emoji} ${n.label}</div>
                        </div>
                    </div>
                `).join('');
            }
        } else {
            const newsEl = document.getElementById('newsContent');
            if (newsEl) newsEl.innerHTML = '<div style="color:#8a9bb5;padding:10px;">No news articles found for this company.</div>';
        }

        // Scroll to results
        results.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Update doc count
        const docCount = document.getElementById('documentCount');
        if (docCount) {
            let current = parseInt(docCount.textContent || '0');
            docCount.textContent = (current + 1).toString();
        }

        const totalDocs = document.getElementById('totalDocuments');
        if (totalDocs) {
            let current = parseInt(totalDocs.textContent.split(' ')[0] || '0');
            totalDocs.textContent = `${current + 1} Total`;
        }
    }

    loadSampleData() {
        const docCount = document.getElementById('documentCount');
        if (docCount) {
            docCount.textContent = '5';
        }
        
        const lastUsed = document.getElementById('lastUsed');
        if (lastUsed) {
            lastUsed.textContent = 'Ready to help';
        }
        
        const totalDocs = document.getElementById('totalDocuments');
        if (totalDocs) {
            totalDocs.textContent = '5 Total';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('dashboard')) {
        window.dashboard = new Dashboard();
    }
});