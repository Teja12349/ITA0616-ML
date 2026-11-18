let charts = {};

document.addEventListener('DOMContentLoaded', function () {
    initModule1Page();

    // Upload Form Listener
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const fileInput = document.getElementById('csvFileInput');
            if (!fileInput.files.length) return;

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            const btnSubmit = document.getElementById('btnUploadSubmit');
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Uploading...';

            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message);
                    document.getElementById('activeFilename').innerText = data.filename;
                    document.getElementById('statRecordCount').innerText = data.record_count;
                    document.getElementById('statColCount').innerText = data.column_count;
                    initModule1Page();
                } else {
                    showAlert('danger', data.error);
                }
            })
            .catch(err => showAlert('danger', 'Upload failed: ' + err))
            .finally(() => {
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = '<i class="fa-solid fa-upload me-1"></i> Upload Dataset';
            });
        });
    }

    // Run Preprocessing button
    const btnRunPrep = document.getElementById('btnRunPreprocessing');
    if (btnRunPrep) {
        btnRunPrep.addEventListener('click', function () {
            btnRunPrep.disabled = true;
            btnRunPrep.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Processing...';

            fetch('/api/preprocess?fill_strategy=mean&outlier_method=iqr&scale_method=minmax')
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showAlert('success', 'Preprocessing completed! Noise smoothing and scaling applied.');
                        updatePreprocessingStats(data.stats);
                    } else {
                        showAlert('danger', data.error);
                    }
                })
                .catch(err => showAlert('danger', 'Preprocessing error: ' + err))
                .finally(() => {
                    btnRunPrep.disabled = false;
                    btnRunPrep.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles me-1"></i> Execute Preprocessing';
                });
        });
    }

    // Sample Data button inside upload box
    const btnLoadSampleModule1 = document.getElementById('btnLoadSampleModule1');
    if (btnLoadSampleModule1) {
        btnLoadSampleModule1.addEventListener('click', function () {
            fetch('/api/reset-sample-data', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showAlert('success', 'Loaded sample pump dataset with 800 records.');
                        document.getElementById('activeFilename').innerText = data.filename;
                        document.getElementById('statRecordCount').innerText = data.record_count;
                        document.getElementById('statColCount').innerText = data.column_count;
                        initModule1Page();
                    }
                });
        });
    }
});

function initModule1Page() {
    fetchFluidAnalysis();
    fetchFeatureEngineering();
    fetchPreprocessingStats();
}

function fetchPreprocessingStats() {
    fetch('/api/preprocess')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                updatePreprocessingStats(data.stats);
            }
        });
}

function updatePreprocessingStats(stats) {
    document.getElementById('prepMissingCount').innerText = stats.missing_values_found || 0;
    document.getElementById('prepDuplicateCount').innerText = stats.duplicates_removed || 0;
    document.getElementById('prepOutlierCount').innerText = stats.outliers_handled || 0;
    document.getElementById('statRecordCount').innerText = stats.final_rows || '--';
}

function fetchFluidAnalysis() {
    fetch('/api/fluid-analysis')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const m = data.metrics;
                document.getElementById('fluidPressureDiff').innerText = m.pressure_difference || '--';
                document.getElementById('fluidFlowStd').innerText = m.flow_stats ? m.flow_stats.std : '--';
                document.getElementById('fluidTempMean').innerText = m.temp_stats ? m.temp_stats.mean : '--';
                document.getElementById('fluidHeadMean').innerText = m.pump_head_stats ? m.pump_head_stats.mean : '--';
                document.getElementById('fluidVibRMS').innerText = m.vibration_rms || '--';
                document.getElementById('fluidOpCondition').innerText = m.operating_condition || 'NORMAL';

                renderFluidCharts(data.chart_data);
            }
        });
}

function fetchFeatureEngineering() {
    fetch('/api/feature-engineering')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.getElementById('featureCountBadge').innerText = `${data.feature_count} Features Extracted`;
                renderFeatureTable(data.table_preview);
            }
        });
}

