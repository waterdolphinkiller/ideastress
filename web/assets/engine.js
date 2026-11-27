// IdeaStress v0.8.1 Shared Deterministic Financial + 1,000-Run Monte Carlo + US Stripe/Tax Engine
const PAYMENT_FEES = {
  none: { pct: 0, flat: 0, label: 'None (0%)' },
  stripe_us: { pct: 0.029, flat: 0.30, label: 'Stripe US (2.9% + $0.30)' },
  stripe_saas: { pct: 0.036, flat: 0.30, label: 'Stripe US + Billing (3.6% + $0.30)' },
  mor_paddle: { pct: 0.050, flat: 0.50, label: 'MoR Paddle/LS (5% + $0.50)' }
};

function mulberry32(seed) {
  let a = seed >>> 0;
  return function() {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function randNorm(rng) {
  const u1 = Math.max(1e-7, rng()), u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function showToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

function paymentFee(price, preset) {
  const f = PAYMENT_FEES[preset] || PAYMENT_FEES.none;
  return price * f.pct + f.flat;
}

function simPath(cfg, mults = {}) {
  const p = cfg.price * (mults.p || 1);
  const fee = paymentFee(p, cfg.processor);
  const v = cfg.varCost * (1 + cfg.payrollPct / 100) * (mults.v || 1) + fee;
  const fx = cfg.fixed * (mults.fx || 1);
  const nc = Math.max(0, Math.round(cfg.newC * (mults.nc || 1)));
  const sp = cfg.spend * (mults.sp || 1);
  const ch = Math.min(0.95, Math.max(0, (cfg.churnPct / 100) * (mults.ch || 1)));
  const netUnit = p * (1 - cfg.refundPct / 100);
  const contrib = netUnit - v;
  let active = 0, c = cfg.cash, minC = cfg.cash;
  const series = [cfg.cash];
  for (let m = 1; m <= 12; m++) {
    if (cfg.type === 'saas') {
      active = Math.max(0, Math.round(active * (1 - ch))) + nc;
    } else {
      active = nc;
    }
    const ebt = active * contrib - fx - sp;
    const tax = (ebt > 0 && cfg.taxPct > 0) ? ebt * (cfg.taxPct / 100) : 0;
    c += (ebt - tax);
    if (c < minC) minC = c;
    series.push(c);
  }
  return { ending: c, minC, contrib, fee, series };
}

function runMonteCarlo1000(cfg) {
  const N = 1000;
  const rng = mulberry32(42);
  const fee = paymentFee(cfg.price, cfg.processor);
  const baseVar = cfg.varCost * (1 + cfg.payrollPct / 100) + fee;
  const netUnit = cfg.price * (1 - cfg.refundPct / 100);
  const ends = new Float64Array(N);
  const mins = new Float64Array(N);
  let survived = 0;

  for (let i = 0; i < N; i++) {
    const cacMult = Math.min(2.4, Math.max(0.65, Math.exp(0.05 + 0.22 * randNorm(rng))));
    const churnMult = Math.min(2.2, Math.max(0.5, 1.02 + 0.20 * randNorm(rng)));
    const varMult = Math.min(1.35, Math.max(0.8, 1.0 + 0.08 * randNorm(rng)));
    let c = cfg.cash, minC = cfg.cash, active = 0;
    for (let m = 1; m <= 12; m++) {
      const nc = Math.max(0, Math.round(cfg.newC + Math.max(1, cfg.newC * 0.22) * randNorm(rng)));
      if (cfg.type === 'saas') {
        const spike = m === 1 ? 1.35 : (m === 2 ? 1.15 : 1.0);
        const mc = Math.min(0.90, Math.max(0, (cfg.churnPct / 100) * churnMult * spike));
        active = Math.max(0, active - Math.round(active * mc)) + nc;
      } else {
        active = nc;
      }
      const ebt = active * (netUnit - baseVar * varMult) - cfg.fixed - cfg.spend * cacMult;
      const tax = (ebt > 0 && cfg.taxPct > 0) ? ebt * (cfg.taxPct / 100) : 0;
      c += (ebt - tax);
      if (c < minC) minC = c;
    }
    ends[i] = c; mins[i] = minC;
    if (minC >= 0) survived++;
  }
  ends.sort(); mins.sort();
  const survivalPct = (survived / N) * 100;
  const risk = survivalPct >= 85 ? 'LOW_RISK' : (survivalPct >= 60 ? 'MODERATE_RISK' : (survivalPct >= 30 ? 'HIGH_RISK' : 'CRITICAL_RISK'));
  return {
    survivalPct, risk,
    p10End: ends[Math.floor(N * 0.1)],
    p50End: ends[Math.floor(N * 0.5)],
    p90End: ends[Math.floor(N * 0.9)],
    p10Min: mins[Math.floor(N * 0.1)]
  };
}

function solveMaxCac(cfg) {
  if (cfg.newC <= 0) return 0;
  if (simPath({ ...cfg, spend: 0 }).minC < 0) return 0;
  let lo = 0, hi = Math.max(5000, cfg.price * 24);
  for (let i = 0; i < 32; i++) {
    const mid = (lo + hi) / 2;
    if (simPath({ ...cfg, spend: mid * cfg.newC }).minC >= 0) lo = mid;
    else hi = mid;
  }
  return lo;
}

function solveMinPrice(cfg) {
  let lo = 0.01, hi = 25000;
  if (simPath({ ...cfg, price: hi }).minC < 0) return null;
  for (let i = 0; i < 32; i++) {
    const mid = (lo + hi) / 2;
    if (simPath({ ...cfg, price: mid }).minC >= 0) hi = mid;
    else lo = mid;
  }
  return hi;
}

function renderCashChart(svgId, cons, base, opt, cur) {
  const svg = document.getElementById(svgId);
  if (!svg) return;
  const all = [...cons, ...base, ...opt, 0];
  const minV = Math.min(...all), maxV = Math.max(...all), span = Math.max(1, maxV - minV);
  const W = 680, H = 195, padL = 56, padR = 16, padT = 16, padB = 24;
  const x = i => padL + (i / 12) * (W - padL - padR);
  const y = v => padT + (1 - (v - minV) / span) * (H - padT - padB);
  const path = arr => arr.map((v, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  const yZero = y(0);
  svg.innerHTML = `
    <line x1="${padL}" y1="${yZero.toFixed(1)}" x2="${W - padR}" y2="${yZero.toFixed(1)}" stroke="#ef444466" stroke-dasharray="4 4" />
    <text x="6" y="${(yZero + 4).toFixed(1)}" fill="#ef4444" font-size="10" font-family="monospace">0 ${cur}</text>
    <text x="6" y="18" fill="#8a95ad" font-size="10" font-family="monospace">${Math.round(maxV).toLocaleString()}</text>
    <text x="6" y="${H - 22}" fill="#8a95ad" font-size="10" font-family="monospace">${Math.round(minV).toLocaleString()}</text>
    <path d="${path(cons)}" fill="none" stroke="#f59e0b" stroke-width="2" stroke-dasharray="5 3" />
    <path d="${path(base)}" fill="none" stroke="#38bdf8" stroke-width="3" />
    <path d="${path(opt)}" fill="none" stroke="#10b981" stroke-width="2" opacity="0.8" />
    <text x="${padL}" y="${H - 6}" fill="#8a95ad" font-size="10" font-family="monospace">M0</text>
    <text x="${x(6).toFixed(1)}" y="${H - 6}" fill="#8a95ad" font-size="10" font-family="monospace">M6</text>
    <text x="${(W - padR - 22)}" y="${H - 6}" fill="#8a95ad" font-size="10" font-family="monospace">M12</text>
  `;
}

window.initFrontierTool = function() {
  const root = document.getElementById('tool-frontier');
  if (!root) return;
  let lastCfg = null;
  function update() {
    const cfg = {
      type: document.getElementById('f_type').value,
      cur: document.getElementById('f_cur').value,
      processor: document.getElementById('f_proc').value,
      taxPct: parseFloat(document.getElementById('f_tax').value) || 0,
      payrollPct: parseFloat(document.getElementById('f_payroll')?.value) || 0,
      price: parseFloat(document.getElementById('f_price').value) || 0,
      varCost: parseFloat(document.getElementById('f_var').value) || 0,
      fixed: parseFloat(document.getElementById('f_fixed').value) || 0,
      cash: parseFloat(document.getElementById('f_cash').value) || 0,
      newC: parseInt(document.getElementById('f_new').value, 10) || 0,
      spend: parseFloat(document.getElementById('f_spend').value) || 0,
      churnPct: parseFloat(document.getElementById('f_churn').value) || 0,
      refundPct: parseFloat(document.getElementById('f_refund').value) || 0
    };
    lastCfg = cfg;
    const base = simPath(cfg);
    const cons = simPath(cfg, { p: 0.9, nc: 0.65, v: 1.15, fx: 1.1, sp: 1.25, ch: 1.35 });
    const opt = simPath(cfg, { p: 1.1, nc: 1.3, v: 0.95, sp: 0.9, ch: 0.8 });
    const mc = runMonteCarlo1000(cfg);
    const maxCac = solveMaxCac(cfg);
    const minPrice = solveMinPrice(cfg);
    const curCac = cfg.newC > 0 ? cfg.spend / cfg.newC : 0;

    const vbox = document.getElementById('f_verdict_box');
    const survColor = mc.survivalPct >= 85 ? 'var(--ok)' : (mc.survivalPct >= 60 ? 'var(--warn)' : 'var(--bad)');
    const cls = (base.contrib <= 0 || mc.survivalPct < 30) ? 'bad' : (mc.survivalPct < 80 ? 'warn' : 'ok');
    vbox.className = 'alert-box ' + cls;
    vbox.innerHTML = `<strong class="mono">${mc.risk} · ${mc.survivalPct.toFixed(1)}% 12-Month Survival Probability (1,000 Monte Carlo runs)</strong> — P10 cash trough: ${cfg.cur} ${Math.round(mc.p10Min).toLocaleString()} · Payment fee/unit: ${cfg.cur} ${base.fee.toFixed(2)}.`;

    document.getElementById('f_kpis').innerHTML = `
      <div class="kpi"><div class="kl">1,000-Run Survival Prob</div><div class="kv" style="color:${survColor}">${mc.survivalPct.toFixed(1)}%</div><div class="ks">P50 Cash: ${cfg.cur} ${Math.round(mc.p50End).toLocaleString()}</div></div>
      <div class="kpi"><div class="kl">Max Viable CAC (12m)</div><div class="kv" style="color:var(--accent)">${cfg.cur} ${maxCac.toFixed(2)}</div><div class="ks">Modeled CAC: ${cfg.cur} ${curCac.toFixed(2)}</div></div>
      <div class="kpi"><div class="kl">Min Viable Price</div><div class="kv">${minPrice !== null ? cfg.cur + ' ' + minPrice.toFixed(2) : 'IMPOSSIBLE'}</div><div class="ks">Unit Contrib: ${cfg.cur} ${base.contrib.toFixed(2)}</div></div>
      <div class="kpi"><div class="kl">P10 Downside Cash</div><div class="kv" style="color:${mc.p10End >= 0 ? 'var(--ok)':'var(--bad)'}">${cfg.cur} ${Math.round(mc.p10End).toLocaleString()}</div><div class="ks">P90 Upside: ${cfg.cur} ${Math.round(mc.p90End).toLocaleString()}</div></div>
    `;

    const afBox = document.getElementById('f_autofix_box');
    if (afBox) {
      if (mc.survivalPct < 85) {
        let loP = cfg.price, hiP = Math.max(cfg.price * 6, 500), solvedP = null;
        if (runMonteCarlo1000({ ...cfg, price: hiP }).survivalPct >= 85) {
          for (let k = 0; k < 14; k++) {
            const mP = (loP + hiP) / 2;
            if (runMonteCarlo1000({ ...cfg, price: mP }).survivalPct >= 85) { hiP = mP; solvedP = mP; }
            else loP = mP;
          }
        }
        afBox.style.display = 'block';
        afBox.className = 'alert-box warn';
        afBox.innerHTML = solvedP
          ? `<strong class="mono">AUTO-FIX RESCUE PRESCRIPTION (Target &ge;85% Survival):</strong> Raise unit price from <strong>${cfg.cur} ${cfg.price}</strong> to <strong>${cfg.cur} ${solvedP.toFixed(2)}</strong>, or add a 20%-off Annual Prepay Plan / cap monthly ad spend.`
          : `<strong class="mono">AUTO-FIX ALERT:</strong> Even raising price 6x cannot reach 85% survival — restructure fixed/variable costs or customer volume.`;
      } else {
        afBox.style.display = 'none';
      }
    }
    renderCashChart('f_chart', cons.series, base.series, opt.series, cfg.cur);
    const cpc = parseFloat(document.getElementById('f_cpc')?.value) || 0;
    const cvr = Math.max(0.001, (parseFloat(document.getElementById('f_cvr')?.value) || 2.5) / 100);
    const impliedCac = cpc / cvr;
    const reqCvr = maxCac > 0 ? (cpc / maxCac) * 100 : 999;
    const cpcBox = document.getElementById('f_cpc_box');
    if (cpcBox) {
      if (maxCac <= 0 || impliedCac > maxCac || reqCvr > 15) {
        cpcBox.className = 'alert-box bad';
        cpcBox.innerHTML = `<strong class="mono">CHANNEL_IMPOSSIBLE</strong> — At ${cfg.cur} ${cpc.toFixed(2)} CPC &amp; ${(cvr*100).toFixed(1)}% CVR, implied paid CAC is <strong>${cfg.cur} ${impliedCac.toFixed(2)}</strong> vs your <strong>${cfg.cur} ${maxCac.toFixed(2)}</strong> ceiling (needs ${reqCvr.toFixed(1)}% CVR to break even).`;
      } else if (impliedCac > maxCac * 0.75) {
        cpcBox.className = 'alert-box warn';
        cpcBox.innerHTML = `<strong class="mono">CHANNEL_TIGHT</strong> — Implied paid CAC (${cfg.cur} ${impliedCac.toFixed(2)}) consumes &gt;75% of your ${cfg.cur} ${maxCac.toFixed(2)} ceiling (min CVR: ${reqCvr.toFixed(1)}%).`;
      } else {
        cpcBox.className = 'alert-box ok';
        cpcBox.innerHTML = `<strong class="mono">CHANNEL_VIABLE</strong> — Implied paid CAC (${cfg.cur} ${impliedCac.toFixed(2)}) fits under your ${cfg.cur} ${maxCac.toFixed(2)} ceiling (min CVR: ${reqCvr.toFixed(1)}%).`;
      }
    }
  }
  root.querySelectorAll('input, select').forEach(el => el.addEventListener('input', update));
  const dlBtn = document.getElementById('btn_export_yaml');
  if (dlBtn) {
    dlBtn.onclick = () => {
      if (!lastCfg) return;
      const c = lastCfg;
      const y = `idea: "My ${c.type} business idea"\ntarget_market:\n  - "United States"\nbusiness_type: ${c.type}\nbudget: "${c.cash}"\ncurrency: ${c.cur}\ntimeline_months: 12\nfinancials:\n  business_type: ${c.type}\n  currency: ${c.cur}\n  unit_price: "${c.price}"\n  variable_cost_per_unit: "${c.varCost}"\n  fixed_monthly_costs: "${c.fixed}"\n  monthly_new_customers: ${c.newC}\n  monthly_acquisition_spend: "${c.spend}"\n  monthly_churn_rate: "${(c.churnPct / 100).toFixed(4)}"\n  refund_rate: "${(c.refundPct / 100).toFixed(4)}"\n  payment_processor: "${c.processor}"\n  effective_tax_rate: "${(c.taxPct / 100).toFixed(4)}"\n  starting_cash: "${c.cash}"\n  horizon_months: 12\n`;
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([y], { type: 'text/yaml' }));
      a.download = 'venture.yaml'; a.click();
      showToast('Downloaded venture.yaml with US Stripe & Tax presets!');
    };
  }
  const pcBtn = document.getElementById('btn_proof_card');
  if (pcBtn) {
    pcBtn.onclick = () => {
      if (!lastCfg) return;
      const c = lastCfg;
      const mc = runMonteCarlo1000(c);
      const maxCac = solveMaxCac(c);
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630"><rect width="1200" height="630" fill="#080a0f"/><rect x="44" y="44" width="1112" height="542" rx="24" fill="#101521" stroke="#243047" stroke-width="2"/><text x="86" y="106" fill="#38bdf8" font-family="monospace" font-size="22" font-weight="800">IDEASTRESS // FALSIFICATION PROOF CARD</text><text x="86" y="190" fill="#fff" font-family="sans-serif" font-size="38" font-weight="800">${c.type.toUpperCase()} · ${c.cur} ${c.price} Price · ${c.cur} ${c.cash} Cash</text><text x="86" y="310" fill="#10b981" font-family="monospace" font-size="48" font-weight="800">${mc.survivalPct.toFixed(1)}% 12M SURVIVAL (1,000 RUNS)</text><text x="86" y="390" fill="#edf2fb" font-family="monospace" font-size="34">MAX VIABLE CAC: ${c.cur} ${maxCac.toFixed(2)} · P10 CASH: ${c.cur} ${Math.round(mc.p10End).toLocaleString()}</text><text x="86" y="540" fill="#8a95ad" font-family="monospace" font-size="18">Stress-tested with IdeaStress (MIT Open-Source) · ideastress.dev</text></svg>`;
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml' }));
      a.download = 'ideastress_proof_card.svg'; a.click();
      showToast('Downloaded 1200x630 Proof Card SVG!');
    };
  }
  update();
};

window.initBreakEvenTool = function() {
  const root = document.getElementById('tool-breakeven');
  if (!root) return;
  function update() {
    const p = parseFloat(document.getElementById('be_price').value) || 0;
    const v = parseFloat(document.getElementById('be_var').value) || 0;
    const r = parseFloat(document.getElementById('be_ref').value) || 0;
    const proc = document.getElementById('be_proc').value;
    const fx = parseFloat(document.getElementById('be_fixed').value) || 0;
    const vol = parseInt(document.getElementById('be_vol').value, 10) || 0;
    const fee = paymentFee(p, proc);
    const cm = p * (1 - r / 100) - v - fee;
    const units = cm > 0 ? Math.ceil(fx / cm) : null;
    const profit = vol * cm - fx;
    const al = document.getElementById('be_alert');
    al.className = 'alert-box ' + (cm <= 0 ? 'bad' : (profit >= 0 ? 'ok' : 'warn'));
    al.innerHTML = cm <= 0 ? '<strong>Unreachable Break-Even:</strong> Variable + payment fees exceed net unit price.'
      : (profit >= 0 ? `<strong>Profitable:</strong> ${vol} units/mo clears break-even (${units}) with $${Math.round(profit).toLocaleString()}/mo profit (after $${fee.toFixed(2)}/unit payment fee).`
        : `<strong>Below Break-Even:</strong> Need ${units - vol} more units/month to cover fixed costs.`);
    document.getElementById('be_kpis').innerHTML = `
      <div class="kpi"><div class="kl">Break-Even Units / Mo</div><div class="kv" style="color:var(--accent)">${units ?? 'N/A'}</div></div>
      <div class="kpi"><div class="kl">Break-Even Revenue</div><div class="kv">${units !== null ? '$' + Math.round(units * p).toLocaleString() : 'N/A'}</div></div>
      <div class="kpi"><div class="kl">Net Unit Contribution</div><div class="kv">$${cm.toFixed(2)}</div><div class="ks">Fee: $${fee.toFixed(2)}/order</div></div>
      <div class="kpi"><div class="kl">Monthly Profit @ Volume</div><div class="kv" style="color:${profit >= 0 ? 'var(--ok)':'var(--bad)'}">$${Math.round(profit).toLocaleString()}</div></div>
    `;
  }
  root.querySelectorAll('input, select').forEach(el => el.addEventListener('input', update));
  update();
};

window.initSaasTool = function() {
  const root = document.getElementById('tool-saas');
  if (!root) return;
  function update() {
    const arpa = parseFloat(document.getElementById('s_arpa').value) || 0;
    const gm = (parseFloat(document.getElementById('s_gm').value) || 0) / 100;
    const churn = (parseFloat(document.getElementById('s_churn').value) || 0) / 100;
    const cac = parseFloat(document.getElementById('s_cac').value) || 0;
    const proc = document.getElementById('s_proc').value;
    const fee = paymentFee(arpa, proc);
    const monthlyGp = Math.max(0, arpa * gm - fee);
    const ltv = churn > 0 ? monthlyGp / churn : null;
    const ratio = ltv !== null && cac > 0 ? ltv / cac : null;
    const payback = monthlyGp > 0 ? cac / monthlyGp : null;
    const al = document.getElementById('s_alert');
    al.className = 'alert-box ' + (!ratio ? 'warn' : (ratio < 3 ? 'bad' : 'ok'));
    al.innerHTML = !ratio ? 'Enter non-zero churn and CAC.'
      : (ratio < 3 ? `<strong>Fragile SaaS Economics (${ratio.toFixed(2)}x):</strong> Below 3.0x baseline (2026 median is 4.1x).`
        : `<strong>Healthy Ratio (${ratio.toFixed(2)}x):</strong> Clears 3.0x baseline after $${fee.toFixed(2)}/mo processing fee.`);
    document.getElementById('s_kpis').innerHTML = `
      <div class="kpi"><div class="kl">Net Gross-Margin LTV</div><div class="kv" style="color:var(--accent)">${ltv !== null ? '$' + Math.round(ltv).toLocaleString() : 'N/A'}</div></div>
      <div class="kpi"><div class="kl">LTV : CAC Ratio</div><div class="kv" style="color:${ratio && ratio >= 3 ? 'var(--ok)':'var(--bad)'}">${ratio !== null ? ratio.toFixed(2) + 'x' : 'N/A'}</div></div>
      <div class="kpi"><div class="kl">CAC Payback</div><div class="kv">${payback !== null ? payback.toFixed(1) + ' mo' : 'N/A'}</div><div class="ks">2026 median: 16 mo</div></div>
      <div class="kpi"><div class="kl">Avg Lifespan</div><div class="kv">${churn > 0 ? (1 / churn).toFixed(1) + ' mo' : 'N/A'}</div></div>
    `;
  }
  root.querySelectorAll('input, select').forEach(el => el.addEventListener('input', update));
  update();
};

window.initEcomTool = function() {
  const root = document.getElementById('tool-ecom');
  if (!root) return;
  function update() {
    const aov = parseFloat(document.getElementById('e_aov').value) || 0;
    const cogs = parseFloat(document.getElementById('e_cogs').value) || 0;
    const ship = parseFloat(document.getElementById('e_ship').value) || 0;
    const proc = document.getElementById('e_proc').value;
    const cpa = parseFloat(document.getElementById('e_cpa').value) || 0;
    const fee = paymentFee(aov, proc);
    const preAd = aov - cogs - ship - fee;
    const beRoas = preAd > 0 ? aov / preAd : null;
    const net = preAd - cpa;
    const al = document.getElementById('e_alert');
    al.className = 'alert-box ' + (net >= 0 ? 'ok' : 'bad');
    al.innerHTML = net >= 0
      ? `<strong>First-Order Profitable:</strong> +$${net.toFixed(2)}/order after ads & $${fee.toFixed(2)} fee. Stay above <strong>${beRoas ? beRoas.toFixed(2) : 'N/A'}x ROAS</strong>.`
      : `<strong>Losing $${Math.abs(net).toFixed(2)} / Order:</strong> Ad CPA ($${cpa}) exceeds pre-ad margin ($${preAd.toFixed(2)}).`;
    document.getElementById('e_kpis').innerHTML = `
      <div class="kpi"><div class="kl">Break-Even ROAS</div><div class="kv" style="color:var(--accent)">${beRoas !== null ? beRoas.toFixed(2) + 'x' : 'IMPOSSIBLE'}</div></div>
      <div class="kpi"><div class="kl">Pre-Ad Margin</div><div class="kv">$${preAd.toFixed(2)}</div><div class="ks">Stripe/Fee: $${fee.toFixed(2)}</div></div>
      <div class="kpi"><div class="kl">Max Profitable CPA</div><div class="kv">$${Math.max(0, preAd).toFixed(2)}</div><div class="ks">2026 US avg: $53-$91</div></div>
      <div class="kpi"><div class="kl">First-Order Net</div><div class="kv" style="color:${net >= 0 ? 'var(--ok)':'var(--bad)'}">$${net.toFixed(2)}</div></div>
    `;
  }
  root.querySelectorAll('input, select').forEach(el => el.addEventListener('input', update));
  update();
};




window.applyPreset = function(key) {
  const P = {
    healthy_saas: { type:'saas', cur:'USD', price:79, varCost:6, fixed:900, cash:15000, newC:12, spend:480, churn:4, refund:1, cpc:4.20, cvr:3.0 },
    losing_ai:    { type:'saas', cur:'USD', price:19, varCost:14, fixed:1400, cash:5000, newC:20, spend:600, churn:11, refund:3, cpc:6.50, cvr:2.0 },
    high_cpc:     { type:'saas', cur:'USD', price:49, varCost:6, fixed:900, cash:12000, newC:14, spend:560, churn:5, refund:2, cpc:8.90, cvr:2.5 }
  }[key];
  if (!P) return;
  document.getElementById('f_type').value = P.type;
  document.getElementById('f_cur').value = P.cur;
  document.getElementById('f_price').value = P.price;
  document.getElementById('f_var').value = P.varCost;
  document.getElementById('f_fixed').value = P.fixed;
  document.getElementById('f_cash').value = P.cash;
  document.getElementById('f_new').value = P.newC;
  document.getElementById('f_spend').value = P.spend;
  document.getElementById('f_churn').value = P.churn;
  document.getElementById('f_refund').value = P.refund;
  if (document.getElementById('f_cpc')) document.getElementById('f_cpc').value = P.cpc;
  if (document.getElementById('f_cvr')) document.getElementById('f_cvr').value = P.cvr;
  document.getElementById('f_price').dispatchEvent(new Event('input'));
  showToast('Loaded preset: ' + key.replace('_', ' '));
};


window.initQuitJobTool = function() {
  const root = document.getElementById('tool-quit-job');
  if (!root) return;
  function update() {
    const sal = parseFloat(document.getElementById('q_sal').value) || 0;
    const tax = Math.min(80, Math.max(0, parseFloat(document.getElementById('q_tax').value) || 0)) / 100;
    const ops = parseFloat(document.getElementById('q_ops').value) || 0;
    const price = parseFloat(document.getElementById('q_price').value) || 1;
    const proc = document.getElementById('q_proc').value;
    const feePct = proc === 'mor_paddle' ? 0.05 : 0.029;
    const feeFlat = proc === 'mor_paddle' ? 0.50 : 0.30;
    const netPerCust = price * (1 - feePct) - feeFlat;
    const preTaxNeed = (sal / 12) / Math.max(0.1, 1 - tax);
    const reqCust = netPerCust > 0 ? Math.ceil((preTaxNeed + ops) / netPerCust) : 0;
    const reqMrr = reqCust * price;
    const annStripe = reqCust * (price * 0.029 + 0.30) * 12;
    const annMor = reqCust * (price * 0.05 + 0.50) * 12;
    const diff = annMor - annStripe;
    const al = document.getElementById('q_alert');
    al.className = 'alert-box ok';
    al.innerHTML = `<strong>Quit-Safely Target: $${Math.round(reqMrr).toLocaleString()} MRR (${reqCust.toLocaleString()} customers)</strong> — Stripe US saves <strong>$${Math.round(diff).toLocaleString()}/year</strong> vs MoR (Paddle/LS), though MoR handles global VAT/sales tax.`;
    document.getElementById('q_kpis').innerHTML = `
      <div class="kpi"><div class="kl">Required MRR to Quit</div><div class="kv" style="color:var(--accent)">$${Math.round(reqMrr).toLocaleString()}</div><div class="ks">Replaces $${Math.round(sal).toLocaleString()}/yr</div></div>
      <div class="kpi"><div class="kl">Paying Customers Needed</div><div class="kv">${reqCust.toLocaleString()}</div><div class="ks">@ $${price}/mo</div></div>
      <div class="kpi"><div class="kl">Annual Stripe US Fees</div><div class="kv">$${Math.round(annStripe).toLocaleString()}</div><div class="ks">2.9% + $0.30</div></div>
      <div class="kpi"><div class="kl">Annual MoR Fees</div><div class="kv" style="color:var(--warn)">$${Math.round(annMor).toLocaleString()}</div><div class="ks">5% + $0.50 (+$${Math.round(diff).toLocaleString()}/yr)</div></div>
    `;
  }
  root.querySelectorAll('input, select').forEach(el => el.addEventListener('input', update));
  update();
};

window.initFreemiumTool = function() {
  const root = document.getElementById('tool-freemium');
  if (!root) return;
  function update() {
    const mau = parseInt(document.getElementById('fr_mau').value, 10) || 0;
    const cvr = (parseFloat(document.getElementById('fr_cvr').value) || 0) / 100;
    const price = parseFloat(document.getElementById('fr_price').value) || 0;
    const freeCost = parseFloat(document.getElementById('fr_fcost').value) || 0;
    const paidCost = parseFloat(document.getElementById('fr_pcost').value) || 0;
    const paidU = Math.round(mau * cvr);
    const freeU = Math.max(0, mau - paidU);
    const rev = paidU * price;
    const drag = freeU * freeCost;
    const paidCogs = paidU * (paidCost + price * 0.029 + 0.30);
    const gp = rev - drag - paidCogs;
    const gm = rev > 0 ? (gp / rev) * 100 : -100;
    const unitPaid = price * 0.971 - 0.30 - paidCost;
    const minCvr = (unitPaid > 0 && (unitPaid + freeCost) > 0) ? (freeCost / (unitPaid + freeCost)) * 100 : null;
    const al = document.getElementById('fr_alert');
    al.className = 'alert-box ' + (gp <= 0 ? 'bad' : (gm < 60 ? 'warn' : 'ok'));
    al.innerHTML = gp <= 0
      ? `<strong>FREEMIUM BLEEDING ($${Math.round(gp).toLocaleString()}/mo):</strong> ${freeU.toLocaleString()} free users cost $${Math.round(drag).toLocaleString()}/mo. Switch to a time-limited free trial or cut free-tier cost.`
      : `<strong>${gm < 60 ? 'COMPRESSED FREEMIUM' : 'HEALTHY FREEMIUM'} (${gm.toFixed(1)}% blended margin):</strong> Minimum conversion rate to break even on free-tier drag is <strong>${minCvr ? minCvr.toFixed(2) + '%' : 'N/A'}</strong>.`;
    document.getElementById('fr_kpis').innerHTML = `
      <div class="kpi"><div class="kl">Free-Tier Monthly Drag</div><div class="kv" style="color:var(--bad)">-$${Math.round(drag).toLocaleString()}</div><div class="ks">${freeU.toLocaleString()} free users</div></div>
      <div class="kpi"><div class="kl">Net Monthly Gross Profit</div><div class="kv" style="color:${gp >= 0 ? 'var(--ok)':'var(--bad)'}">$${Math.round(gp).toLocaleString()}</div><div class="ks">${gm.toFixed(1)}% blended margin</div></div>
      <div class="kpi"><div class="kl">Min Break-Even CVR</div><div class="kv" style="color:var(--accent)">${minCvr ? minCvr.toFixed(2) + '%' : 'N/A'}</div><div class="ks">Current: ${(cvr*100).toFixed(2)}%</div></div>
      <div class="kpi"><div class="kl">Paid Revenue / Mo</div><div class="kv">$${Math.round(rev).toLocaleString()}</div><div class="ks">${paidU.toLocaleString()} paid users</div></div>
    `;
  }
  root.querySelectorAll('input').forEach(el => el.addEventListener('input', update));
  update();
};

window.initSocialCpmTool = function() {
  const root = document.getElementById('tool-social-cpm');
  if (!root) return;
  function update() {
    const cpm = parseFloat(document.getElementById('sc_cpm').value) || 0;
    const ctr = (parseFloat(document.getElementById('sc_ctr').value) || 0) / 100;
    const cvr = (parseFloat(document.getElementById('sc_cvr').value) || 0) / 100;
    const aov = parseFloat(document.getElementById('sc_aov').value) || 0;
    const mPct = (parseFloat(document.getElementById('sc_margin').value) || 0) / 100;
    const clicks = 1000 * ctr;
    const cpc = clicks > 0 ? cpm / clicks : 999;
    const cpa = cvr > 0 ? cpc / cvr : 9999;
    const preAd = aov * mPct;
    const beRoas = preAd > 0 ? aov / preAd : null;
    const net = preAd - cpa;
    const al = document.getElementById('sc_alert');
    al.className = 'alert-box ' + (net >= 0 ? 'ok' : 'bad');
    al.innerHTML = net >= 0
      ? `<strong>SOCIAL_VIABLE (+$${net.toFixed(2)}/order):</strong> At $${cpm} CPM &amp; ${(ctr*100).toFixed(1)}% CTR, effective CPC is $${cpc.toFixed(2)} -> CPA $${cpa.toFixed(2)} vs $${preAd.toFixed(2)} pre-ad margin.`
      : `<strong>SOCIAL_UNPROFITABLE (-$${Math.abs(net).toFixed(2)}/order):</strong> Implied CPA ($${cpa.toFixed(2)}) exceeds your $${preAd.toFixed(2)} pre-ad margin. Improve creative CTR or raise AOV.`;
    document.getElementById('sc_kpis').innerHTML = `
      <div class="kpi"><div class="kl">Implied Paid Social CPA</div><div class="kv" style="color:${net >= 0 ? 'var(--ok)':'var(--bad)'}">$${cpa.toFixed(2)}</div><div class="ks">Effective CPC: $${cpc.toFixed(2)}</div></div>
      <div class="kpi"><div class="kl">Pre-Ad Margin / Order</div><div class="kv">$${preAd.toFixed(2)}</div><div class="ks">AOV: $${aov}</div></div>
      <div class="kpi"><div class="kl">Break-Even ROAS</div><div class="kv" style="color:var(--accent)">${beRoas ? beRoas.toFixed(2) + 'x' : 'N/A'}</div></div>
      <div class="kpi"><div class="kl">First-Order Net Profit</div><div class="kv" style="color:${net >= 0 ? 'var(--ok)':'var(--bad)'}">$${net.toFixed(2)}</div></div>
    `;
  }
  root.querySelectorAll('input').forEach(el => el.addEventListener('input', update));
  update();
};

window.initGeoTool = function() {
  const root = document.getElementById('tool-geo');
  if (!root) return;
  const MKTS = [
    { code: 'US', name: 'United States', cpcF: 1.00, ppF: 1.00 },
    { code: 'UK', name: 'United Kingdom', cpcF: 0.72, ppF: 0.95 },
    { code: 'DE', name: 'Germany (DACH)', cpcF: 0.58, ppF: 0.92 },
    { code: 'SG', name: 'Singapore', cpcF: 0.52, ppF: 0.90 },
    { code: 'MY', name: 'Malaysia', cpcF: 0.26, ppF: 0.55 }
  ];
  function update() {
    const usCpc = parseFloat(document.getElementById('g_cpc').value) || 0;
    const usCac = parseFloat(document.getElementById('g_cac').value) || 0;
    const cvr = Math.max(0.001, (parseFloat(document.getElementById('g_cvr').value) || 2.5) / 100);
    const rows = MKTS.map(m => {
      const cpc = usCpc * m.cpcF;
      const imp = cpc / cvr;
      const ceil = usCac * m.ppF;
      const score = imp > 0 ? ceil / imp : 0;
      const verdict = (ceil <= 0 || imp > ceil) ? 'CHANNEL_IMPOSSIBLE' : (imp > ceil * 0.75 ? 'CHANNEL_TIGHT' : 'CHANNEL_VIABLE');
      return { ...m, cpc, imp, ceil, score, verdict };
    }).sort((a, b) => b.score - a.score);
    const best = rows[0];
    document.getElementById('g_alert').className = 'alert-box ' + (best.verdict === 'CHANNEL_VIABLE' ? 'ok' : (best.verdict === 'CHANNEL_TIGHT' ? 'warn' : 'bad'));
    document.getElementById('g_alert').innerHTML = `<strong>Best Arbitrage Market: ${best.name} (${best.code})</strong> — Est. CPC $${best.cpc.toFixed(2)} -> Implied CAC $${best.imp.toFixed(2)} vs localized ceiling $${best.ceil.toFixed(2)} (Headroom: ${best.score.toFixed(2)}x).`;
    document.getElementById('g_tbody').innerHTML = rows.map(r => {
      const col = r.verdict === 'CHANNEL_VIABLE' ? 'var(--ok)' : (r.verdict === 'CHANNEL_TIGHT' ? 'var(--warn)' : 'var(--bad)');
      return `<tr><td><strong>${r.name} (${r.code})</strong></td><td class="mono">$${r.cpc.toFixed(2)}</td><td class="mono">$${r.imp.toFixed(2)}</td><td class="mono">$${r.ceil.toFixed(2)}</td><td class="mono" style="color:${col};font-weight:700;">${r.verdict} (${r.score.toFixed(2)}x)</td></tr>`;
    }).join('');
  }
  root.querySelectorAll('input').forEach(el => el.addEventListener('input', update));
  update();
};

window.initAiMarginTool = function() {
  const root = document.getElementById('tool-ai-margin');
  if (!root) return;
  const PRESETS = {
    budget_fast: [0.15, 0.60],
    mid_balanced: [1.25, 5.00],
    frontier_reasoning: [3.00, 15.00]
  };
  function update() {
    const price = parseFloat(document.getElementById('ai_price').value) || 0;
    const reqs = parseInt(document.getElementById('ai_reqs').value, 10) || 0;
    const inTok = parseInt(document.getElementById('ai_in').value, 10) || 0;
    const outTok = parseInt(document.getElementById('ai_out').value, 10) || 0;
    const [inR, outR] = PRESETS[document.getElementById('ai_model').value] || [1.25, 5.00];
    const costPerReq = (inTok / 1e6) * inR + (outTok / 1e6) * outR;
    const aiCogs = costPerReq * reqs * 30;
    const stripe = price * 0.029 + 0.30;
    const totalVar = aiCogs + stripe + 1.0;
    const gp = price - totalVar;
    const gm = price > 0 ? (gp / price) * 100 : 0;
    const netBudget = price - stripe - 1.0;
    const whale = (costPerReq > 0 && netBudget > 0) ? Math.floor((netBudget / costPerReq) / 30) : 0;
    const al = document.getElementById('ai_alert');
    al.className = 'alert-box ' + (gp <= 0 ? 'bad' : (gm < 60 ? 'warn' : 'ok'));
    al.innerHTML = gp <= 0
      ? `<strong>NEGATIVE UNIT MARGIN:</strong> Average user costs $${totalVar.toFixed(2)}/mo vs $${price.toFixed(2)}/mo price. Add usage caps or switch to a faster model.`
      : `<strong>${gm < 60 ? 'COMPRESSED AI MARGIN' : 'HEALTHY AI MARGIN'} (${gm.toFixed(1)}%):</strong> Any power user running more than <strong>${whale} requests/day</strong> loses you money.`;
    document.getElementById('ai_kpis').innerHTML = `
      <div class="kpi"><div class="kl">Real AI Gross Margin</div><div class="kv" style="color:${gm >= 60 ? 'var(--ok)':'var(--bad)'}">${gm.toFixed(1)}%</div><div class="ks">Traditional SaaS: 80%</div></div>
      <div class="kpi"><div class="kl">Monthly LLM Token COGS</div><div class="kv" style="color:var(--accent)">$${aiCogs.toFixed(2)}</div><div class="ks">$${costPerReq.toFixed(5)} / req</div></div>
      <div class="kpi"><div class="kl">Whale Bankruptcy Limit</div><div class="kv" style="color:var(--warn)">${whale} req/day</div><div class="ks">Break-even usage cap</div></div>
      <div class="kpi"><div class="kl">Net Profit / User / Mo</div><div class="kv" style="color:${gp >= 0 ? 'var(--ok)':'var(--bad)'}">$${gp.toFixed(2)}</div><div class="ks">After Stripe ($${stripe.toFixed(2)})</div></div>
    `;
  }
  root.querySelectorAll('input, select').forEach(el => el.addEventListener('input', update));
  update();
};

window.initRunwayTool = function() {
  const root = document.getElementById('tool-runway');
  if (!root) return;
  function simR(cash, rev, grow, burn) {
    let c = cash, r = rev;
    for (let m = 1; m <= 60; m++) {
      c += r - burn;
      if (c < 0) return m - 1;
      r *= (1 + grow / 100);
    }
    return 60;
  }
  function update() {
    const cash = parseFloat(document.getElementById('r_cash').value) || 0;
    const rev = parseFloat(document.getElementById('r_rev').value) || 0;
    const grow = parseFloat(document.getElementById('r_grow').value) || 0;
    const burn = parseFloat(document.getElementById('r_burn').value) || 0;
    const baseM = simR(cash, rev, grow, burn);
    const stressM = simR(cash, rev * 0.7, grow * 0.5, burn * 1.2);
    const al = document.getElementById('r_alert');
    al.className = 'alert-box ' + (stressM >= 12 ? 'ok' : (stressM >= 6 ? 'warn' : 'bad'));
    al.innerHTML = stressM >= 60 ? '<strong>Self-Sustaining</strong> even under a -30% revenue &amp; +20% expense shock.'
      : `<strong>Downside Shock Runway: ${stressM} months</strong> (Base: ${baseM >= 60 ? '60+ mo' : baseM + ' mo'}).`;
    document.getElementById('r_kpis').innerHTML = `
      <div class="kpi"><div class="kl">Current Net Burn</div><div class="kv">$${Math.round(burn - rev).toLocaleString()}/mo</div></div>
      <div class="kpi"><div class="kl">Base Runway</div><div class="kv" style="color:var(--accent)">${baseM >= 60 ? '60+ mo' : baseM + ' mo'}</div></div>
      <div class="kpi"><div class="kl">Shock Runway (-30% rev / +20% cost)</div><div class="kv" style="color:${stressM >= 12 ? 'var(--ok)':'var(--bad)'}">${stressM >= 60 ? '60+ mo' : stressM + ' mo'}</div></div>
    `;
  }
  root.querySelectorAll('input').forEach(el => el.addEventListener('input', update));
  update();
};
