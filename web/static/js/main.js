/**
 * Socratic RAG Enhanced - Main JavaScript
 * Interactive features for dashboard, conversations, code generation, and system monitoring
 * Clean/minimal design - Desktop focused
 */

// Global application state
window.SocraticRAG = {
    version: '7.3.0',
    charts: {},
    intervals: {},
    config: {
        autoRefreshInterval: 30000, // 30 seconds
        chartColors: {
            primary: '#2f81f7',
            success: '#3fb950',
            warning: '#d29922',
            danger: '#f85149',
            info: '#a5a5a5',
            muted: '#6e7681'
        }
    }
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Socratic RAG Enhanced v' + SocraticRAG.version + ' initializing...');

    // Initialize all components
    initializeDashboardCharts();
    initializeRealTimeFeatures();
    initializeSocraticConversation();
    initializeCodeGeneration();
    initializeProjectManagement();
    initializeSystemMonitoring();
    initializeUIEnhancements();

    console.log('✅ Socratic RAG Enhanced initialized successfully');
});

// ============================================================================
// DASHBOARD CHARTS & ANALYTICS
// ============================================================================

function initializeDashboardCharts() {
    // Project progress chart
    const progressCtx = document.getElementById('projectProgressChart');
    if (progressCtx) {
        SocraticRAG.charts.progress = new Chart(progressCtx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'In Progress', 'Pending', 'Failed'],
                datasets: [{
                    data: [0, 0, 0, 0], // Will be updated via HTMX
                    backgroundColor: [
                        SocraticRAG.config.chartColors.success,
                        SocraticRAG.config.chartColors.primary,
                        SocraticRAG.config.chartColors.warning,
                        SocraticRAG.config.chartColors.danger
                    ],
                    borderWidth: 2,
                    borderColor: '#21262d'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#f0f6fc',
                            padding: 15,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    // Agent activity timeline
    const activityCtx = document.getElementById('agentActivityChart');
    if (activityCtx) {
        SocraticRAG.charts.activity = new Chart(activityCtx, {
            type: 'line',
            data: {
                labels: [], // Will be populated with time data
                datasets: [{
                    label: 'Agent Requests',
                    data: [],
                    borderColor: SocraticRAG.config.chartColors.primary,
                    backgroundColor: SocraticRAG.config.chartColors.primary + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#f0f6fc'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#8b949e' },
                        grid: { color: '#30363d' }
                    },
                    y: {
                        ticks: { color: '#8b949e' },
                        grid: { color: '#30363d' }
                    }
                }
            }
        });
    }

    // Code quality metrics
    const qualityCtx = document.getElementById('codeQualityChart');
    if (qualityCtx) {
        SocraticRAG.charts.quality = new Chart(qualityCtx, {
            type: 'radar',
            data: {
                labels: ['Complexity', 'Maintainability', 'Coverage', 'Security', 'Performance'],
                datasets: [{
                    label: 'Code Quality Score',
                    data: [0, 0, 0, 0, 0], // Will be updated with actual metrics
                    borderColor: SocraticRAG.config.chartColors.success,
                    backgroundColor: SocraticRAG.config.chartColors.success + '20',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f0f6fc'
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { color: '#8b949e' },
                        grid: { color: '#30363d' },
                        pointLabels: { color: '#f0f6fc' }
                    }
                }
            }
        });
    }
}

function updateChartData(chartName, data) {
    if (SocraticRAG.charts[chartName]) {
        const chart = SocraticRAG.charts[chartName];
        if (data.labels) chart.data.labels = data.labels;
        if (data.datasets) chart.data.datasets = data.datasets;
        chart.update('none'); // No animation for real-time updates
    }
}

// ============================================================================
// REAL-TIME FEATURES
// ============================================================================

function initializeRealTimeFeatures() {
    // Auto-refresh system status
    SocraticRAG.intervals.systemStatus = setInterval(function() {
        const statusButton = document.querySelector('[hx-get*="api_system_status"]');
        if (statusButton && document.hasFocus()) {
            htmx.trigger(statusButton, 'click');
        }
    }, SocraticRAG.config.autoRefreshInterval);

    // Real-time metrics updates
    SocraticRAG.intervals.metrics = setInterval(function() {
        updateDashboardMetrics();
    }, SocraticRAG.config.autoRefreshInterval);

    // Activity feed updates
    SocraticRAG.intervals.activity = setInterval(function() {
        refreshActivityFeed();
    }, SocraticRAG.config.autoRefreshInterval / 2); // More frequent activity updates
}

function updateDashboardMetrics() {
    // Update metric cards with live data
    const metricCards = document.querySelectorAll('[data-metric]');
    metricCards.forEach(card => {
        const metric = card.dataset.metric;
        fetchMetricData(metric).then(data => {
            updateMetricCard(card, data);
        });
    });
}

function fetchMetricData(metric) {
    return fetch(`/api/metrics/${metric}`)
        .then(response => response.json())
        .catch(error => {
            console.warn(`Failed to fetch metric ${metric}:`, error);
            return { value: 'N/A', trend: 'neutral' };
        });
}

function updateMetricCard(card, data) {
    const valueElement = card.querySelector('.metric-value');
    const trendElement = card.querySelector('.metric-trend');

    if (valueElement) {
        valueElement.textContent = data.value;

        // Add animation for value changes
        valueElement.classList.add('fade-in');
        setTimeout(() => valueElement.classList.remove('fade-in'), 300);
    }

    if (trendElement && data.trend) {
        trendElement.className = `metric-trend trend-${data.trend}`;
        trendElement.innerHTML = getTrendIcon(data.trend);
    }
}

function getTrendIcon(trend) {
    switch (trend) {
        case 'up': return '<i class="bi bi-arrow-up text-success"></i>';
        case 'down': return '<i class="bi bi-arrow-down text-danger"></i>';
        case 'stable': return '<i class="bi bi-arrow-right text-muted"></i>';
        default: return '<i class="bi bi-dash text-muted"></i>';
    }
}

function refreshActivityFeed() {
    const activityContainer = document.getElementById('activity-feed');
    if (activityContainer) {
        htmx.ajax('GET', '/api/activity-feed', {
            target: '#activity-feed',
            swap: 'innerHTML'
        });
    }
}

// ============================================================================
// SOCRATIC CONVERSATION INTERFACE
// ============================================================================

function initializeSocraticConversation() {
    // Auto-scroll conversation to bottom
    const conversationContainer = document.getElementById('conversation-messages');
    if (conversationContainer) {
        scrollToBottom(conversationContainer);

        // Observe for new messages
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    scrollToBottom(conversationContainer);
                }
            });
        });

        observer.observe(conversationContainer, { childList: true });
    }

    // Role selector functionality
    const roleSelectors = document.querySelectorAll('[data-role]');
    roleSelectors.forEach(selector => {
        selector.addEventListener('click', function() {
            const role = this.dataset.role;
            switchConversationRole(role);

            // Update UI to show active role
            roleSelectors.forEach(s => s.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Message input enhancements
    const messageInput = document.getElementById('user-message');
    if (messageInput) {
        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        });

        // Submit on Ctrl+Enter
        messageInput.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                const form = this.closest('form');
                if (form) {
                    htmx.trigger(form, 'submit');
                }
            }
        });
    }

    // Question suggestion clicks
    document.addEventListener('click', function(e) {
        if (e.target.matches('.question-suggestion')) {
            const question = e.target.textContent;
            const messageInput = document.getElementById('user-message');
            if (messageInput) {
                messageInput.value = question;
                messageInput.focus();
            }
        }
    });
}

