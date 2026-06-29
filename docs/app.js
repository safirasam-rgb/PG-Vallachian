const SECTOR_ORDER = ['S', 'SV', 'V', 'JV', 'J', 'JZ', 'Z', 'SZ'];

function colorForScore(score) {
  if (score > 90) return 'rgba(0, 180, 85, .92)';
  if (score >= 80) return 'rgba(31, 158, 92, .88)';
  if (score >= 60) return 'rgba(125, 211, 123, .84)';
  if (score >= 40) return 'rgba(217, 182, 76, .84)';
  return 'rgba(224, 95, 95, .78)';
}

function textColorForScore(score) {
  if (score > 90) return 'var(--rich-good)';
  if (score >= 80) return 'var(--good)';
  if (score >= 60) return 'var(--light-good)';
  if (score >= 40) return 'var(--mid)';
  return 'var(--bad)';
}

function fmt(value, digits = 1) {
  return value === null || value === undefined || Number.isNaN(Number(value))
    ? '?'
    : Number(value).toFixed(digits);
}

function fmtMeters(value) {
  return value === null || value === undefined || Number.isNaN(Number(value))
    ? '? m'
    : `${Math.round(Number(value) / 100) * 100} m`;
}

function sectorMap(day) {
  const map = {};
  for (const item of day.sector_scores || []) map[item.sector] = item;
  return map;
}

function setRoseColors(card, day) {
  const map = sectorMap(day);
  for (const sector of SECTOR_ORDER) {
    card.style.setProperty(
      `--rose-${sector.toLowerCase()}`,
      colorForScore((map[sector] || { score: 0 }).score),
    );
  }
}

function renderSectors(card, day) {
  const container = card.querySelector('.sectors');
  container.innerHTML = '';
  for (const item of (day.sector_scores || []).slice(0, 8)) {
    const row = document.createElement('div');
    row.className = 'sector-row';
    row.style.color = textColorForScore(item.score);
    row.innerHTML = `<strong>${item.sector}</strong><div class="bar"><div class="fill" style="--w:${Math.max(0, Math.min(100, item.score))}%"></div></div><span>${Math.round(item.score)}/100</span>`;
    container.appendChild(row);
  }
}

function renderDay(day) {
  const template = document.getElementById('day-template');
  const card = template.content.firstElementChild.cloneNode(true);
  const global = day.global || {};
  const scores = day.scores || {};
  const thermal = scores.thermal || {};
  const ceiling = scores.ceiling || {};
  const storm = (day.risks && day.risks.storm) || {};
  const vli = Math.round(scores.vli ?? 0);
  const direction = global.direction_deg ?? null;

  card.querySelector('.relative').textContent = day.web_label || '';
  card.querySelector('.date').textContent = day.date_label || day.target_date || '';
  card.querySelector('.vli').textContent = vli;
  card.querySelector('.score-badge').style.color = textColorForScore(vli);
  card.querySelector('.arrow').style.setProperty('--deg', `${direction ?? 0}deg`);
  setRoseColors(card, day);

  card.querySelector('.wind-line').textContent = `Vitr z ${direction ?? '?'} deg - ${fmt(global.mean_wind_ms)}/${fmt(global.max_gust_ms)} m/s - stabilita ${global.stability_1to5 ?? '?'}/5`;
  card.querySelector('.verdict').textContent = day.verdict || 'Bez slovniho verdiktu.';
  card.querySelector('.thermal').textContent = `${Math.round(thermal.score ?? 0)}/100`;
  card.querySelector('.ceiling').textContent = `${Math.round(ceiling.score ?? 0)}/100 - ${fmtMeters(ceiling.estimated_ceiling_m)}`;
  card.querySelector('.storm').textContent = storm.risk || '?';
  card.querySelector('.stability').textContent = `${global.stability_1to5 ?? '?'} / 5`;

  renderSectors(card, day);
  return card;
}

async function main() {
  const response = await fetch('./data/latest.json', { cache: 'no-store' });
  if (!response.ok) throw new Error(`Nepodarilo se nacist data: ${response.status}`);
  const data = await response.json();

  document.getElementById('today-title').textContent = `Dnes je: ${data.today_label}`;
  document.getElementById('generated').textContent = `Lokalita: ${data.location?.name || 'Valassko'} - vygenerovano ${new Date(data.generated_at).toLocaleString('cs-CZ')}`;

  const cards = document.getElementById('cards');
  cards.innerHTML = '';
  for (const day of data.days || []) cards.appendChild(renderDay(day));

  const today = (data.days || [])[0];
  if (today) {
    const score = Math.round(today.scores?.vli ?? 0);
    const heroScore = document.getElementById('hero-score');
    heroScore.textContent = score;
    heroScore.style.color = textColorForScore(score);
    heroScore.style.background = `conic-gradient(${colorForScore(score)} 0deg ${score * 3.6}deg, rgba(255,255,255,.08) ${score * 3.6}deg 360deg)`;
  }
}

main().catch((error) => {
  console.error(error);
  document.getElementById('today-title').textContent = 'Nepodarilo se nacist PG index';
  document.getElementById('generated').textContent = error.message;
});
