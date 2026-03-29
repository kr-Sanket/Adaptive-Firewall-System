// ---- Chart Setup ----
const ctx = document.getElementById('rewardChart').getContext('2d');
const rewardChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Avg Reward',
      data: [],
      borderColor: '#00d4ff',
      backgroundColor: 'rgba(0,212,255,0.08)',
      borderWidth: 2,
      pointRadius: 0,
      fill: true,
      tension: 0.4,
    }]
  },
  options: {
    responsive: true,
    animation: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { display: false },
      y: {
        grid: { color: 'rgba(30,58,95,0.5)' },
        ticks: {
          color: '#64748b',
          font: { family: 'Share Tech Mono', size: 10 }
        }
      }
    }
  }
});

const phaseColors = {
  RECON: '#3b82f6', PROBE: '#f59e0b',
  EXPLOIT: '#f97316', ESCALATE: '#ef4444', STEALTH: '#6b7280'
};

const actionColors = {
  ALLOW: '#22c55e', BLOCK: '#ef4444',
  THROTTLE: '#f59e0b', OBSERVE: '#3b82f6', DECEIVE: '#a855f7'
};

// ---- SSE Connection ----
const evtSource = new EventSource('/stream');

evtSource.onmessage = function(e) {
  const data = JSON.parse(e.data);
  updateDashboard(data);
};

function updateDashboard(data) {
  // Always update header stats
  document.getElementById('stepCounter').textContent = data.step;

  if (data.mode === 'comparison') {
    // In comparison mode — only update comparison panel
    const avg = data.rl_avg_reward;
    document.getElementById('avgReward').textContent =
      (avg >= 0 ? '+' : '') + avg.toFixed(2);
    updateComparison(data);
    return; // skip normal dashboard updates
  }

  // Normal mode updates
  document.getElementById('avgReward').textContent =
    (data.avg_reward >= 0 ? '+' : '') + data.avg_reward.toFixed(2);

  updateThreatGauge(data.threat_level);
  data.attackers.forEach((atk, i) => updateCard(i, atk));
  updateChart(data.reward_history);
  updateActionBars(data.action_totals);
  updateEventLog(data.event_log);
  updateTimeline(data.attackers, data.step);

  if (data.attackers[activeExplainerIdx]?.deep_explanation) {
    lastExplainerData = data.attackers.map(a => a.deep_explanation);
    updateExplainer(lastExplainerData[activeExplainerIdx]);
  }
}

function updateCard(i, atk) {
  const phase = document.getElementById(`phase-${i}`);
  phase.textContent = atk.phase;
  phase.style.background = atk.phase_color + '22';
  phase.style.color = atk.phase_color;
  phase.style.borderColor = atk.phase_color;

  document.getElementById(`card-${i}`).style.borderColor =
    atk.phase === 'ESCALATE' ? '#ef4444' :
    atk.phase === 'EXPLOIT'  ? '#f97316' : '#1e3a5f';

  document.getElementById(`tactic-${i}`).textContent = atk.tactic_desc;

  document.getElementById(`conf-${i}`).style.width = atk.confidence + '%';
  document.getElementById(`conf-val-${i}`).textContent = atk.confidence + '%';

  document.getElementById(`frus-${i}`).style.width = atk.frustration + '%';
  document.getElementById(`frus-val-${i}`).textContent = atk.frustration + '%';

  document.getElementById(`rate-${i}`).textContent = atk.rate + ' pps';

  const actionEl = document.getElementById(`action-${i}`);
  actionEl.textContent = atk.action;
  actionEl.style.color = atk.action_color;

  document.getElementById(`why-${i}`).textContent = atk.explanation;
}

function updateThreatGauge(level) {
  const arc = document.getElementById('gaugeArc');
  const total = 251;
  const filled = (level / 100) * total;
  arc.setAttribute('stroke-dasharray', `${filled} ${total}`);
  document.getElementById('threatNum').textContent = level;

  const statusEl = document.getElementById('threatStatus');
  if (level < 30) {
    statusEl.textContent = 'LOW RISK';
    statusEl.style.color = '#22c55e';
  } else if (level < 60) {
    statusEl.textContent = 'MODERATE';
    statusEl.style.color = '#f59e0b';
  } else if (level < 80) {
    statusEl.textContent = 'HIGH RISK';
    statusEl.style.color = '#f97316';
  } else {
    statusEl.textContent = 'CRITICAL';
    statusEl.style.color = '#ef4444';
  }
}

function updateChart(history) {
  rewardChart.data.labels = history.map((_, i) => i);
  rewardChart.data.datasets[0].data = history;
  rewardChart.update('none');
}

