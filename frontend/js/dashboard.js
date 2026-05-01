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
                    alert(`Analysis complete for ${data.company_name || 'document'}! Check console for results.`);
                    console.log('Analysis Results:', data);
                    // Update UI here using the returned data
                    this.updateDashboardWithResults(data);
                } else {
                    alert(`Error: ${data.message || 'Failed to analyze document'}`);
                }
            } catch (error) {
                console.error('Upload error:', error);
                alert('Connection error while uploading document.');
            } finally {
                uploadBtn.innerHTML = originalText;
                uploadBtn.disabled = false;
                event.target.value = ''; // Reset file input
            }
        }
    }

    updateDashboardWithResults(data) {
        // Here we would typically populate the various charts and tables
        // For example, updating the company name if found
        if (data.company_name) {
            const companyDisplay = document.getElementById('companyNameDisplay');
            if (companyDisplay) companyDisplay.textContent = data.company_name;
        }
        
        // Update document count
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