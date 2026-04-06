// ===== THEME TOGGLE =====
(function () {
  const t = document.querySelector('[data-theme-toggle]'),
    r = document.documentElement;
  let d = matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light';
  r.setAttribute('data-theme', d);
  function updateIcon() {
    if (!t) return;
    t.setAttribute('aria-label', 'Switch to ' + (d === 'dark' ? 'light' : 'dark') + ' mode');
    t.innerHTML = d === 'dark'
      ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
      : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  }
  updateIcon();
  t && t.addEventListener('click', () => {
    d = d === 'dark' ? 'light' : 'dark';
    r.setAttribute('data-theme', d);
    updateIcon();
    // Redraw charts with new colors
    drawInfluenceChart();
    drawTimeline(currentFilter);
  });
})();

// ===== UTILITY =====
function getCSS(varName) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
}

// ===== TOOLTIP =====
const tooltip = document.createElement('div');
tooltip.className = 'chart-tooltip';
document.body.appendChild(tooltip);

function showTooltip(html, event) {
  tooltip.innerHTML = html;
  tooltip.classList.add('visible');
  const rect = tooltip.getBoundingClientRect();
  let x = event.clientX + 16;
  let y = event.clientY - 10;
  if (x + rect.width > window.innerWidth - 20) x = event.clientX - rect.width - 16;
  if (y + rect.height > window.innerHeight - 20) y = event.clientY - rect.height - 10;
  if (y < 10) y = 10;
  tooltip.style.left = x + 'px';
  tooltip.style.top = y + 'px';
}

function hideTooltip() {
  tooltip.classList.remove('visible');
}

// ===== INFLUENCE CHART =====
let currentView = 'stacked';
let hiddenFactions = new Set();