function scrollToBottom(container) {
    setTimeout(() => {
        container.scrollTop = container.scrollHeight;
    }, 100);
}

function switchConversationRole(role) {
    // Update the conversation context
    fetch('/api/conversation/switch-role', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ role: role })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Role switched to ' + role, 'success');

            // Refresh question suggestions for new role
            refreshQuestionSuggestions(role);
        }
    })
    .catch(error => {
        console.error('Error switching role:', error);
        showNotification('Failed to switch role', 'error');
    });
}

function refreshQuestionSuggestions(role) {
    const suggestionsContainer = document.getElementById('question-suggestions');
    if (suggestionsContainer) {
        htmx.ajax('GET', `/api/conversation/suggestions?role=${role}`, {
            target: '#question-suggestions',
            swap: 'innerHTML'
        });
    }
}

// ============================================================================
// CODE GENERATION INTERFACE
// ============================================================================

function initializeCodeGeneration() {
    // File tree toggle functionality
    const fileTreeToggles = document.querySelectorAll('.file-tree-toggle');
    fileTreeToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const target = document.querySelector(this.dataset.target);
            if (target) {
                target.classList.toggle('collapsed');
                this.querySelector('i').classList.toggle('bi-chevron-right');
                this.querySelector('i').classList.toggle('bi-chevron-down');
            }
        });
    });

    // Code file selection
    document.addEventListener('click', function(e) {
        if (e.target.matches('.file-tree-file')) {
            const filepath = e.target.dataset.filepath;
            if (filepath) {
                loadCodeFile(filepath);

                // Update active file indicator
                document.querySelectorAll('.file-tree-file').forEach(f => f.classList.remove('active'));
                e.target.classList.add('active');
            }
        }
    });

    // Copy code functionality
    document.addEventListener('click', function(e) {
        if (e.target.matches('.copy-code-btn') || e.target.closest('.copy-code-btn')) {
            const button = e.target.matches('.copy-code-btn') ? e.target : e.target.closest('.copy-code-btn');
            const codeBlock = button.closest('.code-output').querySelector('code, pre');

            if (codeBlock) {
                copyToClipboard(codeBlock.textContent);

                // Visual feedback
                const originalText = button.innerHTML;
                button.innerHTML = '<i class="bi bi-check"></i> Copied!';
                button.classList.add('btn-success');

                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.classList.remove('btn-success');
                }, 2000);
            }
        }
    });

    // Download generated code
    document.addEventListener('click', function(e) {
        if (e.target.matches('.download-code-btn') || e.target.closest('.download-code-btn')) {
            const projectId = document.querySelector('[data-project-id]')?.dataset.projectId;
            if (projectId) {
                downloadGeneratedCode(projectId);
            }
        }
    });

    // Test code functionality
    const testButtons = document.querySelectorAll('.test-code-btn');
    testButtons.forEach(button => {
        button.addEventListener('click', function() {
            const codebaseId = this.dataset.codebaseId;
            if (codebaseId) {
                runCodeTests(codebaseId);
            }
        });
    });
}

