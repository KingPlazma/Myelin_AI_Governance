// MYELIN API Demo JavaScript

const API_BASE_URL = 'http://localhost:8000';

// Utility function to show loader
function showLoader(loaderId) {
    document.getElementById(loaderId).classList.add('active');
}

// Utility function to hide loader
function hideLoader(loaderId) {
    document.getElementById(loaderId).classList.remove('active');
}

// Utility function to display results
function displayResult(resultId, data, type = 'success') {
    const resultBox = document.getElementById(resultId);
    resultBox.className = 'result-box show ' + type;

    let html = '';

    // Check if it's an error
    if (data.error || data.status === 'error') {
        html = `
            <div class="result-header">
                <div class="result-title">❌ Error</div>
            </div>
            <div class="detail-item">
                <strong>Error:</strong> ${data.error || data.detail || 'Unknown error occurred'}
            </div>
        `;
        resultBox.innerHTML = html;
        return;
    }

    // Format based on audit type
    if (data.overall) {
        // Comprehensive or ML audit
        const decision = data.overall.decision || data.overall.verdict || 'UNKNOWN';
        const riskLevel = data.overall.risk_level || 'UNKNOWN';
        const riskScore = data.overall.risk_score || data.overall.fairness_score || 0;

        let badgeClass = 'allow';
        if (decision === 'BLOCK' || decision === 'FAIL') badgeClass = 'block';
        else if (decision === 'WARN') badgeClass = 'warn';
        else if (decision === 'REVIEW') badgeClass = 'review';
        else if (decision === 'PASS') badgeClass = 'pass';

        html = `
            <div class="result-header">
                <div class="result-title">📊 Audit Results</div>
                <div class="result-badge ${badgeClass}">${decision}</div>
            </div>
            <div class="result-metrics">
                <div class="metric">
                    <div class="metric-label">Risk Level</div>
                    <div class="metric-value">${riskLevel}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Risk Score</div>
                    <div class="metric-value">${(riskScore * 100).toFixed(1)}%</div>
                </div>
            </div>
        `;

        // Add risk factors if present
        if (data.overall.risk_factors && data.overall.risk_factors.length > 0) {
            html += '<div class="result-details">';
            html += '<div class="metric-label">Risk Factors:</div>';
            data.overall.risk_factors.forEach(factor => {
                html += `<div class="detail-item">⚠️ ${factor}</div>`;
            });
            html += '</div>';
        }

        // Add pillar summaries for comprehensive audit
        if (data.pillars) {
            html += '<div class="result-details" style="margin-top: 20px;">';
            html += '<div class="metric-label">Pillar Results:</div>';

            Object.keys(data.pillars).forEach(pillar => {
                const pillarData = data.pillars[pillar];
                if (pillarData.status === 'success' && pillarData.report) {
                    const report = pillarData.report;
                    let pillarInfo = '';

                    if (pillar === 'toxicity') {
                        pillarInfo = `Score: ${report.toxicity_score}, Decision: ${report.decision}`;
                    } else if (pillar === 'governance') {
                        pillarInfo = `Risk: ${(report.governance_risk_score * 100).toFixed(1)}%`;
                    } else if (pillar === 'factual') {
                        pillarInfo = `Score: ${pillarData.final_score}`;
                    } else if (pillar === 'bias') {
                        pillarInfo = `Bias Index: ${report?.global_bias_index || 0}`;
                    }

                    html += `<div class="detail-item"><strong>${pillar.toUpperCase()}:</strong> ${pillarInfo}</div>`;
                }
            });
            html += '</div>';
        }

    } else if (data.report) {
        // Individual pillar audit
        const report = data.report;

        if (report.toxicity_score !== undefined) {
            // Toxicity report
            const decision = report.decision || 'UNKNOWN';
            let badgeClass = 'allow';
            if (decision === 'BLOCK') badgeClass = 'block';
            else if (decision === 'WARN') badgeClass = 'warn';

            html = `
                <div class="result-header">
                    <div class="result-title">⚠️ Toxicity Analysis</div>
                    <div class="result-badge ${badgeClass}">${decision}</div>
                </div>
                <div class="result-metrics">
                    <div class="metric">
                        <div class="metric-label">Toxicity Score</div>
                        <div class="metric-value">${report.toxicity_score}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Risk Level</div>
                        <div class="metric-value">${report.risk_level}</div>
                    </div>
                </div>
            `;

            if (report.violated_categories && report.violated_categories.length > 0) {
                html += '<div class="result-details">';
                html += '<div class="metric-label">Violated Categories:</div>';
                report.violated_categories.forEach(cat => {
                    html += `<div class="detail-item">⚠️ ${cat}</div>`;
                });
                html += '</div>';
            }

        } else if (report.governance_risk_score !== undefined) {
            // Governance report
            html = `
                <div class="result-header">
                    <div class="result-title">🛡️ Governance Analysis</div>
                </div>
                <div class="result-metrics">
                    <div class="metric">
                        <div class="metric-label">Risk Score</div>
                        <div class="metric-value">${(report.governance_risk_score * 100).toFixed(1)}%</div>
                    </div>
                </div>
            `;

            if (report.details && report.details.length > 0) {
                const violations = report.details.filter(d => d.violation);
                if (violations.length > 0) {
                    html += '<div class="result-details">';
                    html += '<div class="metric-label">Violations Found:</div>';
                    violations.forEach(v => {
                        html += `<div class="detail-item"><strong>${v.rule_name}:</strong> ${v.reason}</div>`;
                    });
                    html += '</div>';
                }
            }
        }

    } else if (data.final_score !== undefined) {
        // Factual check report
        html = `
            <div class="result-header">
                <div class="result-title">✓ Factual Verification</div>
            </div>
            <div class="result-metrics">
                <div class="metric">
                    <div class="metric-label">Factual Score</div>
                    <div class="metric-value">${(data.final_score * 100).toFixed(1)}%</div>
                </div>
            </div>
        `;

        if (data.meta_decision) {
            html += '<div class="result-details">';
            html += '<div class="metric-label">Assessment:</div>';
            html += `<div class="detail-item">${JSON.stringify(data.meta_decision, null, 2)}</div>`;
            html += '</div>';
        }
    }

    resultBox.innerHTML = html;
}