function drawInfluenceChart() {
  const container = document.getElementById('influence-chart');
  container.innerHTML = '';

  const bounds = container.getBoundingClientRect();
  const margin = { top: 30, right: 30, bottom: 50, left: 50 };
  const width = Math.max(bounds.width, 600) - margin.left - margin.right;
  const height = Math.max(bounds.height, 380) - margin.top - margin.bottom;

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom);

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  // Filter visible factions
  const visibleFactions = FACTIONS.filter(f => !hiddenFactions.has(f.id));
  const keys = visibleFactions.map(f => f.id);

  // Scale
  const x = d3.scaleLinear()
    .domain([1, 1300])
    .range([0, width]);

  // Stack
  const stack = d3.stack()
    .keys(keys)
    .order(d3.stackOrderNone);

  if (currentView === 'stream') {
    stack.offset(d3.stackOffsetSilhouette);
  } else if (currentView === 'expanded') {
    stack.offset(d3.stackOffsetExpand);
  } else {
    stack.offset(d3.stackOffsetNone);
  }

  const series = stack(INFLUENCE_DATA);

  // Y domain
  let yMax;
  if (currentView === 'expanded') {
    yMax = 1;
  } else if (currentView === 'stream') {
    const allVals = series.flat().flatMap(d => [d[0], d[1]]);
    yMax = d3.max(allVals);
    var yMin = d3.min(allVals);
  } else {
    yMax = d3.max(series, s => d3.max(s, d => d[1]));
  }

  const y = d3.scaleLinear()
    .domain(currentView === 'stream' ? [yMin, yMax] : [0, yMax])
    .range([height, 0]);

  // Era bands
  const eras = [
    { start: 1, end: 220, label: 'Four Empires Era' },
    { start: 220, end: 618, label: 'Fragmentation' },
    { start: 618, end: 907, label: 'Tang Golden Age' },
    { start: 907, end: 1206, label: 'Islamic Dominance' },
    { start: 1206, end: 1300, label: 'Pax Mongolica' },
  ];

  const eraColors = ['#9e5a2e', '#3a8a7c', '#c4443a', '#3d7a3d', '#5b7fa5'];

  eras.forEach((era, i) => {
    g.append('rect')
      .attr('class', 'era-band')
      .attr('x', x(era.start))
      .attr('y', 0)
      .attr('width', x(era.end) - x(era.start))
      .attr('height', height)
      .attr('fill', eraColors[i]);

    g.append('text')
      .attr('x', x((era.start + era.end) / 2))
      .attr('y', 14)
      .attr('text-anchor', 'middle')
      .attr('font-family', getCSS('--font-body'))
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', getCSS('--color-text-faint'))
      .attr('letter-spacing', '0.03em')
      .text(era.label);
  });

  // Grid
  g.append('g')
    .attr('class', 'grid')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x)
      .tickValues([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300])
      .tickSize(-height)
      .tickFormat(''));

  // Area generator
  const area = d3.area()
    .x(d => x(d.data.year))
    .y0(d => y(d[0]))
    .y1(d => y(d[1]))
    .curve(d3.curveBasis);

  // Draw areas
  const paths = g.selectAll('.area-layer')
    .data(series)
    .join('path')
    .attr('class', 'area-layer')
    .attr('d', area)
    .attr('fill', (d, i) => visibleFactions[i].color)
    .attr('fill-opacity', 0.8)
    .attr('stroke', (d, i) => visibleFactions[i].color)
    .attr('stroke-width', 0.5)
    .attr('stroke-opacity', 0.5);

  // Axes
  const xAxis = g.append('g')
    .attr('class', 'axis')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x)
      .tickValues([1, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300])
      .tickFormat(d => d + ' AD'));

  xAxis.selectAll('text')
    .attr('font-size', '11px');

  if (currentView !== 'stream') {
    const yAxis = g.append('g')
      .attr('class', 'axis')
      .call(d3.axisLeft(y).ticks(5)
        .tickFormat(currentView === 'expanded' ? d3.format('.0%') : d3.format('d')));

    yAxis.selectAll('text')
      .attr('font-size', '11px');
  }

  // Hover interaction
  const hoverLine = g.append('line')
    .attr('stroke', getCSS('--color-text-faint'))
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '4,3')
    .attr('y1', 0)
    .attr('y2', height)
    .style('opacity', 0);

  const overlay = g.append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'transparent')
    .on('mousemove', function (event) {
      const [mx] = d3.pointer(event);
      const year = Math.round(x.invert(mx));
      const clamped = Math.max(1, Math.min(1300, year));

      hoverLine
        .attr('x1', x(clamped))
        .attr('x2', x(clamped))
        .style('opacity', 1);

      // Interpolate data at this year
      const bisect = d3.bisector(d => d.year).left;
      const idx = bisect(INFLUENCE_DATA, clamped);
      const d0 = INFLUENCE_DATA[Math.max(0, idx - 1)];
      const d1 = INFLUENCE_DATA[Math.min(INFLUENCE_DATA.length - 1, idx)];
      let interp = {};
      if (d0 && d1 && d0.year !== d1.year) {
        const t = (clamped - d0.year) / (d1.year - d0.year);
        keys.forEach(k => interp[k] = d0[k] + t * (d1[k] - d0[k]));
      } else {
        const dd = d0 || d1;
        keys.forEach(k => interp[k] = dd[k]);
      }

      // Build tooltip
      let rows = '';
      const sorted = visibleFactions
        .map(f => ({ ...f, val: interp[f.id] || 0 }))
        .filter(f => f.val > 0.5)
        .sort((a, b) => b.val - a.val);

      sorted.forEach(f => {
        rows += `<div class="tooltip-row">
          <span class="tooltip-swatch" style="background:${f.color}"></span>
          <span class="tooltip-label">${f.name}</span>
          <span class="tooltip-value">${Math.round(f.val)}</span>
        </div>`;
      });

      showTooltip(`<div class="tooltip-year">${Math.round(clamped)} AD</div>${rows}`, event);

      // Highlight
      paths.attr('fill-opacity', (d, i) => {
        const fid = visibleFactions[i].id;
        return (interp[fid] || 0) > 0.5 ? 0.85 : 0.3;
      });
    })
    .on('mouseleave', function () {
      hoverLine.style('opacity', 0);
      hideTooltip();
      paths.attr('fill-opacity', 0.8);
    });

  // Legend
  drawLegend();
}

