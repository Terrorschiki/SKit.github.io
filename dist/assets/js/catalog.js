/* ==========================================================================
   SKit — catalog browser: search, filter, sort, paginate, add to quotation
   Expects #catalog[data-set="L|P|S|all"][data-base=""]
   ========================================================================== */
(function () {
  'use strict';

  var root = document.getElementById('catalog');
  if (!root) return;

  var SETKEY = root.getAttribute('data-set') || 'all';
  var PER_PAGE = 48;
  var state = { all: [], view: [], page: 1, q: '', cat: 'all', mat: 'all', sort: 'code',
                layout: SKIT.store('skit.layout') || 'grid' };

  function base() { return (typeof window.SKIT_BASE === 'string' ? window.SKIT_BASE : ''); }
  function u(p) { return base() + p; }
  function T(k, v) { return SKIT.t(k, v); }

  var els = {
    grid: document.getElementById('prodGrid'),
    count: document.getElementById('resultCount'),
    pager: document.getElementById('pager'),
    search: document.getElementById('searchInput'),
    cat: document.getElementById('catFilter'),
    mat: document.getElementById('matFilter'),
    sort: document.getElementById('sortSelect'),
    chips: document.getElementById('catChips'),
    viewBtns: document.querySelectorAll('[data-layout]'),
    searchWrap: document.querySelector('.search-wrap')
  };

  // ------------------------------------------------------------------ helpers
  function displayName(p) {
    if (SKIT.lang === 'zh') return p.name_zh || p.name_en || p.code;
    return p.name_en || p.name_zh || p.code;
  }
  function catLabel(p) {
    var key = 'cat.' + (p.cat || 'utensils');
    var v = T(key);
    if (v && v !== key) return v;
    return SKIT.lang === 'zh' ? (p.cat_label_zh || p.cat_label || p.cat) : (p.cat_label || p.cat);
  }
  function secondaryName(p) {
    if (SKIT.lang === 'zh') return p.name_en || '';
    return p.name_zh || '';
  }
  function searchBlob(p) {
    return [p.code, p.name_zh, p.name_en, p.material, p.material_en, p.size, p.packing,
            p.packing_en, p.note, p.note_en, p.colour, p.colour_en, p.cat_label]
      .join(' ').toLowerCase();
  }
  function materialKey(p) {
    var m = (p.material || '').toLowerCase().replace(/[\s\-_]/g, '');
    if (/硅胶|silicone/.test(m)) return 'silicone';
    if (/尼龙|nylon/.test(m)) return 'nylon';
    if (/木|wood|beech|sapele|rubber/.test(m)) return 'wood';
    if (/不锈钢|stainless|ss|\d{3}/.test(m)) return 'steel';
    if (/pp|塑料|plastic|abs|tpr/.test(m)) return 'plastic';
    return 'other';
  }
  var MAT_LABELS = {
    wood: 'material.wood', steel: 'material.steel', silicone: 'material.silicone',
    nylon: 'material.nylon', plastic: 'material.plastic', other: 'material.other'
  };

  /* The sheets are bilingual or Chinese-only in places; translate the short
     enumerable values so non-Chinese visitors read English throughout. */
  var PACKING = {
    '绑卡': 'Carded', '彩盒': 'Colour box', '清装': 'Bulk', '吊卡': 'Blister card',
    'PP袋': 'PP bag', 'OPP袋': 'OPP bag', '白盒': 'White box', '礼盒': 'Gift box',
    '吸塑': 'Blister', '散装': 'Loose'
  };
  var COLOURS = {
    '黑色': 'Black', '白色': 'White', '灰色': 'Grey', '绿色': 'Green', '红色': 'Red',
    '蓝色': 'Blue', '银色': 'Silver', '粉色': 'Pink', '米色': 'Beige', '棕色': 'Brown',
    '原木色': 'Natural wood', '黑': 'Black', '白': 'White', '灰': 'Grey', '绿': 'Green',
    '彩': 'Assorted'
  };

  function localizeList(value, dict) {
    if (!value) return '';
    if (SKIT.lang === 'zh') return String(value);
    return String(value).split(/\s*[\/,、]\s*/).map(function (part) {
      var p = part.trim();
      if (!p) return '';
      if (dict[p]) return dict[p];
      var cleaned = p.replace(/[\u4e00-\u9fff]/g, '').trim();
      return cleaned || p;
    }).filter(Boolean).join(' / ');
  }

  function packShort(value, valueEn) {
    if (SKIT.lang === 'zh') return String(value || valueEn || '');
    return valueEn || localizeList(value, PACKING);
  }
  function colourShort(value, valueEn) {
    if (SKIT.lang === 'zh') return String(value || valueEn || '');
    return valueEn || localizeList(value, COLOURS);
  }

  /* Compact material for cards: "Sapele wood + 420SS + 430SS". The detail page
     spells the grades out in full. */
  function materialShort(p) {
    var raw = p.material || '';
    if (SKIT.lang === 'zh') return raw;
    var full = p.material_en || raw;
    if (!/stainless steel/i.test(full)) return full;
    return full.replace(/\s*stainless steel/gi, 'SS').replace(/\s*\+\s*/g, ' + ').trim();
  }

  // ------------------------------------------------------------------ render
  function card(p) {
    var img = u('assets/products/') + p.id + '-thumb.jpg';
    var full = u('assets/products/') + p.id + '-card.jpg';
    var href = u('products/') + p.id + '.html';
    var payload = SKIT.esc(JSON.stringify({
      id: p.id, code: p.code, name_zh: p.name_zh, name_en: p.name_en,
      price: p.price, qty: p.qty, size: p.size, set: p.set
    }));
    var specs = [
      ['spec.size', p.size],
      ['spec.packing', packShort(p.packing, p.packing_en)],
      ['spec.material', materialShort(p)],
      ['spec.gw', p.gw],
      ['spec.cbm', p.cbm],
      ['spec.colour', colourShort(p.colour, p.colour_en)]
    ].filter(function (s) { return s[1]; }).slice(0, 4).map(function (s) {
      return '<div class="spec"><span>' + T(s[0]) + '</span><span title="' + SKIT.esc(s[1]) + '">' +
        SKIT.esc(s[1]) + '</span></div>';
    }).join('');

    return '<article class="prod-card" data-id="' + p.id + '">' +
      '<div class="prod-media">' +
        '<a href="' + href + '" aria-label="' + SKIT.esc(displayName(p)) + '">' +
          '<img src="' + img + '" alt="' + SKIT.esc(displayName(p)) + ' — ' + SKIT.esc(p.code) +
          '" loading="lazy" decoding="async" width="520" height="390">' +
        '</a>' +
        '<span class="prod-set">' + (p.set === 'S' ? 'Silicone &amp; Nylon' : p.set + '-Handle') + '</span>' +
        '<button class="prod-zoom" type="button" data-zoom="' + full + '" title="' + T('product.zoom') + '">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5M11 8v6M8 11h6"/></svg>' +
        '</button>' +
      '</div>' +
      '<div class="prod-body">' +
        '<h3 class="prod-name"><a href="' + href + '">' + SKIT.esc(displayName(p)) + '</a></h3>' +
        '<div class="prod-sub">' + SKIT.esc(secondaryName(p)) + '</div>' +
        '<div><span class="prod-code">' + SKIT.esc(p.code || '—') + '</span></div>' +
        '<div class="prod-specs">' + specs + '</div>' +
        '<div class="prod-foot">' +
          '<div class="price"><b>' + SKIT.money(p.price) + '</b>' +
            '<small>' + T('spec.perPiece') + ' · ' + T('spec.moq') + ' ' + SKIT.esc(p.qty || '—') + '</small>' +
          '</div>' +
          '<button class="add-btn" type="button" data-add="' + payload + '" title="' + T('product.addQuote') + '" aria-label="' + T('product.addQuote') + '">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>' +
          '</button>' +
        '</div>' +
      '</div>' +
    '</article>';
  }

  function render() {
    if (!els.grid) return;
    if (!state.view.length) {
      els.grid.classList.remove('list');
      els.grid.innerHTML = '<div class="empty" style="grid-column:1/-1">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>' +
        '<h3>' + T('catalog.noResults') + '</h3><p>' + T('catalog.noResults2') + '</p>' +
        '<button class="btn btn-ghost btn-sm" data-reset>' + T('catalog.reset') + '</button></div>';
    } else {
      var start = (state.page - 1) * PER_PAGE;
      var slice = state.view.slice(start, start + PER_PAGE);
      els.grid.classList.toggle('list', state.layout === 'list');
      els.grid.innerHTML = slice.map(card).join('');
    }
    if (els.count) {
      // the template carries the <b> markup, so inject it unescaped
      els.count.innerHTML = T('catalog.showing', {
        from: state.view.length ? (state.page - 1) * PER_PAGE + 1 : 0,
        to: Math.min(state.page * PER_PAGE, state.view.length),
        total: state.view.length
      });
    }
    renderPager();
    document.dispatchEvent(new CustomEvent('skit:catalogRendered'));
  }

  function renderPager() {
    if (!els.pager) return;
    var pages = Math.ceil(state.view.length / PER_PAGE);
    if (pages <= 1) { els.pager.innerHTML = ''; return; }
    var html = '<button data-page="' + (state.page - 1) + '"' + (state.page === 1 ? ' disabled' : '') + '>‹</button>';
    var list = [];
    for (var i = 1; i <= pages; i++) {
      if (i === 1 || i === pages || Math.abs(i - state.page) <= 1) list.push(i);
      else if (list[list.length - 1] !== '…') list.push('…');
    }
    list.forEach(function (i) {
      if (i === '…') html += '<span class="gap">…</span>';
      else html += '<button data-page="' + i + '"' + (i === state.page ? ' aria-current="page"' : '') + '>' + i + '</button>';
    });
    html += '<button data-page="' + (state.page + 1) + '"' + (state.page === pages ? ' disabled' : '') + '>›</button>';
    els.pager.innerHTML = html;
  }

  function apply() {
    var q = state.q.trim().toLowerCase();
    var terms = q ? q.split(/\s+/) : [];
    var out = state.all.filter(function (p) {
      if (state.cat !== 'all' && p.cat !== state.cat) return false;
      if (state.mat !== 'all' && materialKey(p) !== state.mat) return false;
      if (terms.length) {
        var blob = p._blob || (p._blob = searchBlob(p));
        for (var i = 0; i < terms.length; i++) if (blob.indexOf(terms[i]) === -1) return false;
      }
      return true;
    });
    var by = state.sort;
    out.sort(function (a, b) {
      if (by === 'price-asc') return (parseFloat(a.price) || 0) - (parseFloat(b.price) || 0);
      if (by === 'price-desc') return (parseFloat(b.price) || 0) - (parseFloat(a.price) || 0);
      if (by === 'name') return String(a.name_en || a.name_zh).localeCompare(String(b.name_en || b.name_zh));
      return String(a.code).localeCompare(String(b.code), undefined, { numeric: true });
    });
    state.view = out;
    state.page = 1;
    render();
  }

  function chipCounts() {
    var m = {};
    state.all.forEach(function (p) { m[p.cat] = (m[p.cat] || 0) + 1; });
    return m;
  }

  function buildChips() {
    if (!els.chips) return;
    var counts = chipCounts();
    var cats = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; });
    var labels = {};
    state.all.forEach(function (p) { labels[p.cat] = catLabel(p); });
    var html = '<button class="chip" data-cat="all" aria-pressed="true">' + T('catalog.allCats') +
      '<span class="n">' + state.all.length + '</span></button>';
    cats.forEach(function (c) {
      html += '<button class="chip" data-cat="' + c + '" aria-pressed="false">' + SKIT.esc(labels[c] || c) +
        '<span class="n">' + counts[c] + '</span></button>';
    });
    els.chips.innerHTML = html;
  }

  function buildMaterials() {
    if (!els.mat) return;
    var counts = {};
    state.all.forEach(function (p) {
      var k = materialKey(p);
      counts[k] = (counts[k] || 0) + 1;
    });
    var html = '<option value="all">' + T('catalog.allMaterials') + '</option>';
    Object.keys(counts).sort().forEach(function (k) {
      html += '<option value="' + k + '">' + T(MAT_LABELS[k] || 'material.other') + ' (' + counts[k] + ')</option>';
    });
    els.mat.innerHTML = html;
  }

  function buildCats() {
    if (!els.cat) return;
    var counts = chipCounts(), labels = {};
    state.all.forEach(function (p) { labels[p.cat] = catLabel(p); });
    var html = '<option value="all">' + T('catalog.allCats') + '</option>';
    Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; }).forEach(function (c) {
      html += '<option value="' + c + '">' + SKIT.esc(labels[c] || c) + ' (' + counts[c] + ')</option>';
    });
    els.cat.innerHTML = html;
  }

  // ------------------------------------------------------------------ events
  if (els.search) {
    var timer;
    els.search.addEventListener('input', function () {
      els.searchWrap.classList.toggle('has-value', !!els.search.value);
      clearTimeout(timer);
      timer = setTimeout(function () { state.q = els.search.value; apply(); }, 180);
    });
  }
  document.addEventListener('click', function (e) {
    var chip = e.target.closest('.chip[data-cat]');
    if (chip) {
      state.cat = chip.getAttribute('data-cat');
      if (els.cat) els.cat.value = state.cat;
      els.chips.querySelectorAll('.chip').forEach(function (c) {
        c.setAttribute('aria-pressed', c === chip ? 'true' : 'false');
      });
      apply();
      window.scrollTo({ top: root.offsetTop - 130, behavior: 'smooth' });
      return;
    }
    var pg = e.target.closest('[data-page]');
    if (pg && !pg.disabled) {
      var p = parseInt(pg.getAttribute('data-page'), 10);
      var pages = Math.ceil(state.view.length / PER_PAGE);
      if (p >= 1 && p <= pages) {
        state.page = p;
        render();
        var tb = document.querySelector('.toolbar');
        window.scrollTo({ top: (tb ? tb.offsetTop : 0) - 4, behavior: 'smooth' });
      }
      return;
    }
    if (e.target.closest('[data-reset]')) {
      state.q = ''; state.cat = 'all'; state.mat = 'all';
      if (els.search) { els.search.value = ''; els.searchWrap.classList.remove('has-value'); }
      if (els.cat) els.cat.value = 'all';
      if (els.mat) els.mat.value = 'all';
      if (els.chips) els.chips.querySelectorAll('.chip').forEach(function (c) {
        c.setAttribute('aria-pressed', c.getAttribute('data-cat') === 'all' ? 'true' : 'false');
      });
      apply();
      return;
    }
    var layout = e.target.closest('[data-layout]');
    if (layout) {
      state.layout = layout.getAttribute('data-layout');
      SKIT.store('skit.layout', state.layout);
      els.viewBtns.forEach(function (b) {
        b.setAttribute('aria-pressed', b === layout ? 'true' : 'false');
      });
      render();
      return;
    }
    var clear = e.target.closest('.search-clear');
    if (clear && els.search) {
      els.search.value = ''; state.q = '';
      els.searchWrap.classList.remove('has-value');
      apply(); els.search.focus();
    }
  });

  if (els.cat) els.cat.addEventListener('change', function () {
    state.cat = els.cat.value;
    if (els.chips) els.chips.querySelectorAll('.chip').forEach(function (c) {
      c.setAttribute('aria-pressed', c.getAttribute('data-cat') === state.cat ? 'true' : 'false');
    });
    apply();
  });
  if (els.mat) els.mat.addEventListener('change', function () { state.mat = els.mat.value; apply(); });

  document.addEventListener('skit:sort', function (e) { state.sort = e.detail.value; apply(); });
  document.addEventListener('skit:currency', function () { render(); });
  document.addEventListener('skit:lang', function () {
    buildChips(); buildCats(); buildMaterials();
    if (els.sort) els.sort.value = state.sort;
    render();
  });

  // ------------------------------------------------------------------ load
  fetch(u('data/catalog.json'), { cache: 'force-cache' })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      state.all = (data.products || []).filter(function (p) {
        return SETKEY === 'all' || p.set === SETKEY;
      });
      buildChips();
      buildCats();
      buildMaterials();
      if (els.sort) els.sort.value = state.sort;
      els.viewBtns.forEach(function (b) {
        b.setAttribute('aria-pressed', b.getAttribute('data-layout') === state.layout ? 'true' : 'false');
      });
      apply();
    })
    .catch(function (err) {
      if (window.console && console.error) console.error('[SKit] catalogue failed:', err);
      els.grid.innerHTML = '<div class="empty" style="grid-column:1/-1">' +
        '<h3>' + T('catalog.noResults') + '</h3><p>' + SKIT.esc(String(err)) + '</p></div>';
    });
})();