function loadCodeFile(filepath) {
    const codeContainer = document.getElementById('code-display');
    if (codeContainer) {
        // Show loading state
        codeContainer.innerHTML = '<div class="text-center p-4"><i class="bi bi-hourglass-split spin"></i> Loading...</div>';

        // Load file content
        htmx.ajax('GET', `/api/code/file?path=${encodeURIComponent(filepath)}`, {
            target: '#code-display',
            swap: 'innerHTML'
        });
    }
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Code copied to clipboard', 'success');
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        showNotification('Code copied to clipboard', 'success');
    } catch (err) {
        showNotification('Failed to copy code', 'error');
    }

    document.body.removeChild(textArea);
}

function downloadGeneratedCode(projectId) {
    const downloadLink = document.createElement('a');
    downloadLink.href = `/api/code/download/${projectId}`;
    downloadLink.download = `project-${projectId}-code.zip`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);

    showNotification('Download started', 'info');
}

function runCodeTests(codebaseId) {
    const testContainer = document.getElementById('test-results');
    if (testContainer) {
        // Show loading state
        testContainer.innerHTML = '<div class="text-center p-4"><i class="bi bi-hourglass-split spin"></i> Running tests...</div>';

        // Start test execution
        htmx.ajax('POST', `/api/code/test/${codebaseId}`, {
            target: '#test-results',
            swap: 'innerHTML'
        });
    }
}

// ============================================================================
// PROJECT MANAGEMENT
// ============================================================================

function initializeProjectManagement() {
    // Project creation form validation
    const projectForm = document.getElementById('create-project-form');
    if (projectForm) {
        projectForm.addEventListener('submit', function(e) {
            if (!validateProjectForm()) {
                e.preventDefault();
                return false;
            }
        });
    }

    // Technology stack selection
    const techStackInputs = document.querySelectorAll('.tech-stack-input');
    techStackInputs.forEach(input => {
        input.addEventListener('change', function() {
            updateTechStackPreview();
        });
    });

    // Module management
    const moduleToggles = document.querySelectorAll('.module-toggle');
    moduleToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const moduleId = this.dataset.moduleId;
            const isEnabled = this.checked;
            toggleProjectModule(moduleId, isEnabled);
        });
    });

    // Collaborative features
    const collaboratorInputs = document.querySelectorAll('.collaborator-input');
    collaboratorInputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateCollaboratorEmail(this.value, this);
        });
    });
}

function validateProjectForm() {
    const requiredFields = document.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });

    // Custom validation rules
    const projectName = document.getElementById('project-name');
    if (projectName && projectName.value.length < 3) {
        showFieldError(projectName, 'Project name must be at least 3 characters');
        isValid = false;
    }

    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);

    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.textContent = message;

    field.classList.add('is-invalid');
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

function updateTechStackPreview() {
    const selectedTechs = Array.from(document.querySelectorAll('.tech-stack-input:checked'))
        .map(input => input.value);

    const previewContainer = document.getElementById('tech-stack-preview');
    if (previewContainer) {
        previewContainer.innerHTML = selectedTechs.map(tech =>
            `<span class="badge bg-primary me-1">${tech}</span>`
        ).join('');
    }
}