function drawLegend() {
  const legendEl = document.getElementById('influence-legend');
  legendEl.innerHTML = '';
  FACTIONS.forEach(f => {
    const item = document.createElement('div');
    item.className = 'legend-item' + (hiddenFactions.has(f.id) ? ' dimmed' : '');
    item.innerHTML = `<span class="legend-swatch" style="background:${f.color}"></span><span>${f.name}</span>`;
    item.addEventListener('click', () => {
      if (hiddenFactions.has(f.id)) {
        hiddenFactions.delete(f.id);
      } else {
        hiddenFactions.add(f.id);
      }
      drawInfluenceChart();
    });
    legendEl.appendChild(item);
  });
}

// Chart view buttons
document.querySelectorAll('.chart-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentView = btn.dataset.view;
    drawInfluenceChart();
  });
});


// ===== TIMELINE CHART =====
let currentFilter = 'all';

function drawTimeline(filter) {
  const container = document.getElementById('timeline-chart');
  container.innerHTML = '';

  const filtered = filter === 'all' ? EVENTS : EVENTS.filter(e => e.type === filter);

  const bounds = container.getBoundingClientRect();
  const margin = { top: 20, right: 50, bottom: 50, left: 50 };

  // Width is based on container or enough for events
  const minWidth = Math.max(bounds.width - 2, 900);
  const neededWidth = Math.max(minWidth, filtered.length * 90 + margin.left + margin.right);
  const width = neededWidth - margin.left - margin.right;
  const height = 540;

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom);

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  const x = d3.scaleLinear()
    .domain([1, 1300])
    .range([0, width]);

  const typeColors = {
    political: '#5b7fa5',
    military: '#b35a4a',
    trade: '#7a9a5a',
  };

  // Era backgrounds
  const eras = [
    { start: 1, end: 220, label: 'Four Empires', shade: '#9e5a2e' },
    { start: 220, end: 618, label: 'Fragmentation & Sassanids', shade: '#3a8a7c' },
    { start: 618, end: 907, label: 'Tang Golden Age', shade: '#c4443a' },
    { start: 907, end: 1206, label: 'Islamic Dominance', shade: '#3d7a3d' },
    { start: 1206, end: 1300, label: 'Mongol Conquests', shade: '#5b7fa5' },
  ];

  eras.forEach((era) => {
    g.append('rect')
      .attr('x', x(era.start))
      .attr('y', 0)
      .attr('width', x(era.end) - x(era.start))
      .attr('height', height)
      .attr('fill', era.shade)
      .attr('opacity', 0.05);

    g.append('text')
      .attr('x', x((era.start + era.end) / 2))
      .attr('y', height + 36)
      .attr('text-anchor', 'middle')
      .attr('font-family', getCSS('--font-display'))
      .attr('font-size', '12px')
      .attr('font-weight', '500')
      .attr('fill', getCSS('--color-text-faint'))
      .text(era.label);
  });

  // Central timeline axis at middle
  const axisY = height * 0.5;

  g.append('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', axisY)
    .attr('y2', axisY)
    .attr('stroke', getCSS('--color-border'))
    .attr('stroke-width', 2);

  // Century markers on axis
  for (let yr = 100; yr <= 1300; yr += 100) {
    g.append('line')
      .attr('x1', x(yr))
      .attr('x2', x(yr))
      .attr('y1', axisY - 6)
      .attr('y2', axisY + 6)
      .attr('stroke', getCSS('--color-border'))
      .attr('stroke-width', 1.5);

    g.append('text')
      .attr('x', x(yr))
      .attr('y', axisY + 22)
      .attr('text-anchor', 'middle')
      .attr('font-family', getCSS('--font-body'))
      .attr('font-size', '11px')
      .attr('font-weight', '500')
      .attr('fill', getCSS('--color-text-muted'))
      .text(yr);
  }

  // Assign stagger lanes to avoid overlap
  // Sort by year, alternate above/below, and vary stem lengths
  const sorted = [...filtered].sort((a, b) => a.year - b.year);
  const lanes = [1, 2, 3]; // 3 levels of stem length
  let laneIdx = 0;

  const positioned = sorted.map((evt, i) => {
    const above = i % 2 === 0;
    const lane = lanes[laneIdx % lanes.length];
    laneIdx++;
    return { ...evt, above, lane };
  });

  // Draw stems and dots
  positioned.forEach((evt) => {
    const cx = x(evt.year);
    const baseStem = height * 0.14;
    const laneOffset = evt.lane * baseStem * 0.65;
    const stemLen = baseStem + laneOffset;
    const ey = evt.above ? axisY - stemLen : axisY + stemLen;
    const color = typeColors[evt.type];

    // Stem line
    g.append('line')
      .attr('x1', cx)
      .attr('x2', cx)
      .attr('y1', axisY)
      .attr('y2', ey)
      .attr('stroke', color)
      .attr('stroke-width', 1)
      .attr('stroke-opacity', 0.35)
      .attr('stroke-dasharray', '2,2');

    // Dot on axis
    g.append('circle')
      .attr('class', 'event-dot')
      .attr('cx', cx)
      .attr('cy', axisY)
      .attr('r', 5)
      .attr('fill', color)
      .attr('stroke', getCSS('--color-surface-2'))
      .attr('stroke-width', 2)
      .on('mouseover', function (event) {
        d3.select(this).attr('r', 8);
        const typeLabel = evt.type.charAt(0).toUpperCase() + evt.type.slice(1);
        showTooltip(`
          <div class="event-tooltip-title">${evt.title}</div>
          <div class="event-tooltip-year">${evt.year} AD</div>
          <div class="event-tooltip-desc">${evt.desc}</div>
          <span class="event-tooltip-type ${evt.type}">${typeLabel}</span>
        `, event);
      })
      .on('mouseleave', function () {
        d3.select(this).attr('r', 5);
        hideTooltip();
      });

    // Small dot at label end
    g.append('circle')
      .attr('cx', cx)
      .attr('cy', ey)
      .attr('r', 3)
      .attr('fill', color)
      .attr('fill-opacity', 0.5);

    // Label near end of stem
    const labelLines = wrapText(evt.title, 16);
    const lineHeight = 12;
    const totalLabelH = labelLines.length * lineHeight;

    if (evt.above) {
      // Labels go above the endpoint
      labelLines.forEach((line, li) => {
        g.append('text')
          .attr('x', cx)
          .attr('y', ey - 8 - totalLabelH + (li + 1) * lineHeight)
          .attr('text-anchor', 'middle')
          .attr('font-family', getCSS('--font-body'))
          .attr('font-size', '10px')
          .attr('font-weight', '500')
          .attr('fill', getCSS('--color-text-muted'))
          .text(line);
      });
    } else {
      // Labels go below the endpoint
      labelLines.forEach((line, li) => {
        g.append('text')
          .attr('x', cx)
          .attr('y', ey + 12 + li * lineHeight)
          .attr('text-anchor', 'middle')
          .attr('font-family', getCSS('--font-body'))
          .attr('font-size', '10px')
          .attr('font-weight', '500')
          .attr('fill', getCSS('--color-text-muted'))
          .text(line);
      });
    }

    // Year label next to axis dot
    g.append('text')
      .attr('x', cx)
      .attr('y', evt.above ? axisY + 36 : axisY - 12)
      .attr('text-anchor', 'middle')
      .attr('font-family', getCSS('--font-body'))
      .attr('font-size', '9px')
      .attr('font-weight', '400')
      .attr('fill', getCSS('--color-text-faint'))
      .text(evt.year + ' AD');
  });
}

function wrapText(text, maxChars) {
  const words = text.split(' ');
  const lines = [];
  let current = '';
  words.forEach(w => {
    if ((current + ' ' + w).trim().length > maxChars && current) {
      lines.push(current.trim());
      current = w;
    } else {
      current = (current + ' ' + w).trim();
    }
  });
  if (current) lines.push(current.trim());
  return lines;
}

// Timeline filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    drawTimeline(currentFilter);
  });
});


// ===== INIT =====
function init() {
  drawInfluenceChart();
  drawTimeline('all');
}

// Resize handler
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    drawInfluenceChart();
    drawTimeline(currentFilter);
  }, 200);
});

init();
