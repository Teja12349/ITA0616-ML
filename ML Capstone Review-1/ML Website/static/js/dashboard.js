let chartDashboardTrends = null;
let chartStatusPie = null;

document.addEventListener('DOMContentLoaded', function () {
    loadDashboardData();

    const btnRefresh = document.getElementById('btnRefreshDashboard');
    if (btnRefresh) {
        btnRefresh.addEventListener('click', function () {
            btnRefresh.disabled = true;
            btnRefresh.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Refreshing...';
            loadDashboardData().finally(() => {
                btnRefresh.disabled = false;
                btnRefresh.innerHTML = '<i class="fa-solid fa-arrows-rotate me-1"></i> Refresh Monitoring';
            });
        });
    }
});

function loadDashboardData() {
    return fetch('/api/dashboard-summary')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                updateDashboardKPIs(data.kpis, data.latest_model);
                renderDashboardTrends(data.chart_data);
                renderStatusPieChart(data.status_distribution);
                renderRecentPredictionsTable(data.recent_predictions);
            }
        })
        .catch(err => console.error('Dashboard data error:', err));
}

function updateDashboardKPIs(kpis, latestModel) {
    const statusVal = document.getElementById('dashStatusValue');
    const statusCard = document.getElementById('kpiStatusCard');
    const statusSub = document.getElementById('dashStatusSub');

    statusVal.innerText = kpis.current_status;

    if (kpis.current_status === 'NORMAL') {
        statusVal.className = 'kpi-value text-emerald';
        statusCard.className = 'kpi-card kpi-success';
        statusSub.innerText = 'Operating nominal parameters';
    } else if (kpis.current_status === 'WARNING') {
        statusVal.className = 'kpi-value text-amber';
        statusCard.className = 'kpi-card kpi-warning';
        statusSub.innerText = 'Elevated thermal / vibration signature';
    } else {
        statusVal.className = 'kpi-value text-rose';
        statusCard.className = 'kpi-card kpi-danger';
        statusSub.innerText = 'High failure risk detected';
    }

    // Risk
    document.getElementById('dashRiskValue').innerText = kpis.risk_estimate.toFixed(1) + '%';
    const riskBar = document.getElementById('dashRiskBar');
    riskBar.style.width = Math.min(100, kpis.risk_estimate) + '%';
    if (kpis.risk_estimate > 70) riskBar.className = 'progress-bar bg-danger';
    else if (kpis.risk_estimate > 35) riskBar.className = 'progress-bar bg-warning';
    else riskBar.className = 'progress-bar bg-cyan';

    document.getElementById('dashPressureValue').innerText = kpis.latest_pressure + ' bar';
    document.getElementById('dashFlowValue').innerText = kpis.latest_flow + ' L/m';
    document.getElementById('dashTempValue').innerText = kpis.latest_temp + ' °C';
    document.getElementById('dashVibValue').innerText = kpis.latest_vibration + ' mm/s';
    document.getElementById('dashRPMValue').innerText = kpis.latest_rpm;
    document.getElementById('dashRecordCount').innerText = kpis.record_count;

    if (latestModel) {
        document.getElementById('dashModelName').innerText = latestModel.model_name;
    }
}

function renderDashboardTrends(chartData) {
    const ctx = document.getElementById('chartDashboardTrends');
    if (!ctx || !chartData || !chartData.timestamps) return;

    const labels = chartData.timestamps.map((t, idx) => `T${idx+1}`);

    if (chartDashboardTrends) chartDashboardTrends.destroy();

    chartDashboardTrends = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                { label: 'Pressure (bar)', data: chartData.pressure, borderColor: '#00f2fe', tension: 0.3, pointRadius: 0 },
                { label: 'Temp (°C)', data: chartData.temperature, borderColor: '#f59e0b', tension: 0.3, pointRadius: 0 },
                { label: 'Vibration (mm/s)', data: chartData.vibration, borderColor: '#ef4444', tension: 0.3, pointRadius: 0 },
                { label: 'Flow Rate (x10 L/m)', data: chartData.flow_rate.map(v => v / 10.0), borderColor: '#3b82f6', tension: 0.3, pointRadius: 0 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8' } }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', maxTicksLimit: 10 } },
                y: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

function renderStatusPieChart(dist) {
    const ctx = document.getElementById('chartStatusPie');
    if (!ctx || !dist) return;

    if (chartStatusPie) chartStatusPie.destroy();

    chartStatusPie = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['NORMAL', 'WARNING', 'POTENTIAL FAILURE'],
            datasets: [{
                data: [dist.NORMAL || 0, dist.WARNING || 0, dist.POTENTIAL_FAILURE || 0],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 } } }
            }
        }
    });
}

function renderRecentPredictionsTable(predictions) {
    const tbody = document.getElementById('recentPredictionsBody');
    if (!tbody) return;

    if (!predictions || !predictions.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-3 text-secondary">No predictions recorded yet. Run a prediction in Module 2.</td></tr>`;
        return;
    }

    let html = '';
    predictions.forEach(p => {
        let badgeClass = 'badge-normal';
        if (p.predicted_status === 'WARNING') badgeClass = 'badge-warning';
        else if (p.predicted_status === 'POTENTIAL FAILURE') badgeClass = 'badge-failure';

        html += `
            <tr>
                <td class="small font-mono text-secondary">${p.timestamp}</td>
                <td class="text-cyan">${p.pressure} bar</td>
                <td>${p.flow_rate} L/min</td>
                <td class="text-amber">${p.temperature} °C</td>
                <td class="text-rose">${p.vibration} mm/s</td>
                <td><span class="badge ${badgeClass}">${p.predicted_status}</span></td>
                <td class="fw-bold text-white">${p.risk_score}%</td>
                <td class="small text-secondary text-truncate" style="max-width: 250px;">${p.recommendation}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}
