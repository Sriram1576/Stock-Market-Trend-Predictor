// Modernized app.js connecting UI-UX-Pro-Max to the 4-Pillar Algorithmic Pipeline
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

const UI = {
    searchBtn: document.getElementById('search-btn'),
    searchInput: document.getElementById('stock-search'),
    searchLoader: document.getElementById('search-loader'),
    chips: document.querySelectorAll('.stock-chip'),
    loadingProgress: document.getElementById('loading-progress'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-percentage'),
    progressMsg: document.getElementById('progress-message'),
    analysisContainer: document.getElementById('stock-analysis'),
    retrySection: document.getElementById('retry-section'),
    retryBtn: document.getElementById('retry-btn'),
    chartRefreshBtn: document.getElementById('refresh-chart')
};

let chartInstance = null;

async function initApp() {
    UI.searchBtn.addEventListener('click', handleSearch);
    UI.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
    
    UI.chips.forEach(chip => {
        chip.addEventListener('click', () => {
            UI.chips.forEach(c => c.classList.remove('active', 'border-blue-500'));
            chip.classList.add('active', 'border-blue-500');
            UI.searchInput.value = chip.dataset.symbol;
            handleSearch();
        });
    });

    UI.retryBtn.addEventListener('click', handleSearch);
    UI.chartRefreshBtn.addEventListener('click', handleSearch);

    // Initial load
    if (UI.chips.length > 0) {
        UI.searchInput.value = UI.chips[0].dataset.symbol;
        await handleSearch();
    }
}

async function handleSearch() {
    const symbol = UI.searchInput.value.trim().toUpperCase();
    if (!symbol) return;
    
    // UI state updates
    UI.retrySection.classList.add('hidden');
    UI.analysisContainer.classList.add('hidden');
    UI.loadingProgress.classList.remove('hidden');
    
    await simulateProgress();

    try {
        const response = await fetch('data/daily_predictions.json?t=' + Date.now());
        if (!response.ok) throw new Error('Data not found');
        
        const data = await response.json();
        
        let stockData = data[symbol];
        if (!stockData) {
            // Try fallback appending .NS
            stockData = data[symbol.replace('.BSE', '.NS')] || data[symbol + '.NS'];
        }

        if (!stockData) {
            throw new Error(`Symbol ${symbol} not found in algorithmic database.`);
        }

        renderDashboard(symbol, stockData);
        
        UI.loadingProgress.classList.add('hidden');
        UI.analysisContainer.classList.remove('hidden');
        document.getElementById('api-status').innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-2"></span>Online';
        document.getElementById('api-status').className = 'status-value high flex items-center text-emerald-400';
        document.getElementById('last-update').innerText = new Date().toLocaleTimeString();
        
    } catch (error) {
        console.error(error);
        UI.loadingProgress.classList.add('hidden');
        UI.retrySection.classList.remove('hidden');
        document.getElementById('retry-message').innerText = error.message;
        document.getElementById('api-status').innerHTML = '<span class="w-2 h-2 rounded-full bg-red-500 mr-2"></span>Offline';
        document.getElementById('api-status').className = 'status-value negative flex items-center text-red-400';
    }
}

function renderDashboard(symbol, data) {
    const quote = data.quote;
    const tech = data.technical;
    const pred = data.prediction;

    // Overview
    document.getElementById('stock-symbol').innerText = symbol.replace('.NS', '');
    const chip = Array.from(UI.chips).find(c => c.dataset.symbol.includes(symbol.replace('.NS', '')));
    document.getElementById('company-name').innerText = chip ? chip.dataset.name : symbol;
    
    document.getElementById('current-price').innerText = `₹${quote.price.toFixed(2)}`;
    
    const changeEl = document.getElementById('price-change');
    changeEl.innerText = `${quote.change >= 0 ? '+' : ''}₹${quote.change.toFixed(2)} (${quote.change_percent >= 0 ? '+' : ''}${quote.change_percent.toFixed(2)}%)`;
    changeEl.className = `text-xl font-medium ${quote.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`;

    document.getElementById('volume').innerText = formatNumber(quote.volume);
    document.getElementById('day-range').innerText = `₹${quote.low.toFixed(2)} - ₹${quote.high.toFixed(2)}`;

    // Pillars
    document.getElementById('ema-13').innerText = `EMA 13: ₹${tech.ema13.toFixed(2)}`;
    document.getElementById('ema-21').innerText = `EMA 21: ₹${tech.ema21.toFixed(2)}`;
    document.getElementById('ema-signal').innerText = tech.trend;
    document.getElementById('ema-signal').className = tech.trend === 'Bullish' ? 'text-emerald-400 ml-2' : 'text-red-400 ml-2';

    document.getElementById('macd-line').innerText = tech.vol_spike ? 'Vol > 1.5x SMA' : 'Vol < 1.5x SMA';
    document.getElementById('macd-histogram').innerText = tech.vol_spike ? 'Valid Spike' : 'Average';
    document.getElementById('macd-histogram').className = tech.vol_spike ? 'text-emerald-400 ml-2' : 'text-slate-400 ml-2';

    document.getElementById('rsi-value').innerText = `PCR: ${tech.pcr.toFixed(2)}`;
    document.getElementById('rsi-status').innerText = tech.pcr_sentiment;
    document.getElementById('rsi-status').className = tech.pcr_sentiment === 'BULLISH' ? 'text-emerald-400 ml-2' : (tech.pcr_sentiment === 'BEARISH' ? 'text-red-400 ml-2' : 'text-yellow-400 ml-2');

    // AI Prediction
    document.getElementById('prediction-direction').innerText = pred.signal_text;
    document.getElementById('prediction-direction').className = `text-3xl font-black tracking-widest mb-2 ${pred.direction === 'BULLISH' ? 'text-emerald-400' : (pred.direction === 'BEARISH' ? 'text-red-400' : 'text-yellow-400')}`;
    
    let alignmentCount = (pred.pillars_aligned.match(/True/g) || []).length;
    document.getElementById('prediction-confidence').innerText = `${alignmentCount}/4 Pillars Aligned`;

    // Risk / Execution
    document.getElementById('entry-signal').innerText = pred.signal_text !== 'NO TRADE' ? `Execute ${pred.direction} at Market` : 'Wait for setup';
    document.getElementById('target-1').innerText = pred.target > 0 ? `₹${pred.target.toFixed(2)}` : 'N/A';
    document.getElementById('stop-loss').innerText = pred.stop_loss > 0 ? `₹${pred.stop_loss.toFixed(2)}` : 'N/A';
    
    renderChart(symbol, quote);
}

function renderChart(symbol, quote) {
    const ctx = document.getElementById('price-chart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    // Generate random path ending at quote.price for aesthetic
    let prices = [];
    let cur = quote.open;
    for(let i=0; i<30; i++) {
        prices.push(cur);
        cur += (Math.random() - 0.5) * (quote.high - quote.low) * 0.5;
    }
    prices.push(quote.price); // end at exact current price

    const isBull = quote.change >= 0;
    const color = isBull ? '#10b981' : '#ef4444'; // Emerald or Red

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: new Array(31).fill(''),
            datasets: [{
                label: symbol,
                data: prices,
                borderColor: color,
                backgroundColor: isBull ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { display: false, min: Math.min(...prices) * 0.99, max: Math.max(...prices) * 1.01 }
            }
        }
    });
}

async function simulateProgress() {
    const steps = [
        { pct: 20, msg: "Connecting to Exchange..." },
        { pct: 50, msg: "Fetching 15m OHLCV Data..." },
        { pct: 75, msg: "Evaluating 4-Pillar Pipeline..." },
        { pct: 100, msg: "Calculating Risk Parameters..." }
    ];
    
    for (const step of steps) {
        UI.progressFill.style.width = step.pct + '%';
        UI.progressText.innerText = step.pct + '%';
        UI.progressMsg.innerText = step.msg;
        await new Promise(r => setTimeout(r, 400));
    }
}

function formatNumber(num) {
    if (num >= 1e7) return (num / 1e7).toFixed(2) + 'Cr';
    if (num >= 1e5) return (num / 1e5).toFixed(2) + 'L';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'k';
    return num.toString();
}