// Test Conversation Audit
async function testConversation() {
    const userInput = document.getElementById('conv-user').value;
    const botResponse = document.getElementById('conv-bot').value;
    const sourceText = document.getElementById('conv-source').value;

    if (!userInput || !botResponse) {
        alert('Please fill in user input and bot response');
        return;
    }

    showLoader('conv-loader');

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/audit/conversation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_input: userInput,
                bot_response: botResponse,
                source_text: sourceText || null
            })
        });

        const data = await response.json();

        if (!response.ok) {
            displayResult('conv-result', { error: data.detail || 'API request failed' }, 'error');
        } else {
            const riskLevel = data.overall?.risk_level?.toLowerCase() || 'low';
            displayResult('conv-result', data, riskLevel === 'critical' ? 'critical' : riskLevel === 'high' ? 'error' : riskLevel === 'medium' ? 'warning' : 'success');
        }
    } catch (error) {
        displayResult('conv-result', { error: `Failed to connect to API: ${error.message}. Make sure the server is running on ${API_BASE_URL}` }, 'error');
    } finally {
        hideLoader('conv-loader');
    }
}

// Test Toxicity Audit
async function testToxicity() {
    const userInput = document.getElementById('tox-user').value;
    const botResponse = document.getElementById('tox-bot').value;

    if (!userInput || !botResponse) {
        alert('Please fill in both fields');
        return;
    }

    showLoader('tox-loader');

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/audit/toxicity`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_input: userInput,
                bot_response: botResponse
            })
        });

        const data = await response.json();

        if (!response.ok) {
            displayResult('tox-result', { error: data.detail || 'API request failed' }, 'error');
        } else {
            const decision = data.report?.decision?.toLowerCase() || 'allow';
            displayResult('tox-result', data, decision === 'block' ? 'critical' : decision === 'warn' ? 'warning' : 'success');
        }
    } catch (error) {
        displayResult('tox-result', { error: `Failed to connect to API: ${error.message}` }, 'error');
    } finally {
        hideLoader('tox-loader');
    }
}

// Test Factual Audit
async function testFactual() {
    const modelOutput = document.getElementById('fact-output').value;
    const sourceText = document.getElementById('fact-source').value;

    if (!modelOutput) {
        alert('Please enter AI output to verify');
        return;
    }

    showLoader('fact-loader');

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/audit/factual`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model_output: modelOutput,
                source_text: sourceText || null
            })
        });

        const data = await response.json();

        if (!response.ok) {
            displayResult('fact-result', { error: data.detail || 'API request failed' }, 'error');
        } else {
            const score = data.final_score || 0;
            displayResult('fact-result', data, score > 0.7 ? 'success' : score > 0.4 ? 'warning' : 'error');
        }
    } catch (error) {
        displayResult('fact-result', { error: `Failed to connect to API: ${error.message}` }, 'error');
    } finally {
        hideLoader('fact-loader');
    }
}

