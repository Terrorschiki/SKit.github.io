/* ==========================================================================
   SKit — shared app: i18n, currency, quotation drawer, lightbox, header
   ========================================================================== */
(function () {
  'use strict';

  var LANGS = {
    en: { label: 'English',  flag: '🇬🇧', html: 'en' },
    es: { label: 'Español',  flag: '🇪🇸', html: 'es' },
    fr: { label: 'Français', flag: '🇫🇷', html: 'fr' },
    zh: { label: '中文',      flag: '🇨🇳', html: 'zh-CN' }
  };

  var CURRENCIES = {
    USD: { rate: 1, symbol: '$', code: 'USD', pos: 'pre' },
    EUR: { rate: 0.92, symbol: '€', code: 'EUR', pos: 'pre' },
    ZAR: { rate: 18.4, symbol: 'R', code: 'ZAR', pos: 'pre' }
  };

  var LS = { lang: 'skit.lang', cur: 'skit.currency', quote: 'skit.quote' };

  /* Sub-pages (e.g. /products/x.html) set window.SKIT_BASE = '../' before this
     script runs, so every asset reference resolves from the site root. */
  var BASE = typeof window.SKIT_BASE === 'string' ? window.SKIT_BASE : '';
  function url(p) { return BASE + p; }

  // ---------------------------------------------------------------- helpers
  function store(key, val) {
    try {
      if (val === undefined) return localStorage.getItem(key);
      if (val === null) localStorage.removeItem(key); else localStorage.setItem(key, val);
    } catch (e) { /* private mode */ }
    return null;
  }

  function detectLang() {
    var saved = store(LS.lang);
    if (saved && LANGS[saved]) return saved;
    var list = (navigator.languages || [navigator.language || 'en']).map(function (l) {
      return String(l).toLowerCase();
    });
    for (var i = 0; i < list.length; i++) {
      var l = list[i];
      if (l.indexOf('zh') === 0) return 'zh';
      if (l.indexOf('es') === 0) return 'es';
      if (l.indexOf('fr') === 0) return 'fr';
      if (l.indexOf('en') === 0) return 'en';
    }
    return 'en';
  }

  var state = {
    lang: detectLang(),
    currency: store(LS.cur) || 'USD',
    dict: null,
    baseDict: null,
    quote: []
  };

  function t(key, vars) {
    var d = state.dict || {};
    var s = (d[key] !== undefined ? d[key] : undefined);
    if (s === undefined && state.baseDict) s = state.baseDict[key];
    if (s === undefined) s = key;
    if (vars) {
      s = String(s).replace(/\{(\w+)\}/g, function (m, k) {
        return vars[k] !== undefined ? vars[k] : m;
      });
    }
    return s;
  }

  // ---------------------------------------------------------------- currency
  function money(usd) {
    var n = parseFloat(usd);
    if (!isFinite(n)) return '—';
    var c = CURRENCIES[state.currency] || CURRENCIES.USD;
    var v = n * c.rate;
    var s = v >= 1000 ? v.toFixed(0) : v.toFixed(2);
    s = s.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return c.pos === 'pre' ? c.symbol + ' ' + s : s + ' ' + c.symbol;
  }

  function moneyCode() { return (CURRENCIES[state.currency] || CURRENCIES.USD).code; }

  // ---------------------------------------------------------------- i18n apply
  function applyI18n(root) {
    var scope = root || document;
    scope.querySelectorAll('[data-i18n]').forEach(function (el) {
      var k = el.getAttribute('data-i18n');
      var v = t(k);
      if (v === k) return;
      if (el.hasAttribute('data-i18n-html')) el.innerHTML = v; else el.textContent = v;
    });
    scope.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      var v = t(el.getAttribute('data-i18n-placeholder'));
      if (v) el.setAttribute('placeholder', v);
    });
    scope.querySelectorAll('[data-i18n-title]').forEach(function (el) {
      var v = t(el.getAttribute('data-i18n-title'));
      if (v) el.setAttribute('title', v);
    });
    scope.querySelectorAll('[data-i18n-aria]').forEach(function (el) {
      var v = t(el.getAttribute('data-i18n-aria'));
      if (v) el.setAttribute('aria-label', v);
    });
    document.documentElement.lang = (LANGS[state.lang] || LANGS.en).html;
  }

  function loadDict(lang) {
    return fetch(url('assets/data/i18n/' + lang + '.json'), { cache: 'force-cache' })
      .then(function (r) { return r.ok ? r.json() : {}; })
      .catch(function () { return {}; });
  }

  function setLang(lang, silent) {
    if (!LANGS[lang]) lang = 'en';
    state.lang = lang;
    store(LS.lang, lang);
    var jobs = [loadDict(lang)];
    if (lang !== 'en') jobs.push(state.baseDict ? Promise.resolve(state.baseDict) : loadDict('en'));
    return Promise.all(jobs).then(function (res) {
      state.dict = res[0] || {};
      if (res[1]) state.baseDict = res[1];
      if (lang === 'en') state.baseDict = state.dict;
      applyI18n();
      updateLangUI();
      document.dispatchEvent(new CustomEvent('skit:lang', { detail: { lang: lang } }));
      if (!silent) closeMenus();
    });
  }

  function updateLangUI() {
    document.querySelectorAll('[data-lang-label]').forEach(function (el) {
      el.textContent = (LANGS[state.lang] || LANGS.en).label;
    });
    document.querySelectorAll('[data-lang-flag]').forEach(function (el) {
      el.textContent = (LANGS[state.lang] || LANGS.en).flag;
    });
    document.querySelectorAll('.lang-menu [data-lang]').forEach(function (b) {
      b.setAttribute('aria-current', b.getAttribute('data-lang') === state.lang ? 'true' : 'false');
    });
  }

  function setCurrency(cur) {
    if (!CURRENCIES[cur]) cur = 'USD';
    state.currency = cur;
    store(LS.cur, cur);
    document.querySelectorAll('select[data-currency-select]').forEach(function (s) { s.value = cur; });
    document.dispatchEvent(new CustomEvent('skit:currency'));
  }

  // ---------------------------------------------------------------- quote
  function loadQuote() {
    try { state.quote = JSON.parse(store(LS.quote) || '[]') || []; } catch (e) { state.quote = []; }
    if (!Array.isArray(state.quote)) state.quote = [];
  }
  function saveQuote() {
    store(LS.quote, JSON.stringify(state.quote));
    document.dispatchEvent(new CustomEvent('skit:quote'));
  }
  function quoteCount() {
    return state.quote.reduce(function (a, i) { return a + (i.qty || 0); }, 0);
  }
  function inQuote(id) {
    return state.quote.some(function (i) { return i.id === id; });
  }
  function addQuote(item, qty) {
    var found = state.quote.filter(function (i) { return i.id === item.id; })[0];
    var moq = parseInt(item.qty, 10) || 1;
    if (found) {
      found.qty += (qty || moq);
    } else {
      state.quote.push({
        id: item.id, code: item.code, zh: item.name_zh, en: item.name_en,
        price: parseFloat(item.price) || 0, qty: qty || moq, moq: moq,
        size: item.size || '', set: item.set
      });
    }
    saveQuote();
  }
  function removeQuote(id) {
    state.quote = state.quote.filter(function (i) { return i.id !== id; });
    saveQuote();
  }
  function setQty(id, qty) {
    var it = state.quote.filter(function (i) { return i.id === id; })[0];
    if (!it) return;
    it.qty = Math.max(1, parseInt(qty, 10) || 1);
    saveQuote();
  }
  function clearQuote() { state.quote = []; saveQuote(); }

  // ---------------------------------------------------------------- UI bits
  function toast(msg) {
    var el = document.querySelector('.toast');
    if (!el) {
      el = document.createElement('div');
      el.className = 'toast';
      document.body.appendChild(el);
    }
    el.textContent = msg;
    requestAnimationFrame(function () { el.classList.add('show'); });
    clearTimeout(el._t);
    el._t = setTimeout(function () { el.classList.remove('show'); }, 2400);
  }

  function closeMenus() {
    document.querySelectorAll('.lang.open').forEach(function (el) { el.classList.remove('open'); });
    var nav = document.querySelector('.nav.open');
    if (nav) nav.classList.remove('open');
  }

  function lightbox(src) {
    var lb = document.querySelector('.lightbox');
    if (!lb) {
      lb = document.createElement('div');
      lb.className = 'lightbox';
      lb.innerHTML = '<button class="lb-close" aria-label="Close">✕</button><img alt="">';
      document.body.appendChild(lb);
      lb.addEventListener('click', function (e) {
        if (e.target === lb || e.target.classList.contains('lb-close')) lb.classList.remove('open');
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') lb.classList.remove('open');
      });
    }
    lb.querySelector('img').src = src;
    lb.classList.add('open');
  }

  // ---------------------------------------------------------------- drawer
  function openDrawer() {
    var d = document.querySelector('.drawer'), s = document.querySelector('.drawer-scrim');
    if (!d) return;
    d.classList.add('open'); s.classList.add('open');
    document.body.style.overflow = 'hidden';
    renderDrawer();
  }
  function closeDrawer() {
    var d = document.querySelector('.drawer'), s = document.querySelector('.drawer-scrim');
    if (!d) return;
    d.classList.remove('open'); s.classList.remove('open');
    document.body.style.overflow = '';
  }

  function renderDrawer() {
    var body = document.querySelector('.drawer-body');
    var foot = document.querySelector('.drawer-foot');
    var fab = document.querySelector('.fab');
    if (fab) {
      var c = quoteCount();
      var bubble = fab.querySelector('.bubble');
      if (bubble) bubble.textContent = c;
      fab.setAttribute('data-empty', state.quote.length ? '0' : '1');
      var lbl = fab.querySelector('.fab-label');
      if (lbl) lbl.textContent = state.quote.length ? t('quote.view') : t('quote.title');
    }
    if (!body) return;

    if (!state.quote.length) {
      body.innerHTML = '<div class="drawer-empty">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 3h2l2.4 12.3a2 2 0 0 0 2 1.7h7.7a2 2 0 0 0 2-1.6L21 7H6"/><circle cx="10" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/></svg>' +
        '<h3 style="color:var(--ink);font-size:17px;margin-bottom:6px">' + t('quote.empty') + '</h3>' +
        '<p style="font-size:14px">' + t('quote.empty2') + '</p></div>';
      if (foot) foot.style.display = 'none';
      return;
    }
    if (foot) foot.style.display = '';

    var html = state.quote.map(function (i) {
      var line = i.price * i.qty;
      var name = state.lang === 'zh' ? (i.zh || i.en) : (i.en || i.zh);
      var sub = state.lang === 'zh' ? (i.en || '') : (i.zh || '');
      return '<div class="q-item" data-id="' + i.id + '">' +
        '<img src="' + url('assets/products/') + i.id + '-thumb.jpg" alt="" loading="lazy">' +
        '<div class="q-main">' +
          '<div class="q-name">' + esc(name) + '</div>' +
          '<div class="q-meta">' + esc(i.code || '') + (sub ? ' · ' + esc(sub) : '') + '</div>' +
          '<div class="q-row">' +
            '<div class="stepper">' +
              '<button type="button" data-step="-1" aria-label="-">−</button>' +
              '<input type="number" min="1" step="' + (i.moq || 1) + '" value="' + i.qty + '" data-qty>' +
              '<button type="button" data-step="1" aria-label="+">+</button>' +
            '</div>' +
            '<span class="q-sub">' + money(line) + '</span>' +
            '<button class="q-del" data-del title="' + t('quote.remove') + '">✕</button>' +
          '</div>' +
        '</div></div>';
    }).join('');
    body.innerHTML = html;

    var total = state.quote.reduce(function (a, i) { return a + i.price * i.qty; }, 0);
    var kinds = state.quote.length;
    var units = quoteCount();
    if (foot) {
      foot.innerHTML =
        '<div class="totals"><span>' + t('quote.lines', { n: kinds }) + '</span><span>' + units + ' ' + t('quote.pcs') + '</span></div>' +
        '<div class="totals"><span>' + t('quote.subtotal') + '</span><span>' + money(total) + '</span></div>' +
        '<div class="totals grand"><span>' + t('quote.total') + '</span><span>' + money(total) + '</span></div>' +
        '<p style="font-size:12px;color:var(--muted);margin:12px 0 14px">' + t('quote.disclaimer', { cur: moneyCode() }) + '</p>' +
        '<div style="display:grid;gap:9px">' +
          '<a class="btn btn-accent btn-block" href="' + url('contact.html') + '#quote">' + t('quote.send') + '</a>' +
          '<div style="display:flex;gap:9px">' +
            '<button class="btn btn-ghost btn-sm" style="flex:1" data-quote-copy>' + t('quote.copy') + '</button>' +
            '<button class="btn btn-ghost btn-sm" style="flex:1" data-quote-csv>' + t('quote.csv') + '</button>' +
          '</div>' +
          '<button class="btn btn-quiet btn-sm" data-quote-clear>' + t('quote.clear') + '</button>' +
        '</div>';
    }
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
    });
  }

  function quoteText() {
    var lines = [t('quote.docTitle'), ''];
    state.quote.forEach(function (i, n) {
      var name = state.lang === 'zh' ? (i.zh || i.en) : (i.en || i.zh);
      lines.push((n + 1) + '. ' + (i.code ? i.code + ' — ' : '') + name);
      lines.push('    ' + t('quote.qty') + ': ' + i.qty + '  ' + t('quote.unit') + ': ' + money(i.price) + '  ' + t('quote.amount') + ': ' + money(i.price * i.qty));
    });
    var total = state.quote.reduce(function (a, i) { return a + i.price * i.qty; }, 0);
    lines.push('');
    lines.push(t('quote.total') + ': ' + money(total) + ' ' + moneyCode());
    return lines.join('\n');
  }

  function download(name, text, mime) {
    var blob = new Blob([text], { type: mime || 'text/plain;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 500);
  }

  function quoteCsv() {
    var rows = [['Item No.', 'Chinese Name', 'English Name', 'Qty', 'Unit Price (' + moneyCode() + ')', 'Amount (' + moneyCode() + ')']];
    state.quote.forEach(function (i) {
      rows.push([i.code || '', i.zh || '', i.en || '', i.qty, (i.price * (CURRENCIES[state.currency] || CURRENCIES.USD).rate).toFixed(2),
        (i.price * i.qty * (CURRENCIES[state.currency] || CURRENCIES.USD).rate).toFixed(2)]);
    });
    var total = state.quote.reduce(function (a, i) { return a + i.price * i.qty; }, 0);
    rows.push([]);
    rows.push(['', '', '', '', 'TOTAL', (total * (CURRENCIES[state.currency] || CURRENCIES.USD).rate).toFixed(2)]);
    var csv = rows.map(function (r) {
      return r.map(function (c) { return '"' + String(c).replace(/"/g, '""') + '"'; }).join(',');
    }).join('\r\n');
    download('SKit-quotation-' + new Date().toISOString().slice(0, 10) + '.csv', '\uFEFF' + csv, 'text/csv;charset=utf-8');
  }

  // ---------------------------------------------------------------- global binds
  document.addEventListener('click', function (e) {
    var langBtn = e.target.closest('[data-lang-toggle]');
    if (langBtn) {
      e.preventDefault();
      var wrap = langBtn.closest('.lang');
      var wasOpen = wrap.classList.contains('open');
      closeMenus();
      if (!wasOpen) wrap.classList.add('open');
      return;
    }
    var langPick = e.target.closest('[data-lang]');
    if (langPick) { e.preventDefault(); setLang(langPick.getAttribute('data-lang')); return; }

    if (e.target.closest('[data-burger]')) {
      var nav = document.querySelector('.nav');
      if (nav) nav.classList.toggle('open');
      return;
    }
    if (!e.target.closest('.lang')) closeMenus();

    if (e.target.closest('[data-open-quote]')) { e.preventDefault(); openDrawer(); return; }
    if (e.target.closest('[data-close-quote]') || e.target.closest('.drawer-scrim')) { closeDrawer(); return; }

    var del = e.target.closest('[data-del]');
    if (del) {
      var item = del.closest('.q-item');
      removeQuote(item.getAttribute('data-id'));
      toast(t('quote.removed'));
      renderDrawer();
      return;
    }
    var step = e.target.closest('[data-step]');
    if (step) {
      var box = step.closest('.stepper');
      var id = step.closest('.q-item').getAttribute('data-id');
      var input = box.querySelector('[data-qty]');
      var it = state.quote.filter(function (x) { return x.id === id; })[0];
      var stepv = (it && it.moq) || 1;
      var next = Math.max(1, (parseInt(input.value, 10) || 1) + parseInt(step.getAttribute('data-step'), 10) * stepv);
      setQty(id, next);
      renderDrawer();
      return;
    }
    if (e.target.closest('[data-quote-clear]')) { clearQuote(); renderDrawer(); toast(t('quote.cleared')); return; }
    if (e.target.closest('[data-quote-copy]')) {
      var txt = quoteText();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).then(function () { toast(t('quote.copied')); },
          function () { download('SKit-quotation.txt', txt); });
      } else { download('SKit-quotation.txt', txt); }
      return;
    }
    if (e.target.closest('[data-quote-csv]')) { quoteCsv(); toast(t('quote.csvDone')); return; }

    var zoom = e.target.closest('[data-zoom]');
    if (zoom) { e.preventDefault(); lightbox(zoom.getAttribute('data-zoom')); return; }

    var add = e.target.closest('[data-add]');
    if (add) {
      e.preventDefault();
      try {
        var item = JSON.parse(add.getAttribute('data-add'));
        addQuote(item);
        add.setAttribute('data-added', '1');
        toast(t('product.added') + ' · ' + t('quote.view'));
        renderDrawer();
        setTimeout(function () { add.removeAttribute('data-added'); }, 1600);
      } catch (err) { /* ignore */ }
      return;
    }
  });

  document.addEventListener('change', function (e) {
    if (e.target.matches('[data-qty]')) {
      var id = e.target.closest('.q-item').getAttribute('data-id');
      setQty(id, e.target.value);
      renderDrawer();
    }
    if (e.target.matches('[data-currency-select]')) setCurrency(e.target.value);
    if (e.target.matches('[data-sort]')) {
      document.dispatchEvent(new CustomEvent('skit:sort', { detail: { value: e.target.value } }));
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeDrawer(); closeMenus(); }
  });

  document.addEventListener('skit:quote', renderDrawer);
  document.addEventListener('skit:currency', renderDrawer);
  document.addEventListener('skit:lang', renderDrawer);

  // ---------------------------------------------------------------- boot
  window.SKIT = {
    t: t, money: money, moneyCode: moneyCode, esc: esc,
    get lang() { return state.lang; },
    get currency() { return state.currency; },
    get quote() { return state.quote; },
    setLang: setLang, setCurrency: setCurrency, applyI18n: applyI18n,
    addQuote: addQuote, removeQuote: removeQuote, setQty: setQty,
    quoteCount: quoteCount, inQuote: inQuote, openDrawer: openDrawer,
    lightbox: lightbox, toast: toast, CURRENCIES: CURRENCIES,
    store: store, LS: LS, download: download
  };

  loadQuote();

  /* A few source lines have no photograph embedded in the price list.
     Swap any missing product image for the branded placeholder. */
  var PLACEHOLDER = BASE + 'assets/img/no-photo.svg';
  function guardImages(scope) {
    (scope || document).querySelectorAll('img').forEach(function (img) {
      if (img.dataset.guarded) return;
      img.dataset.guarded = '1';
      img.addEventListener('error', function () {
        if (img.src.indexOf('no-photo.svg') === -1) img.src = PLACEHOLDER;
      });
    });
  }
  document.addEventListener('error', function (e) {
    var t = e.target;
    if (t && t.tagName === 'IMG' && t.src.indexOf('no-photo.svg') === -1) t.src = PLACEHOLDER;
  }, true);
  document.addEventListener('skit:catalogRendered', function () { guardImages(); });

  function boot() {
    var jobs = [loadDict(state.lang)];
    if (state.lang !== 'en') jobs.push(loadDict('en'));
    Promise.all(jobs).then(function (res) {
      state.dict = res[0] || {};
      state.baseDict = res[1] || res[0] || {};
      applyI18n();
      updateLangUI();
      setCurrency(state.currency);
      renderDrawer();
      guardImages();
      document.dispatchEvent(new CustomEvent('skit:lang', { detail: { lang: state.lang } }));
      document.documentElement.classList.add('js-ready');
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