function renderFeatureTable(records) {
    const tbody = document.getElementById('featureTableBody');
    if (!tbody) return;

    if (!records || !records.length) {
        tbody.innerHTML = `<tr><td colspan="11" class="text-center py-3 text-secondary">No engineered features available.</td></tr>`;
        return;
    }

    let html = '';
    records.forEach(r => {
        let statusBadge = r.failure_status === 0 ? '<span class="badge badge-normal">0: NORMAL</span>' :
                          (r.failure_status === 1 ? '<span class="badge badge-warning">1: WARN</span>' : '<span class="badge badge-failure">2: FAIL</span>');

        html += `
            <tr>
                <td>${r.index}</td>
                <td class="small font-mono text-secondary">${r.timestamp}</td>
                <td class="text-cyan fw-bold">${r.mean_pressure}</td>
                <td>${r.pressure_diff}</td>
                <td>${r.flow_variation}</td>
                <td class="text-amber">${r.temperature_rise}</td>
                <td class="text-rose fw-bold">${r.vibration_rms}</td>
                <td>${r.rpm_variation}</td>
                <td>${r.motor_current_var}</td>
                <td>${r.operating_hours}</td>
                <td>${statusBadge}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function renderFluidCharts(chartData) {
    if (!chartData || !chartData.timestamps) return;

    const labels = chartData.timestamps.map((t, idx) => `T${idx+1}`);

    // Standard chart options
    const chartOptions = (title, color) => ({
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', maxTicksLimit: 8 } },
            y: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#94a3b8' } }
        }
    });

    // Destroy existing instances
    Object.keys(charts).forEach(key => {
        if (charts[key]) charts[key].destroy();
    });

    // 1. Pressure vs Time
    charts.pressure = new Chart(document.getElementById('chartPressure'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{ label: 'Pressure (bar)', data: chartData.pressure, borderColor: '#00f2fe', backgroundColor: 'rgba(0, 242, 254, 0.1)', fill: true, tension: 0.3, pointRadius: 0 }]
        },
        options: chartOptions('Pressure', '#00f2fe')
    });

    // 2. Flow Rate vs Time
    charts.flow = new Chart(document.getElementById('chartFlow'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{ label: 'Flow Rate (L/min)', data: chartData.flow_rate, borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true, tension: 0.3, pointRadius: 0 }]
        },
        options: chartOptions('Flow Rate', '#3b82f6')
    });

    // 3. Temperature vs Time
    charts.temp = new Chart(document.getElementById('chartTemp'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{ label: 'Temperature (°C)', data: chartData.temperature, borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', fill: true, tension: 0.3, pointRadius: 0 }]
        },
        options: chartOptions('Temperature', '#f59e0b')
    });

    // 4. Vibration vs Time
    charts.vib = new Chart(document.getElementById('chartVib'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{ label: 'Vibration (mm/s)', data: chartData.vibration, borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', fill: true, tension: 0.3, pointRadius: 0 }]
        },
        options: chartOptions('Vibration', '#ef4444')
    });

    // 5. RPM vs Time
    charts.rpm = new Chart(document.getElementById('chartRPM'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{ label: 'RPM', data: chartData.rpm, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.3, pointRadius: 0 }]
        },
        options: chartOptions('RPM', '#10b981')
    });

    // 6. Pressure vs Flow Rate (Pump Curve Scatter)
    const scatterData = chartData.pressure_vs_flow || [];
    charts.pumpCurve = new Chart(document.getElementById('chartPumpCurve'), {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Head / Flow Characteristic',
                data: scatterData,
                backgroundColor: '#f59e0b',
                borderColor: '#f59e0b',
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { title: { display: true, text: 'Flow Rate (L/min)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                y: { title: { display: true, text: 'Pressure (bar)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}