function toggleProjectModule(moduleId, isEnabled) {
    fetch('/api/project/module/toggle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            module_id: moduleId,
            enabled: isEnabled
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Module ${isEnabled ? 'enabled' : 'disabled'}`, 'success');
        } else {
            showNotification('Failed to update module', 'error');
        }
    })
    .catch(error => {
        console.error('Error toggling module:', error);
        showNotification('Failed to update module', 'error');
    });
}

function validateCollaboratorEmail(email, inputElement) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (email && !emailRegex.test(email)) {
        showFieldError(inputElement, 'Please enter a valid email address');
    } else {
        clearFieldError(inputElement);
    }
}

// ============================================================================
// SYSTEM MONITORING
// ============================================================================

function initializeSystemMonitoring() {
    // Agent status monitoring
    updateAgentStatus();
    setInterval(updateAgentStatus, 15000); // Check every 15 seconds

    // Service health checks
    updateServiceStatus();
    setInterval(updateServiceStatus, 20000); // Check every 20 seconds

    // Performance monitoring
    if (window.performance && window.performance.navigation) {
        trackPagePerformance();
    }
}

function updateAgentStatus() {
    fetch('/api/agents/status')
        .then(response => response.json())
        .then(data => {
            updateStatusIndicators('agents', data);
        })
        .catch(error => {
            console.warn('Failed to fetch agent status:', error);
        });
}

function updateServiceStatus() {
    fetch('/api/services/status')
        .then(response => response.json())
        .then(data => {
            updateStatusIndicators('services', data);
        })
        .catch(error => {
            console.warn('Failed to fetch service status:', error);
        });
}

function updateStatusIndicators(type, data) {
    const indicator = document.getElementById(`${type}-status`);
    if (indicator) {
        const isHealthy = data.status === 'healthy';
        const iconClass = isHealthy ? 'text-success' : 'text-warning';
        const statusText = isHealthy ? type.charAt(0).toUpperCase() + type.slice(1) : 'Limited';

        indicator.innerHTML = `<i class="bi bi-${type === 'agents' ? 'cpu' : 'cloud-check'} ${iconClass}"></i> ${statusText}`;
    }
}

function trackPagePerformance() {
    const navigation = performance.getEntriesByType('navigation')[0];
    const loadTime = navigation.loadEventEnd - navigation.loadEventStart;

    if (loadTime > 2000) {
        console.warn(`Slow page load detected: ${loadTime}ms`);
    }

    // Send performance data to analytics endpoint
    fetch('/api/analytics/performance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            load_time: loadTime,
            page: window.location.pathname,
            timestamp: new Date().toISOString()
        })
    }).catch(error => {
        console.debug('Analytics tracking failed:', error);
    });
}

// ============================================================================
// UI ENHANCEMENTS
// ============================================================================

function initializeUIEnhancements() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Auto-hide alerts
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.add('fade');
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+K for search (future implementation)
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            // TODO: Open search modal
        }

        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) modal.hide();
            }
        }
    });

    // Tooltip initialization
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl =>
        new bootstrap.Tooltip(tooltipTriggerEl)
    );

    // Form auto-save (for longer forms)
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    autoSaveForms.forEach(form => {
        const formId = form.id;
        if (formId) {
            // Load saved data
            loadFormData(form, formId);

            // Save on input changes
            form.addEventListener('input', debounce(() => {
                saveFormData(form, formId);
            }, 1000));
        }
    });
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 300);
        }
    }, 4000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function saveFormData(form, formId) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    localStorage.setItem(`form_${formId}`, JSON.stringify(data));
}

function loadFormData(form, formId) {
    try {
        const savedData = localStorage.getItem(`form_${formId}`);
        if (savedData) {
            const data = JSON.parse(savedData);
            Object.entries(data).forEach(([name, value]) => {
                const field = form.querySelector(`[name="${name}"]`);
                if (field && field.type !== 'password') {
                    field.value = value;
                }
            });
        }
    } catch (error) {
        console.warn('Failed to load saved form data:', error);
    }
}

// ============================================================================
// CLEANUP
// ============================================================================

// Clean up intervals when page unloads
window.addEventListener('beforeunload', function() {
    Object.values(SocraticRAG.intervals).forEach(interval => {
        clearInterval(interval);
    });
});

// ============================================================================
// EXPORT GLOBAL FUNCTIONS
// ============================================================================

window.SocraticRAG.updateChartData = updateChartData;
window.SocraticRAG.showNotification = showNotification;
window.SocraticRAG.refreshActivityFeed = refreshActivityFeed;
window.SocraticRAG.switchConversationRole = switchConversationRole;
