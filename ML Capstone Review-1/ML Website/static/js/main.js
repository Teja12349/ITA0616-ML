// Global helper functions and UI listeners
document.addEventListener('DOMContentLoaded', function () {
    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }

    // Reset Sample Data button listener
    const btnResetSample = document.getElementById('btnResetSample');
    if (btnResetSample) {
        btnResetSample.addEventListener('click', function () {
            btnResetSample.disabled = true;
            btnResetSample.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Resetting...';

            fetch('/api/reset-sample-data', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showAlert('success', data.message);
                        setTimeout(() => window.location.reload(), 800);
                    } else {
                        showAlert('danger', 'Error: ' + data.error);
                    }
                })
                .catch(err => showAlert('danger', 'Failed to reset sample data: ' + err))
                .finally(() => {
                    btnResetSample.disabled = false;
                    btnResetSample.innerHTML = '<i class="fa-solid fa-rotate-right me-1"></i> Reload Sample Data';
                });
        });
    }

    // Reset sample button on dataset page if present
    const btnReloadSampleDataset = document.getElementById('btnReloadSampleDataset');
    if (btnReloadSampleDataset) {
        btnReloadSampleDataset.addEventListener('click', function () {
            btnReloadSampleDataset.disabled = true;
            btnReloadSampleDataset.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Regenerating...';

            fetch('/api/reset-sample-data', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showAlert('success', data.message);
                        setTimeout(() => window.location.reload(), 800);
                    } else {
                        showAlert('danger', 'Error: ' + data.error);
                    }
                })
                .catch(err => showAlert('danger', 'Failed: ' + err))
                .finally(() => {
                    btnReloadSampleDataset.disabled = false;
                    btnReloadSampleDataset.innerHTML = '<i class="fa-solid fa-rotate-right me-1"></i> Regenerate Dataset';
                });
        });
    }
});

function showAlert(type, message) {
    const container = document.getElementById('alertContainer');
    if (!container) return;

    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show border-0 shadow mb-3" role="alert">
            <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    container.innerHTML = alertHtml;
    setTimeout(() => {
        container.innerHTML = '';
    }, 6000);
}