// Test Fairness Audit
async function testFairness() {
    const yTrueStr = document.getElementById('fair-true').value;
    const yPredStr = document.getElementById('fair-pred').value;
    const sensStr = document.getElementById('fair-sens').value;

    if (!yTrueStr || !yPredStr || !sensStr) {
        alert('Please fill in all fields');
        return;
    }

    // Parse comma-separated values
    const yTrue = yTrueStr.split(',').map(v => parseInt(v.trim()));
    const yPred = yPredStr.split(',').map(v => parseInt(v.trim()));
    const sensitive = sensStr.split(',').map(v => parseInt(v.trim()));

    // Validate
    if (yTrue.length !== yPred.length || yTrue.length !== sensitive.length) {
        alert('All arrays must have the same length');
        return;
    }

    if (yTrue.some(v => v !== 0 && v !== 1) || yPred.some(v => v !== 0 && v !== 1) || sensitive.some(v => v !== 0 && v !== 1)) {
        alert('All values must be 0 or 1');
        return;
    }

    showLoader('fair-loader');

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/audit/fairness`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                y_true: yTrue,
                y_pred: yPred,
                sensitive: sensitive
            })
        });

        const data = await response.json();

        if (!response.ok) {
            displayResult('fair-result', { error: data.detail || 'API request failed' }, 'error');
        } else {
            const verdict = data.overall?.verdict?.toLowerCase() || 'unknown';
            displayResult('fair-result', data, verdict === 'pass' ? 'success' : 'error');
        }
    } catch (error) {
        displayResult('fair-result', { error: `Failed to connect to API: ${error.message}` }, 'error');
    } finally {
        hideLoader('fair-loader');
    }
}

// Generate API Key
async function generateApiKey() {
    showLoader('key-loader');
    const resultBox = document.getElementById('key-result');
    resultBox.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/generate_key`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (!response.ok) {
            alert('Failed to generate key: ' + (data.detail || 'Unknown error'));
        } else {
            resultBox.style.display = 'block';
            resultBox.innerHTML = `
                <div class="result-header">
                    <div class="result-title">🔑 API Key Generated</div>
                    <div class="result-badge pass">ACTIVE</div>
                </div>
                <div class="key-display" style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin: 10px 0; font-family: monospace; font-size: 1.2em; color: #00ffcc; text-align: center; border: 1px solid rgba(0,255,204,0.3);">
                    ${data.api_key}
                </div>
                <div class="result-metrics">
                    <div class="metric">
                        <div class="metric-label">Rules Enabled</div>
                        <div class="metric-value">${data.rules_enabled}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Permissions</div>
                        <div class="metric-value" style="font-size: 0.8em">${data.permissions.join(', ')}</div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        alert('Failed to connect to API: ' + error.message);
    } finally {
        hideLoader('key-loader');
    }
}
