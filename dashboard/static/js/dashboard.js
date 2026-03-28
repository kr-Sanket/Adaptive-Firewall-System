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
  // Header stats
  document.getElementById('stepCounter').textContent = data.step;
  document.getElementById('avgReward').textContent =
    (data.avg_reward >= 0 ? '+' : '') + data.avg_reward.toFixed(2);

  // Threat gauge
  updateThreatGauge(data.threat_level);

  // Attacker cards
  data.attackers.forEach((atk, i) => updateCard(i, atk));

  // Reward chart
  updateChart(data.reward_history);

  // Action distribution
  updateActionBars(data.action_totals);

  // Event log
  updateEventLog(data.event_log);

  // Phase timeline
  updateTimeline(data.attackers, data.step);

  // Update explainer
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