function updateActionBars(totals) {
  const max = Math.max(...Object.values(totals), 1);
  document.querySelectorAll('.action-bar-row').forEach(row => {
    const action = row.dataset.action;
    const count = totals[action] || 0;
    const pct = (count / max * 100).toFixed(1);
    row.querySelector('.ab-fill').style.width = pct + '%';
    row.querySelector('.ab-count').textContent = count;
  });
}

function updateEventLog(log) {
  const container = document.getElementById('eventLog');
  container.innerHTML = log.map(e => `
    <div class="log-entry" style="border-left-color:${e.phase_color}">
      <span class="log-step">#${e.step}</span>
      <span class="log-name">${e.attacker}</span>
      <span class="log-tactic">${e.tactic}</span>
      <span class="log-action" style="background:${e.action_color}22;color:${e.action_color}">
        ${e.action}
      </span>
    </div>
  `).join('');
}

let timelineData = [];
function updateTimeline(attackers, step) {
  attackers.forEach(atk => {
    timelineData.unshift({
      step, name: atk.name, phase: atk.phase,
      color: phaseColors[atk.phase]
    });
  });
  if (timelineData.length > 30) timelineData = timelineData.slice(0, 30);

  document.getElementById('phaseTimeline').innerHTML =
    timelineData.map(t => `
      <div class="timeline-row">
        <span class="tl-attacker">${t.name}</span>
        <span class="tl-phase" style="background:${t.color}22;color:${t.color};border:1px solid ${t.color}">
          ${t.phase}
        </span>
        <span class="tl-step">#${t.step}</span>
      </div>
    `).join('');
}

// ---- Controls ----
function resetSim() {
  fetch('/reset', { method: 'POST' });
  rewardChart.data.labels = [];
  rewardChart.data.datasets[0].data = [];
  rewardChart.update();
  timelineData = [];
}

function setSpeed(val) {
  document.getElementById('speedVal').textContent = parseFloat(val).toFixed(1) + 's';
  fetch(`/speed/${val}`, { method: 'POST' });
}

// ---- Attack Injection ----
let paused = false;

