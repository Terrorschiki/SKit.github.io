/* ==========================================================================
   SKit — product detail page enhancement (title, add-to-quote, related)
   Reads data-product (sku) and data-cat from <body>.
   ========================================================================== */
(function () {
  'use strict';

  var body = document.body;
  var sku = body.getAttribute('data-product');
  if (!sku) return;

  function u(p) { return (typeof window.SKIT_BASE === 'string' ? window.SKIT_BASE : '') + p; }
  function T(k, v) { return SKIT.t(k, v); }

  var addBtn = document.getElementById('pdpAdd');
  var cache = null;

  function paint() {
    if (!cache || !cache.me) return;
    var me = cache.me;
    // spec table: rebuild so labels follow the active language
    var table = document.getElementById('specTable');
    if (table) {
      var zh = SKIT.lang === 'zh';
      var rows = [
        ['spec.itemNo', me.code],
        ['spec.material', zh ? me.material : (me.material_en || me.material)],
        ['spec.size', me.size],
        ['spec.packing', zh ? me.packing : (me.packing_en || me.packing)],
        ['spec.qty', me.qty],
        ['spec.gw', me.gw],
        ['spec.cbm', me.cbm],
        ['spec.colour', zh ? me.colour : (me.colour_en || me.colour)],
        ['spec.note', zh ? me.note : (me.note_en || me.note)]
      ];
      table.innerHTML = rows.filter(function (r) { return String(r[1] || '').trim(); })
        .map(function (r) {
          return '<tr><th>' + SKIT.esc(T(r[0])) + '</th><td>' + SKIT.esc(String(r[1])) + '</td></tr>';
        }).join('');
    }
    var name = SKIT.lang === 'zh' ? (me.name_zh || me.name_en) : (me.name_en || me.name_zh);
    document.querySelectorAll('[data-pdp-name]').forEach(function (el) { el.textContent = name; });
    var sub = document.getElementById('pdpSub');
    if (sub) sub.textContent = SKIT.lang === 'zh' ? (me.name_en || '') : (me.name_zh || '');
    var unit = document.getElementById('pdpUnit');
    if (unit) {
      unit.innerHTML = SKIT.esc(T('product.priceNote')) + ' · ' + SKIT.esc(T('spec.moq')) + ' ' +
        SKIT.esc(String(me.qty)) + ' ' + SKIT.esc(T('spec.pcs'));
    }
    renderRelated();
  }

  function renderRelated() {
    if (!cache || !cache.items) return;
    var box = document.getElementById('relatedGrid');
    if (!box) return;
    var me = cache.me, items = cache.items;
    var rel = items.filter(function (p) { return p.cat === me.cat && p.id !== me.id; }).slice(0, 6);
    if (rel.length < 6) {
      var extra = items.filter(function (p) {
        return p.set === me.set && p.id !== me.id && rel.indexOf(p) === -1;
      });
      rel = rel.concat(extra).slice(0, 6);
    }
    box.innerHTML = rel.map(function (p) {
      var name = SKIT.lang === 'zh' ? (p.name_zh || p.name_en) : (p.name_en || p.name_zh);
      return '<a class="rel-card" href="' + p.id + '.html">' +
        '<img src="' + u('assets/products/') + p.id + '-thumb.jpg" alt="' + SKIT.esc(name) +
        '" loading="lazy" width="520" height="390">' +
        '<div class="rb"><div class="rn">' + SKIT.esc(name) + '</div>' +
        '<div class="rp">' + SKIT.money(p.price) + ' <span style="font-size:11px;color:var(--muted);font-family:var(--font-sans);font-weight:600">/ ' +
        SKIT.esc(p.code) + '</span></div></div></a>';
    }).join('');
  }

  fetch(u('data/catalog.json'), { cache: 'force-cache' })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var items = data.products || [];
      var me = items.filter(function (p) { return p.id === sku; })[0];
      if (!me) return;
      cache = { items: items, me: me };

      if (addBtn) {
        var payload = JSON.stringify({
          id: me.id, code: me.code, name_zh: me.name_zh, name_en: me.name_en,
          price: me.price, qty: me.qty, size: me.size, set: me.set
        });
        addBtn.setAttribute('data-add', payload);
        addBtn.disabled = false;
      }
      paint();
      var name = SKIT.lang === 'zh' ? (me.name_zh || me.name_en) : (me.name_en || me.name_zh);
      document.title = name + ' · ' + (me.code || '') + ' | SKit Kitchenware';
    })
    .catch(function () { /* static content still stands */ });

  document.addEventListener('skit:lang', paint);

  document.addEventListener('skit:currency', function () {
    document.querySelectorAll('[data-price-usd]').forEach(function (el) {
      el.textContent = SKIT.money(el.getAttribute('data-price-usd'));
    });
    renderRelated();
  });
})();
