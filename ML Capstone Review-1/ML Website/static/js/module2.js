let chartComparison = null;

document.addEventListener('DOMContentLoaded', function () {
    loadExistingModelResults();

    // Train Model Button Listener
    const btnTrain = document.getElementById('btnTrainModel');
    if (btnTrain) {
        btnTrain.addEventListener('click', function () {
            const algo = document.getElementById('selectModelAlgo').value;
            btnTrain.disabled = true;
            btnTrain.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Training Model...';

            fetch('/api/train-model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_type: algo })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const r = data.results;
                    showAlert('success', `Successfully trained ${r.model_name} on ${r.train_count} samples and evaluated on ${r.test_count} samples.`);
                    
                    // Show fallback notice if present
                    const alertBox = document.getElementById('fallbackAlertBox');
                    if (r.fallback_notice) {
                        document.getElementById('fallbackNoticeText').innerText = r.fallback_notice;
                        alertBox.classList.remove('d-none');
                    } else {
                        alertBox.classList.add('d-none');
                    }

                    updateModelResultsUI(r);
                    loadExistingModelResults(); // refresh comparison chart
                } else {
                    showAlert('danger', data.error);
                }
            })
            .catch(err => showAlert('danger', 'Model training error: ' + err))
            .finally(() => {
                btnTrain.disabled = false;
                btnTrain.innerHTML = '<i class="fa-solid fa-play me-2"></i>Train & Evaluate Model';
            });
        });
    }

    // Prediction Form Submit Listener
    const predForm = document.getElementById('predictionForm');
    if (predForm) {
        predForm.addEventListener('submit', function (e) {
            e.preventDefault();
            
            const payload = {
                pressure: parseFloat(document.getElementById('inputPressure').value),
                flow_rate: parseFloat(document.getElementById('inputFlow').value),
                temperature: parseFloat(document.getElementById('inputTemp').value),
                vibration: parseFloat(document.getElementById('inputVibration').value),
                rpm: parseFloat(document.getElementById('inputRPM').value),
                motor_current: parseFloat(document.getElementById('inputCurrent').value),
                pump_head: parseFloat(document.getElementById('inputHead').value),
                operating_hours: parseFloat(document.getElementById('inputHours').value)
            };

            const btnPredict = document.getElementById('btnPredictSubmit');
            btnPredict.disabled = true;
            btnPredict.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Computing ML Prediction...';

            fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    displayPredictionResult(data.prediction);
                } else {
                    showAlert('danger', data.error);
                }
            })
            .catch(err => showAlert('danger', 'Prediction failed: ' + err))
            .finally(() => {
                btnPredict.disabled = false;
                btnPredict.innerHTML = '<i class="fa-solid fa-microchip me-2"></i>PREDICT EQUIPMENT CONDITION';
            });
        });
    }
});

function loadExistingModelResults() {
    fetch('/api/model-results')
        .then(res => res.json())
        .then(data => {
            if (data.success && data.models && data.models.length > 0) {
                const latest = data.models[0];
                updateModelResultsUI({
                    model_name: latest.model_name,
                    metrics: {
                        accuracy: latest.accuracy,
                        precision: latest.precision,
                        recall: latest.recall,
                        f1_score: latest.f1_score
                    },
                    confusion_matrix: latest.confusion_matrix
                });

                renderComparisonChart(data.models);
            } else {
                // Trigger auto training on first visit
                document.getElementById('btnTrainModel').click();
            }
        });
}

function updateModelResultsUI(r) {
    document.getElementById('activeModelLabel').innerText = r.model_name;
    document.getElementById('metricAccuracy').innerText = (r.metrics.accuracy * 100).toFixed(1) + '%';
    document.getElementById('metricPrecision').innerText = (r.metrics.precision * 100).toFixed(1) + '%';
    document.getElementById('metricRecall').innerText = (r.metrics.recall * 100).toFixed(1) + '%';
    document.getElementById('metricF1').innerText = (r.metrics.f1_score * 100).toFixed(1) + '%';

    // Confusion Matrix (3x3)
    const cm = r.confusion_matrix;
    if (cm && cm.length === 3) {
        document.getElementById('cm-0-0').innerText = cm[0][0];
        document.getElementById('cm-0-1').innerText = cm[0][1];
        document.getElementById('cm-0-2').innerText = cm[0][2];

        document.getElementById('cm-1-0').innerText = cm[1][0];
        document.getElementById('cm-1-1').innerText = cm[1][1];
        document.getElementById('cm-1-2').innerText = cm[1][2];

        document.getElementById('cm-2-0').innerText = cm[2][0];
        document.getElementById('cm-2-1').innerText = cm[2][1];
        document.getElementById('cm-2-2').innerText = cm[2][2];
    }
}

function displayPredictionResult(pred) {
    const status = pred.predicted_status;
    const risk = pred.risk_score;

    const statusDisplay = document.getElementById('predStatusDisplay');
    let badgeClass = 'badge-normal';
    let riskColorClass = 'bg-emerald';

    if (status === 'WARNING') {
        badgeClass = 'badge-warning';
        riskColorClass = 'bg-warning';
    } else if (status === 'POTENTIAL FAILURE') {
        badgeClass = 'badge-failure';
        riskColorClass = 'bg-danger';
    }

    statusDisplay.innerHTML = `<span class="badge ${badgeClass} px-4 py-2" style="font-size: 1.1rem;">${status}</span>`;

    document.getElementById('predRiskScore').innerText = risk.toFixed(1) + '%';
    const riskBar = document.getElementById('predRiskBar');
    riskBar.style.width = Math.min(100, Math.max(5, risk)) + '%';
    riskBar.className = `progress-bar ${riskColorClass}`;

    document.getElementById('predRecommendationText').innerText = pred.recommendation;

    // Parameter factors
    const factorsList = document.getElementById('predFactorsList');
    if (pred.contributing_factors && pred.contributing_factors.length) {
        let html = '';
        pred.contributing_factors.forEach(factor => {
            const isOk = factor.includes('within acceptable');
            const icon = isOk ? '<i class="fa-solid fa-check text-emerald me-2"></i>' : '<i class="fa-solid fa-triangle-exclamation text-amber me-2"></i>';
            html += `<li>${icon}${factor}</li>`;
        });
        factorsList.innerHTML = html;
    }
}

function renderComparisonChart(models) {
    const ctx = document.getElementById('chartModelComparison');
    if (!ctx) return;

    const labels = models.map(m => m.model_name);
    const accuracyData = models.map(m => (m.accuracy * 100).toFixed(1));
    const f1Data = models.map(m => (m.f1_score * 100).toFixed(1));

    if (chartComparison) chartComparison.destroy();

    chartComparison = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                { label: 'Accuracy %', data: accuracyData, backgroundColor: '#00f2fe' },
                { label: 'F1 Score %', data: f1Data, backgroundColor: '#10b981' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8' } }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                y: { min: 50, max: 100, grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}
