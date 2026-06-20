let isOverviewMode = false;
let globalMatches = [];

document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('url-input');
    const startBtn = document.getElementById('start-btn');
    const modeToggle = document.getElementById('mode-toggle');
    const labelEinzel = document.getElementById('label-einzel');
    const labelUebersicht = document.getElementById('label-uebersicht');
    const urlLabel = document.getElementById('url-label');
    const progressContainer = document.getElementById('progress-container');
    const resultsContainer = document.getElementById('results-container');

    // Enable button based on input
    urlInput.addEventListener('input', () => {
        startBtn.disabled = urlInput.value.trim().length < 5;
    });

    // Mode Toggle
    modeToggle.addEventListener('change', (e) => {
        isOverviewMode = e.target.checked;
        if (isOverviewMode) {
            labelUebersicht.classList.add('active');
            labelEinzel.classList.remove('active');
            urlLabel.innerText = "Einen Übersichts-Link einfügen:";
        } else {
            labelEinzel.classList.add('active');
            labelUebersicht.classList.remove('active');
            urlLabel.innerText = "Einzelne Spiel-Links hier einfügen:";
        }
    });

    startBtn.addEventListener('click', async () => {
        const text = urlInput.value.trim();
        const urls = text.split('\n').map(u => u.trim()).filter(u => u.startsWith('http'));

        if (urls.length === 0) return;

        startBtn.disabled = true;
        progressContainer.style.display = 'block';
        document.getElementById('progress-fill').classList.remove('determinate');
        document.getElementById('status-text').innerText = 'Arbeite...';
        resultsContainer.innerHTML = '';

        if (isOverviewMode) {
            // Call Python to extract matches
            const url = urls[0];
            try {
                const response = await window.pywebview.api.get_matches_from_overview(url);
                if (response.success) {
                    showSelectionModal(response.matches);
                } else {
                    showError(response.error);
                }
            } catch (err) {
                showError("Verbindungsfehler zur Python-API.");
            }
        } else {
            // Calculate directly
            calculateMatches(urls);
        }
    });

    // Modals Setup
    document.getElementById('cancel-selection-btn').addEventListener('click', () => {
        document.getElementById('selection-modal').style.display = 'none';
        resetUI();
    });

    document.getElementById('select-all').addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('.match-cb');
        checkboxes.forEach(cb => cb.checked = e.target.checked);
    });

    document.getElementById('confirm-selection-btn').addEventListener('click', () => {
        const checkboxes = document.querySelectorAll('.match-cb:checked');
        const selectedUrls = Array.from(checkboxes).map(cb => cb.value);

        if (selectedUrls.length > 0) {
            document.getElementById('selection-modal').style.display = 'none';
            // Switch back to Einzel mode
            modeToggle.checked = false;
            modeToggle.dispatchEvent(new Event('change'));
            urlInput.value = selectedUrls.join('\n');
            calculateMatches(selectedUrls);
        }
    });

    document.getElementById('close-odds-btn').addEventListener('click', () => {
        document.getElementById('odds-modal').style.display = 'none';
    });
});

async function calculateMatches(urls) {
    const pts_ex = document.getElementById('pts-ex').value;
    const pts_diff = document.getElementById('pts-diff').value;
    const pts_tend = document.getElementById('pts-tend').value;

    document.getElementById('progress-fill').classList.add('determinate');
    document.getElementById('progress-fill').style.width = '100%';

    try {
        const response = await window.pywebview.api.calculate_expected_values({
            urls: urls,
            pts_ex: pts_ex,
            pts_diff: pts_diff,
            pts_tend: pts_tend
        });

        if (response.success) {
            renderResults(response.results);
        } else {
            showError(response.error);
        }
    } catch (err) {
        showError("Fehler bei der Berechnung.");
    }

    resetUI();
}