function injectAttack(attackerId, attackType) {
  fetch(`/inject/${attackerId}/${attackType}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      showNotification(attackerId, attackType);
    });
}

function showNotification(attackerId, attackType) {
  const labels = {
    'ddos':        '💥 DDoS attack injected',
    'brute_force': '🔑 Brute force attack injected',
    'stealth':     '👻 Stealth infiltration injected',
    'coordinated': '🎯 APT simulation injected',
    'exfil':       '📤 Data exfiltration injected',
    'reset':       '↺ Attackers reset to RECON',
  };
  const target = attackerId === 'all' ? 'ALL ATTACKERS' : `ATTACKER ${['A','B','C'][attackerId]}`;
  const msg = `${labels[attackType] || attackType} → ${target}`;

  const el = document.getElementById('injectNotify');
  el.textContent = msg;
  el.style.opacity = '1';
  setTimeout(() => { el.style.opacity = '0'; }, 3000);
}

function togglePause() {
  const btn = document.getElementById('pauseBtn');
  if (!paused) {
    fetch('/pause', { method: 'POST' });
    btn.textContent = '▶ RESUME';
    btn.style.background = 'rgba(34,197,94,0.1)';
    btn.style.borderColor = 'rgba(34,197,94,0.4)';
    btn.style.color = '#22c55e';
    paused = true;
  } else {
    fetch('/resume', { method: 'POST' });
    btn.textContent = '⏸ PAUSE';
    btn.style.background = 'rgba(245,158,11,0.1)';
    btn.style.borderColor = 'rgba(245,158,11,0.4)';
    btn.style.color = '#f59e0b';
    paused = false;
  }
}

// ---- Explainability Layer ----
let activeExplainerIdx = 0;
let lastExplainerData = [];

function switchExplainer(idx, btn) {
  activeExplainerIdx = idx;
  document.querySelectorAll('.exp-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  if (lastExplainerData[idx]) updateExplainer(lastExplainerData[idx]);
}

function updateExplainer(exp) {
  document.getElementById('expAction').textContent = exp.action;
  document.getElementById('expAction').style.color =
    actionColors[exp.action] || 'var(--accent)';
  document.getElementById('expPhase').textContent = exp.phase;
  document.getElementById('expWhy').textContent = exp.why;
  document.getElementById('expRisk').textContent = exp.risk;
  document.getElementById('expStrategy').textContent = exp.strategy;
  const r = exp.reward;
  const el = document.getElementById('expReward');
  el.textContent = (r >= 0 ? '+' : '') + r.toFixed(2);
  el.style.color = r >= 0 ? '#22c55e' : '#ef4444';
}

// ---- Comparison Mode ----
let comparisonActive = false;

// Comparison chart
const compCtx = document.getElementById('compChart').getContext('2d');
const compChart = new Chart(compCtx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      {
        label: 'RL Defender',
        data: [],
        borderColor: '#00c8f0',
        backgroundColor: 'rgba(0,200,240,0.06)',
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Static Firewall',
        data: [],
        borderColor: '#f0a020',
        backgroundColor: 'rgba(240,160,32,0.06)',
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.4,
      }
    ]
  },
  options: {
    responsive: true,
    animation: false,
    plugins: {
      legend: {
        display: true,
        labels: {
          color: '#8fa8c0',
          font: { family: 'Share Tech Mono', size: 10 },
          boxWidth: 12,
        }
      }
    },
    scales: {
      x: { display: false },
      y: {
        grid: { color: 'rgba(26,48,80,0.5)' },
        ticks: { color: '#4e6580', font: { family: 'Share Tech Mono', size: 10 } }
      }
    }
  }
});

let rlRewardHistory = [];
let staticRewardHistory = [];

function toggleComparison() {
  comparisonActive = !comparisonActive;
  const btn = document.getElementById('compareBtn');
  const overlay = document.getElementById('comparisonOverlay');

  if (comparisonActive) {
    btn.classList.add('active');
    btn.textContent = '✕ EXIT COMPARE';
    overlay.style.display = 'block';
    fetch('/mode/comparison', { method: 'POST' });
  } else {
    btn.classList.remove('active');
    btn.textContent = '⚡ COMPARE MODE';
    overlay.style.display = 'none';
    fetch('/mode/normal', { method: 'POST' });
  }
}

function updateComparison(data) {
  if (!data.comparison) return;

  // Scores
  const rl = data.rl_avg_reward;
  const st = data.static_avg_reward;

  document.getElementById('rlScore').textContent =
    (rl >= 0 ? '+' : '') + rl.toFixed(2);
  document.getElementById('staticScore').textContent =
    (st >= 0 ? '+' : '') + st.toFixed(2);

  const winner = document.getElementById('compWinner');
  if (rl > st) {
    winner.textContent = '🧠 RL DEFENDER WINNING';
    winner.style.color = '#00c8f0';
  } else if (st > rl) {
    winner.textContent = '🛡 STATIC LEADING';
    winner.style.color = '#f0a020';
  } else {
    winner.textContent = 'TIED';
    winner.style.color = '#4e6580';
  }

  // Per-attacker rows
  data.comparison.forEach((atk, i) => {
    const phase = document.getElementById(`comp-phase-${i}`);
    phase.textContent = atk.phase;
    phase.style.background = atk.phase_color + '22';
    phase.style.color = atk.phase_color;
    phase.style.borderColor = atk.phase_color;

    document.getElementById(`comp-rate-${i}`).textContent = atk.rate + ' pps';

    // Static side
    const sa = document.getElementById(`static-action-${i}`);
    sa.textContent = atk.static_action;
    sa.style.color = atk.static_color;
    document.getElementById(`static-why-${i}`).textContent = atk.static_explanation;
    const sr = document.getElementById(`static-reward-${i}`);
    sr.textContent = 'Reward: ' + (atk.static_reward >= 0 ? '+' : '') + atk.static_reward;
    sr.style.color = atk.static_reward >= 0 ? '#22c55e' : '#f04444';

    // RL side
    const ra = document.getElementById(`rl-action-${i}`);
    ra.textContent = atk.rl_action;
    ra.style.color = atk.rl_color;
    document.getElementById(`rl-why-${i}`).textContent = atk.rl_explanation;
    const rr = document.getElementById(`rl-reward-${i}`);
    rr.textContent = 'Reward: ' + (atk.rl_reward >= 0 ? '+' : '') + atk.rl_reward;
    rr.style.color = atk.rl_reward >= 0 ? '#22c55e' : '#f04444';

    // Highlight rows where decisions differ
    const row = document.getElementById(`comp-row-${i}`);
    if (atk.rl_action !== atk.static_action) {
      row.style.borderColor = 'rgba(0,200,240,0.3)';
    } else {
      row.style.borderColor = 'var(--border)';
    }
  });

  // Comparison chart
  rlRewardHistory.push(rl);
  staticRewardHistory.push(st);
  if (rlRewardHistory.length > 80) {
    rlRewardHistory.shift();
    staticRewardHistory.shift();
  }

  compChart.data.labels = rlRewardHistory.map((_, i) => i);
  compChart.data.datasets[0].data = rlRewardHistory;
  compChart.data.datasets[1].data = staticRewardHistory;
  compChart.update('none');
}