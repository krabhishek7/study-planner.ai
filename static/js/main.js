// Main JavaScript file for Smart Study Planner

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (alert.classList.contains('alert-dismissible')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });

    // Form validation feedback
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
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
});

// Utility functions
const Utils = {
    // Show loading state on button
    showButtonLoading: function(button, loadingText = 'Loading...') {
        const originalText = button.innerHTML;
        button.setAttribute('data-original-text', originalText);
        button.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span>${loadingText}`;
        button.disabled = true;
        button.classList.add('btn-loading');
    },

    // Hide loading state on button
    hideButtonLoading: function(button) {
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.innerHTML = originalText;
            button.removeAttribute('data-original-text');
        }
        button.disabled = false;
        button.classList.remove('btn-loading');
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    // Create toast container if it doesn't exist
    createToastContainer: function() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    },

    // Format date for display
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    // Calculate days until due date
    daysToDue: function(dueDateString) {
        const today = new Date();
        const dueDate = new Date(dueDateString);
        const diffTime = dueDate - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays;
    },

    // Get urgency class based on days until due
    getUrgencyClass: function(dueDateString) {
        const days = this.daysToDue(dueDateString);
        if (days < 0) return 'text-danger'; // Overdue
        if (days <= 2) return 'text-warning'; // Due soon
        if (days <= 7) return 'text-info'; // Due this week
        return 'text-muted'; // Not urgent
    }
};

// Task management functions
const TaskManager = {
    // Decompose task using AI
    decomposeTask: async function(taskId, buttonElement) {
        Utils.showButtonLoading(buttonElement, 'Processing...');
        
        try {
            const response = await fetch(`/decompose_task/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                Utils.hideButtonLoading(buttonElement);
                buttonElement.innerHTML = '<i class="fas fa-check"></i> Decomposed';
                buttonElement.className = 'btn btn-success btn-sm';
                
                Utils.showToast(`Task successfully decomposed into ${result.subtasks.length} subtasks!`, 'success');
                
                // Reload page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                Utils.hideButtonLoading(buttonElement);
                Utils.showToast(`Error: ${result.error}`, 'danger');
            }
        } catch (error) {
            Utils.hideButtonLoading(buttonElement);
            Utils.showToast('An error occurred while decomposing the task.', 'danger');
            console.error('Error:', error);
        }
    },

    // Load and display subtasks
    viewSubtasks: async function(taskId) {
        try {
            const response = await fetch(`/get_subtasks/${taskId}`);
            const result = await response.json();
            
            if (result.success) {
                const subtasksList = document.getElementById('subtasksList');
                if (subtasksList) {
                    subtasksList.innerHTML = '';
                    
                    result.subtasks.forEach((subtask, index) => {
                        const subtaskElement = document.createElement('div');
                        subtaskElement.className = 'card mb-2';
                        subtaskElement.innerHTML = `
                            <div class="card-body">
                                <h6 class="card-title">${index + 1}. ${subtask.title}</h6>
                                <p class="card-text text-muted">${subtask.description}</p>
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i>Estimated: ${subtask.estimated_time} minutes
                                </small>
                            </div>
                        `;
                        subtasksList.appendChild(subtaskElement);
                    });
                    
                    const modal = new bootstrap.Modal(document.getElementById('subtasksModal'));
                    modal.show();
                }
            } else {
                Utils.showToast(`Error loading subtasks: ${result.error}`, 'danger');
            }
        } catch (error) {
            Utils.showToast('An error occurred while loading subtasks.', 'danger');
            console.error('Error:', error);
        }
    },

    // Mark task as reviewed (spaced repetition)
    reviewTask: async function(taskId, buttonElement) {
        if (buttonElement) Utils.showButtonLoading(buttonElement, 'Reviewing...');
        try {
            const response = await fetch(`/review_task/${taskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const result = await response.json();
            if (result.success) {
                Utils.showToast('Task reviewed! Next review scheduled.', 'success');
                setTimeout(() => window.location.reload(), 1200);
            } else {
                Utils.showToast(result.error || 'Review failed.', 'danger');
            }
        } catch (e) {
            Utils.showToast('Error reviewing task.', 'danger');
        } finally {
            if (buttonElement) Utils.hideButtonLoading(buttonElement);
        }
    },

    // Auto-schedule a task
    autoScheduleTask: async function(taskId, buttonElement) {
        if (buttonElement) Utils.showButtonLoading(buttonElement, 'Scheduling...');
        try {
            const response = await fetch(`/auto_schedule_task/${taskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const result = await response.json();
            if (result.success) {
                Utils.showToast('Task auto-scheduled!', 'success');
                setTimeout(() => window.location.reload(), 1200);
            } else {
                Utils.showToast(result.error || 'Auto-schedule failed.', 'danger');
            }
        } catch (e) {
            Utils.showToast('Error auto-scheduling task.', 'danger');
        } finally {
            if (buttonElement) Utils.hideButtonLoading(buttonElement);
        }
    },

    // Complete a task with difficulty rating
    completeTask: async function(taskId, difficulty, buttonElement) {
        if (buttonElement) Utils.showButtonLoading(buttonElement, 'Completing...');
        try {
            const response = await fetch(`/complete_task/${taskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ difficulty: difficulty })
            });
            const result = await response.json();
            if (result.success) {
                Utils.showToast('Task marked as completed!', 'success');
                setTimeout(() => window.location.reload(), 1200);
            } else {
                Utils.showToast(result.error || 'Complete failed.', 'danger');
            }
        } catch (e) {
            Utils.showToast('Error completing task.', 'danger');
        } finally {
            if (buttonElement) Utils.hideButtonLoading(buttonElement);
        }
    }
};

// Subject management functions
const SubjectManager = {
    // Edit subject
    editSubject: function(id, name, description, color) {
        const nameField = document.getElementById('editName');
        const descField = document.getElementById('editDescription');
        const colorField = document.getElementById('editColor');
        const form = document.getElementById('editSubjectForm');
        
        if (nameField && descField && colorField && form) {
            nameField.value = name;
            descField.value = description;
            colorField.value = color;
            form.action = `/edit_subject/${id}`;
            
            const modal = new bootstrap.Modal(document.getElementById('editSubjectModal'));
            modal.show();
        }
    }
};

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + N: New task
    if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
        event.preventDefault();
        const newTaskButton = document.querySelector('[data-bs-target="#addTaskModal"]');
        if (newTaskButton) {
            newTaskButton.click();
        }
    }
    
    // Ctrl/Cmd + S: New subject
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        const newSubjectButton = document.querySelector('[data-bs-target="#addSubjectModal"]');
        if (newSubjectButton) {
            newSubjectButton.click();
        }
    }
    
    // Escape: Close modals
    if (event.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
});

// Export functions for global use
window.Utils = Utils;
window.TaskManager = TaskManager;
window.SubjectManager = SubjectManager;

// Legacy function names for backwards compatibility
window.decomposeTask = function(taskId) {
    const button = event.target;
    TaskManager.decomposeTask(taskId, button);
};

window.viewSubtasks = function(taskId) {
    TaskManager.viewSubtasks(taskId);
};

window.editSubject = function(id, name, description, color) {
    SubjectManager.editSubject(id, name, description, color);
};

// Modal and button wiring for dashboard actions
window.reviewTask = function(taskId) {
    TaskManager.reviewTask(taskId);
};
window.autoScheduleTask = function(taskId) {
    TaskManager.autoScheduleTask(taskId);
};

// Complete Task Modal logic
let completeTaskId = null;
window.openCompleteModal = function(taskId) {
    completeTaskId = taskId;
    document.getElementById('completeTaskId').value = taskId;
    document.getElementById('difficultyRating').value = '';
    const modal = new bootstrap.Modal(document.getElementById('completeTaskModal'));
    modal.show();
};

document.addEventListener('DOMContentLoaded', function() {
    const completeForm = document.getElementById('completeTaskForm');
    if (completeForm) {
        completeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const taskId = document.getElementById('completeTaskId').value;
            const difficulty = document.getElementById('difficultyRating').value;
            if (!taskId || !difficulty) return;
            TaskManager.completeTask(taskId, difficulty);
            const modal = bootstrap.Modal.getInstance(document.getElementById('completeTaskModal'));
            if (modal) modal.hide();
        });
    }
});

// Modern Smart Study Planner JavaScript
class StudyPlannerApp {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeComponents();
        this.loadDynamicContent();
    }

    bindEvents() {
        // Form submissions with loading states
        document.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Button clicks with smooth feedback
        document.addEventListener('click', this.handleButtonClick.bind(this));
        
        // Auto-save functionality for forms
        this.setupAutoSave();
        
        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    initializeComponents() {
        // Initialize tooltips
        this.initTooltips();
        
        // Initialize date pickers with modern styling
        this.initDatePickers();
        
        // Initialize color pickers
        this.initColorPickers();
        
        // Setup smooth scrolling
        this.setupSmoothScrolling();
    }

    loadDynamicContent() {
        // Load stats and metrics
        this.loadUserStats();
        
        // Load notifications
        this.loadNotifications();
        
        // Setup real-time updates
        this.setupRealTimeUpdates();
    }

    handleFormSubmit(event) {
        const form = event.target;
        if (!form.matches('form[data-async="true"]')) return;

        event.preventDefault();
        this.submitFormAsync(form);
    }

    async submitFormAsync(form) {
        const submitButton = form.querySelector('button[type="submit"]');
        const formData = new FormData(form);
        
        // Show loading state
        Utils.showButtonLoading(submitButton);
        
        try {
            const response = await fetch(form.action, {
                method: form.method || 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                Utils.showToast(result.message || 'Operation completed successfully!', 'success');
                
                // Handle redirect or refresh
                if (result.redirect) {
                    setTimeout(() => window.location.href = result.redirect, 1200);
                } else if (result.reload) {
                    setTimeout(() => window.location.reload(), 1200);
                }
                
                // Reset form if needed
                if (result.reset_form) {
                    form.reset();
                }
            } else {
                Utils.showToast(result.error || 'An error occurred. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            Utils.showToast('Network error. Please check your connection and try again.', 'error');
        } finally {
            Utils.hideButtonLoading(submitButton);
        }
    }

    handleButtonClick(event) {
        const button = event.target.closest('button');
        if (!button) return;

        // Add click animation
        this.addClickAnimation(button);

        // Handle specific button actions
        if (button.dataset.action) {
            event.preventDefault();
            this.handleButtonAction(button);
        }
    }

    addClickAnimation(element) {
        element.style.transform = 'scale(0.95)';
        setTimeout(() => {
            element.style.transform = '';
        }, 150);
    }

    async handleButtonAction(button) {
        const action = button.dataset.action;
        const target = button.dataset.target;
        
        Utils.showButtonLoading(button);

        try {
            switch (action) {
                case 'delete':
                    await this.handleDelete(target, button);
                    break;
                case 'complete':
                    await this.handleComplete(target, button);
                    break;
                case 'schedule':
                    await this.handleSchedule(target, button);
                    break;
                case 'review':
                    await this.handleReview(target, button);
                    break;
                default:
                    console.warn('Unknown action:', action);
            }
        } catch (error) {
            console.error('Action error:', error);
            Utils.showToast('An error occurred. Please try again.', 'error');
        } finally {
            Utils.hideButtonLoading(button);
        }
    }

    async handleDelete(target, button) {
        const confirmed = await this.showConfirmDialog(
            'Are you sure?',
            'This action cannot be undone.',
            'Delete',
            'danger'
        );

        if (!confirmed) return;

        const response = await fetch(`/delete_${target}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();
        
        if (result.success) {
            Utils.showToast('Item deleted successfully.', 'success');
            
            // Animate out the element
            const element = button.closest('.card, .list-group-item, tr');
            if (element) {
                element.style.transition = 'all 0.3s ease';
                element.style.opacity = '0';
                element.style.transform = 'translateX(-20px)';
                setTimeout(() => element.remove(), 300);
            }
        } else {
            Utils.showToast(result.error || 'Delete failed.', 'error');
        }
    }

    async handleComplete(target, button) {
        const response = await fetch(`/complete_${target}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();
        
        if (result.success) {
            Utils.showToast('Task completed! Well done! 🎉', 'success');
            
            // Update UI to show completion
            const card = button.closest('.task-card, .card');
            if (card) {
                card.classList.add('completed');
                button.innerHTML = '<i class="fas fa-check me-1"></i>Completed';
                button.classList.remove('btn-success');
                button.classList.add('btn-outline-success');
                button.disabled = true;
            }
        } else {
            Utils.showToast(result.error || 'Completion failed.', 'error');
        }
    }

    async handleSchedule(target, button) {
        const response = await fetch(`/auto_schedule_${target}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();
        
        if (result.success) {
            Utils.showToast('Task scheduled successfully!', 'success');
            if (result.scheduled_time) {
                const timeDisplay = button.closest('.card').querySelector('.scheduled-time');
                if (timeDisplay) {
                    timeDisplay.textContent = `Scheduled: ${result.scheduled_time}`;
                }
            }
        } else {
            Utils.showToast(result.error || 'Scheduling failed.', 'error');
        }
    }

    async handleReview(target, button) {
        const response = await fetch(`/review_${target}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();
        
        if (result.success) {
            Utils.showToast('Review completed! Next review scheduled.', 'success');
            
            // Update the review button
            button.innerHTML = '<i class="fas fa-check me-1"></i>Reviewed';
            button.classList.remove('btn-info');
            button.classList.add('btn-outline-success');
            button.disabled = true;
        } else {
            Utils.showToast(result.error || 'Review failed.', 'error');
        }
    }

    async showConfirmDialog(title, message, confirmText = 'Confirm', type = 'primary') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-${type}" id="confirmAction">${confirmText}</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            const bsModal = new bootstrap.Modal(modal);
            
            modal.querySelector('#confirmAction').addEventListener('click', () => {
                resolve(true);
                bsModal.hide();
            });

            modal.addEventListener('hidden.bs.modal', () => {
                if (!modal.querySelector('#confirmAction').dataset.clicked) {
                    resolve(false);
                }
                document.body.removeChild(modal);
            });

            modal.querySelector('#confirmAction').addEventListener('click', () => {
                modal.querySelector('#confirmAction').dataset.clicked = 'true';
            });

            bsModal.show();
        });
    }

    setupAutoSave() {
        const autoSaveForms = document.querySelectorAll('form[data-autosave="true"]');
        
        autoSaveForms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            
            inputs.forEach(input => {
                input.addEventListener('change', Utils.debounce(() => {
                    this.autoSaveForm(form);
                }, 1000));
            });
        });
    }

    async autoSaveForm(form) {
        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                this.showAutoSaveIndicator();
            }
        } catch (error) {
            console.error('Auto-save error:', error);
        }
    }

    showAutoSaveIndicator() {
        let indicator = document.querySelector('.autosave-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'autosave-indicator position-fixed';
            indicator.style.cssText = `
                top: 20px;
                right: 20px;
                background: var(--success-color);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.8rem;
                opacity: 0;
                transition: opacity 0.3s ease;
                z-index: 1050;
            `;
            indicator.innerHTML = '<i class="fas fa-save me-1"></i>Saved';
            document.body.appendChild(indicator);
        }

        indicator.style.opacity = '1';
        setTimeout(() => {
            indicator.style.opacity = '0';
        }, 2000);
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Ctrl/Cmd + K for quick search
            if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
                event.preventDefault();
                this.openQuickSearch();
            }

            // Ctrl/Cmd + N for new task
            if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
                event.preventDefault();
                this.openNewTaskModal();
            }

            // Escape to close modals
            if (event.key === 'Escape') {
                const openModals = document.querySelectorAll('.modal.show');
                openModals.forEach(modal => {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    if (bsModal) bsModal.hide();
                });
            }
        });
    }

    openQuickSearch() {
        // Implementation for quick search functionality
        Utils.showToast('Quick search coming soon! 🔍', 'info');
    }

    openNewTaskModal() {
        const newTaskModal = document.querySelector('#addTaskModal');
        if (newTaskModal) {
            const modal = new bootstrap.Modal(newTaskModal);
            modal.show();
        }
    }

    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl, {
                delay: { show: 500, hide: 100 }
            });
        });
    }

    initDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"], input[type="datetime-local"]');
        
        dateInputs.forEach(input => {
            input.addEventListener('focus', () => {
                input.style.borderColor = 'var(--primary-color)';
                input.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
            });

            input.addEventListener('blur', () => {
                input.style.borderColor = '';
                input.style.boxShadow = '';
            });
        });
    }

    initColorPickers() {
        const colorInputs = document.querySelectorAll('input[type="color"]');
        
        colorInputs.forEach(input => {
            input.addEventListener('change', () => {
                const preview = input.nextElementSibling;
                if (preview && preview.classList.contains('color-preview')) {
                    preview.style.backgroundColor = input.value;
                }
            });
        });
    }

    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
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
    }

    async loadUserStats() {
        try {
            const response = await fetch('/api/user_stats');
            const stats = await response.json();
            
            if (stats.success) {
                this.updateStatsDisplay(stats.data);
            }
        } catch (error) {
            console.error('Error loading user stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        // Update various stat displays throughout the app
        const statElements = {
            'tasksCompleted': stats.tasks_completed,
            'avgDifficulty': stats.avg_difficulty,
            'reviewStreak': stats.review_streak,
            'studyStreak': stats.study_streak
        };

        Object.entries(statElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value || '-';
            }
        });
    }

    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const notifications = await response.json();
            
            if (notifications.success) {
                this.displayNotifications(notifications.data);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    displayNotifications(notifications) {
        const container = document.querySelector('.notifications-container');
        if (!container) return;

        notifications.forEach(notification => {
            const alertClass = notification.type === 'success' ? 'alert-success' :
                             notification.type === 'warning' ? 'alert-warning' :
                             notification.type === 'error' ? 'alert-danger' : 'alert-info';

            const notificationElement = document.createElement('div');
            notificationElement.className = `alert ${alertClass} alert-dismissible fade show`;
            notificationElement.innerHTML = `
                ${notification.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            container.appendChild(notificationElement);
        });
    }

    setupRealTimeUpdates() {
        // Set up periodic updates for dynamic content
        setInterval(() => {
            this.loadUserStats();
        }, 60000); // Update stats every minute

        setInterval(() => {
            this.loadNotifications();
        }, 300000); // Check for notifications every 5 minutes
    }

    // Progress tracking and animations
    animateProgressBar(element, targetPercentage, duration = 1000) {
        const startTime = Date.now();
        const startWidth = parseFloat(element.style.width) || 0;
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const currentWidth = startWidth + (targetPercentage - startWidth) * progress;
            
            element.style.width = `${currentWidth}%`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    // Enhanced error handling
    handleError(error, context = 'Application') {
        console.error(`${context} Error:`, error);
        
        // Show user-friendly error message
        Utils.showToast(
            'Something went wrong. Please try again or contact support if the problem persists.',
            'error'
        );
        
        // Optionally send error to logging service
        // this.logError(error, context);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.StudyPlannerApp = new StudyPlannerApp();
    
    // Global error handler
    window.addEventListener('error', (event) => {
        window.StudyPlannerApp.handleError(event.error, 'Global');
    });
    
    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
        window.StudyPlannerApp.handleError(event.reason, 'Promise');
    });
});

// Export for use in other scripts
window.StudyPlanner = StudyPlannerApp; 