function renderResults(results) {
    const container = document.getElementById('results-container');
    container.innerHTML = '';

    results.forEach(match => {
        const card = document.createElement('div');
        card.className = 'result-card glass-panel';

        if (match.error) {
            card.innerHTML = `
                <div class="card-header"><div class="teams">${match.match_name}</div></div>
                <div class="error-text">${match.error}</div>
            `;
            container.appendChild(card);
            return;
        }

        let tipsHtml = '';
        const medals = ['🥇', '🥈', '🥉'];
        match.best_tips.slice(0, 3).forEach((tip, idx) => {
            const isWinner = idx === 0 ? 'winner' : '';
            tipsHtml += `
                <div class="tip-row ${isWinner}">
                    <div class="tip-score">${medals[idx]} &nbsp; ${tip.tip}</div>
                    <div class="tip-pts">➔ ${tip.expected_value.toFixed(3)} Pkt</div>
                </div>
            `;
        });

        // Wir speichern die odds im globalen window, um sie später abzurufen
        const matchId = 'match_' + Math.random().toString(36).substr(2, 9);
        window[matchId] = match.odds;

        card.innerHTML = `
            <div class="card-header">
                <div class="teams">${match.match_name.replace(' vs ', ' - ')}</div>
            </div>
            <div class="tips-container">${tipsHtml}</div>
            <button class="odds-btn" onclick="showOdds('${match.match_name.replace(/'/g, "\\'")}', window['${matchId}'])">📊 Quoten</button>
        `;
        container.appendChild(card);
    });
}

function showSelectionModal(matches) {
    const modal = document.getElementById('selection-modal');
    const list = document.getElementById('match-list');
    list.innerHTML = '';
    
    let currentDate = '';

    matches.forEach(match => {
        const mDate = match.date || 'Weitere Spiele';
        if (mDate !== currentDate) {
            currentDate = mDate;
            const header = document.createElement('div');
            header.className = 'match-date-header';
            header.innerText = currentDate;
            list.appendChild(header);
        }

        let displayName = match.name;
        if (match.parts && match.parts.length === 3) {
            displayName = `🕒 ${match.parts[0]} ➔ ${match.parts[1]} - ${match.parts[2]}`;
        }

        const item = document.createElement('div');
        item.className = 'match-item';
        item.innerHTML = `
            <input type="checkbox" class="match-cb" value="${match.url}" id="${match.url}">
            <label for="${match.url}">${displayName}</label>
        `;
        list.appendChild(item);
    });

    document.getElementById('select-all').checked = false;
    document.getElementById('progress-container').style.display = 'none';
    modal.style.display = 'flex';
}

function showOdds(matchName, odds) {
    const modal = document.getElementById('odds-modal');
    document.getElementById('odds-match-title').innerText = matchName;
    const list = document.getElementById('odds-list');
    list.innerHTML = '';

    if (!odds || Object.keys(odds).length === 0) {
        list.innerHTML = '<p>Keine Quoten verfügbar.</p>';
    } else {
        const sortedOdds = Object.entries(odds).sort((a, b) => parseFloat(a[1]) - parseFloat(b[1]));
        sortedOdds.forEach(([score, odd]) => {
            const row = document.createElement('div');
            row.className = 'odds-row';
            row.innerHTML = `<span>Ergebnis ${score}</span> <span>Quote: ${parseFloat(odd).toFixed(2)}</span>`;
            list.appendChild(row);
        });
    }

    modal.style.display = 'flex';
}

function showError(msg) {
    document.getElementById('status-text').innerText = 'Fehler: ' + msg;
    document.getElementById('status-text').style.color = 'var(--danger)';
    resetUI();
}

function updateProgress(msg) {
    document.getElementById('status-text').innerText = msg;
    document.getElementById('status-text').style.color = 'var(--text-secondary)';
}

function resetUI() {
    document.getElementById('start-btn').disabled = false;
    document.getElementById('progress-fill').classList.remove('determinate');
    setTimeout(() => {
        document.getElementById('progress-container').style.display = 'none';
    }, 2000); // Hide after a bit
}
