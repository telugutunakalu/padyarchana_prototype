/*!
 * chandam-lib.js — an embeddable abstraction over the Chandam engine
 * (chandam.te.app.min.js). Give it text, get back structured ganavibhajana
 * and meter-match data that you can render however you like.
 *
 * Usage (browser):
 *   <script src="js/chandam-lib.js"></script>
 *   <script>
 *     Chandam.init({ enginePath: 'js/chandam.te.app.min.js' }).then(function () {
 *       var r = Chandam.analyze("...padyam...");
 *       console.log(r.meter.name, r.ganavibhajana);
 *     });
 *   </script>
 *
 * The library is non-invasive: it relies on a small export hook in the engine
 * (window.__ChandamModules) and never renders into your page on its own.
 */
(function (global) {
  'use strict';

  var LANGUAGES = { telugu: 0, kannada: 1, sanskrit: 2, hindi: 3, malayalam: 4 };

  var DEFAULTS = {
    language: 0,            // 0=telugu 1=kannada 2=sanskrit 3=hindi 4=malayalam (or name string)
    quickMatch: true,       // "కొత్త గణన పద్దతి" — fast new matching method
    matchYati: true,        // check yati maitri
    matchPrasa: true,       // check prasa rule
    allowSantiPrasa: false, // treat santa-prasa as valid
    experimentalSandhi: false, // vowel(achchu)-based yati detection
    includeRare: true,      // include rare meters in the search
    preLines: null          // pre-known number of lines, or null
  };

  // ---- engine access -------------------------------------------------------
  function modules() { return global.__ChandamModules; }
  function business() { var m = modules(); return m && m.Business; }

  // Build a duck-typed options object matching the interface the engine's
  // mostProbable()/match() read from (getters only).
  function buildOptions(o) {
    o = o || {};
    function pick(k) { return (o[k] !== undefined) ? o[k] : DEFAULTS[k]; }
    var lang = pick('language');
    if (typeof lang === 'string') lang = LANGUAGES[lang.toLowerCase()];
    if (lang == null) lang = 0;
    return {
      get_language: function () { return lang; },
      get_includeRare: function () { return !!pick('includeRare'); },
      get_quickMatch: function () { return !!pick('quickMatch'); },
      get_matchYati: function () { return !!pick('matchYati'); },
      get_matchPrasa: function () { return !!pick('matchPrasa'); },
      get_allowSantiPrasa: function () { return !!pick('allowSantiPrasa'); },
      get_experimenatalSandhi: function () { return !!pick('experimentalSandhi'); },
      get_preLines: function () { var p = pick('preLines'); return p == null ? null : p; },
      get_remarks: function () { return ''; },
      set_remarks: function () {}
    };
  }

  // ---- hidden DOM scaffold -------------------------------------------------
  // The engine wires event handlers to many elements by id during init. We
  // provide all of them (correct types) inside a hidden container so init runs
  // cleanly without the host page needing any markup.
  var SCAFFOLD_ID = '__chandam_scaffold';
  var SPEC = {
    textarea: ['txt'],
    select: ['ChandamNames', 'GanaType', 'Lines', 'list', 'MachineEnabled', 'PadyamType'],
    checkbox: ['quickMatch', 'btnYatiCheck', 'experimentalYati', 'allowSantiPrasa',
               'allowSantiPrasa2', 'hasPrasa', 'hasPrasaYati', 'hasAnthyaPrasa',
               'hasSameRules', 'isDaMdakamu', 'shareWithMe'],
    button: ['btnClear3', 'btnClear4', 'btnClear5', 'btnCreate', 'btnCustomRules',
             'btnDetermine', 'btnGenPadyam', 'btnSamples', 'btnScores', 'btnShowRules',
             'btnTry', 'btnWVruttam', 'HowMany', 'PCheck', 'ReportPending', 'Reset',
             'Share', 'WhichG', 'YCheck'],
    text: ['EmailId', 'Group1', 'Group2', 'Name', 'txtEmailInput'],
    number: ['txtNumber', 'txtVruttam'],
    anchor: ['btnClear', 'btnRandom', 'logo'],
    div: ['banner', 'bannerWrapper', 'buttons', 'ChandamContainer', 'Designer',
          'DesignerContainer', 'input', 'LabsPage', 'main', 'mainRow', 'notification',
          'result', 'Rows', 'sortTools', 'tc', 'toolbar'],
    span: ['blog', 'blog2', 'bulk', 'CheatSheet', 'debug', 'Expand', 'fbPost', 'feed',
           'feedback', 'lblAllowSantiPrasa', 'lblexperimentalYati', 'logoH1', 'new_a',
           'notification2', 'print', 'RandomItems', 'req', 'scores', 'SearchPadyamType',
           'SearchSreni', 'subscribe', 'timeTaken', 'totCalcs', 'totItems', 'twitterPost',
           'txtEmail', 'txtPermLink', 'unSubscribe', 'YatiRules'],
    sub: ['sort_a2z', 'sort_g'],
    h5: ['create', 'hideDesigner']
  };
  var CHECKED_BY_DEFAULT = { quickMatch: 1, btnYatiCheck: 1, hasPrasa: 1, hasSameRules: 1 };

  function injectScaffold() {
    if (document.getElementById(SCAFFOLD_ID)) return;
    var host = document.createElement('div');
    host.id = SCAFFOLD_ID;
    host.style.display = 'none';
    host.setAttribute('aria-hidden', 'true');

    function make(tag, id) {
      var el;
      if (tag === 'checkbox' || tag === 'button' || tag === 'text' || tag === 'number') {
        el = document.createElement('input');
        el.type = tag;
        if (tag === 'checkbox' && CHECKED_BY_DEFAULT[id]) el.checked = true;
      } else if (tag === 'anchor') {
        el = document.createElement('a');
      } else {
        el = document.createElement(tag);
      }
      el.id = id;
      return el;
    }

    Object.keys(SPEC).forEach(function (tag) {
      SPEC[tag].forEach(function (id) { host.appendChild(make(tag, id)); });
    });
    // Rules must live inside a <table> for valid DOM
    var tbl = document.createElement('table');
    var tb = document.createElement('tbody');
    tb.id = 'Rules';
    tbl.appendChild(tb);
    host.appendChild(tbl);

    (document.body || document.documentElement).appendChild(host);
  }

  // ---- engine loader -------------------------------------------------------
  var _readyPromise = null;

  function loadEngine(enginePath) {
    return new Promise(function (resolve, reject) {
      if (business()) { resolve(); return; }
      injectScaffold();
      if (enginePath) {
        var existing = document.querySelector('script[data-chandam-engine]');
        if (!existing) {
          var s = document.createElement('script');
          s.src = enginePath;
          s.setAttribute('data-chandam-engine', '1');
          s.onerror = function () { reject(new Error('Failed to load engine: ' + enginePath)); };
          document.head.appendChild(s);
        }
      }
      // poll until the engine exposes its modules and is warm (rules loaded)
      var waited = 0, step = 30, max = 15000;
      var t = setInterval(function () {
        if (business()) {
          if (isWarm()) { clearInterval(t); resolve(); return; }
        }
        waited += step;
        if (waited >= max) {
          clearInterval(t);
          if (business()) resolve();           // engine present but probe never matched
          else reject(new Error('Chandam engine not detected (window.__ChandamModules missing). ' +
                                'Did you include chandam.te.app.min.js, or pass enginePath to init()?'));
        }
      }, step);
    });
  }

  // Probe: rules are inline in the engine but indexed during init; confirm a
  // trivial determine works before declaring ready.
  function isWarm() {
    try {
      var r = business().determine('రామ', buildOptions({ matchYati: false, matchPrasa: false }));
      return r != null;
    } catch (e) { return false; }
  }

  /**
   * Initialise the library.
   * @param {Object} [cfg]
   * @param {string} [cfg.enginePath] path to chandam.te.app.min.js to auto-load.
   *        Omit if the engine <script> is already on the page.
   * @returns {Promise<void>} resolves when analyze() is usable.
   */
  function init(cfg) {
    cfg = cfg || {};
    if (!_readyPromise) _readyPromise = loadEngine(cfg.enginePath);
    return _readyPromise;
  }
  function ready() { return _readyPromise || init(); }
  function isReady() { return !!business() && isWarm(); }

  // ---- result parsing ------------------------------------------------------
  function textOf(node) { return (node.textContent || '').replace(/\s+/g, ' ').trim(); }

  // Convert the engine's laghu/guru row text ("U | | ") into marks.
  // In this engine: 'U' = guru (long), '|' = laghu (short).
  function marksFromPattern(p) {
    var out = [];
    for (var i = 0; i < p.length; i++) {
      var c = p[i];
      if (c === 'U' || c === 'u') out.push('G');
      else if (c === '|' || c === 'I') out.push('L');
    }
    return out;
  }

  function parseDoc(html) {
    if (typeof DOMParser !== 'undefined') {
      return new DOMParser().parseFromString('<table>' + html.replace(/^[\s\S]*?<table[^>]*>/i, '').replace(/<\/table>[\s\S]*$/i, '') + '</table>', 'text/html');
    }
    var d = document.implementation.createHTMLDocument('');
    d.body.innerHTML = html;
    return d;
  }

  // Parse padyam.build(matchResult) HTML table -> structured lines.
  function parseGanavibhajana(html) {
    if (!html) return [];
    var doc = parseDoc(html);
    var rows = Array.prototype.slice.call(doc.querySelectorAll('tr'));
    var lines = [];
    var cur = null;
    rows.forEach(function (row) {
      var cls = row.className || '';
      var cells = Array.prototype.slice.call(row.children);
      if (/\bga\b/.test(cls)) {
        // gana-names row: first cell is the stamper (ok/err mark)
        var stamper = cells[0];
        var lineOk = !!(stamper && stamper.querySelector('.ok'));
        var ganaCells = cells.slice(1);
        cur = {
          ok: lineOk,
          ganas: ganaCells.map(function (td) {
            return {
              name: textOf(td),                                  // e.g. సూర్య / ఇంద్ర / చంద్ర
              code: (td.getAttribute('title') || '').trim(),     // e.g. న / హ / నల
              ok: /\bgOk\b/.test(td.className),
              laghuGuru: '',
              marks: [],
              aksharas: [],
              yati: false,
              yatiAkshara: null
            };
          })
        };
        lines.push(cur);
      } else if (/\bup\b/.test(cls) && cur) {
        cells.forEach(function (td, i) {
          if (!cur.ganas[i]) return;
          var p = textOf(td);
          cur.ganas[i].laghuGuru = p;
          cur.ganas[i].marks = marksFromPattern(p);
        });
      } else if (/\bdw\b/.test(cls) && cur) {
        cells.forEach(function (td, i) {
          if (!cur.ganas[i]) return;
          var g = cur.ganas[i];
          var yat = td.querySelector('.y1');
          if (yat) { g.yati = true; g.yatiAkshara = textOf(yat); }
          g.aksharas = textOf(td).split(' ').filter(Boolean);
        });
      }
    });
    // line-level convenience fields
    lines.forEach(function (l) {
      var ak = [], mk = [];
      l.ganas.forEach(function (g) { ak = ak.concat(g.aksharas); mk = mk.concat(g.marks); });
      l.aksharas = ak;
      l.marks = mk;
      l.text = ak.join(' ');
      l.ganaNames = l.ganas.map(function (g) { return g.name; });
    });
    return lines;
  }

  function safe(fn, dflt) { try { return fn(); } catch (e) { return dflt; } }

  function parseCandidates(res) {
    var list = safe(function () { return res.get_candiates(); }, null);
    if (!list || !list.length) return [];
    var out = [];
    for (var i = 0; i < list.length; i++) {
      var c = list[i];
      out.push({
        name: safe(function () { return c.get_name(); }, null) ||
              safe(function () { return c.get_rule().get_name(); }, null) ||
              safe(function () { return c.get_identifier(); }, null),
        percentage: safe(function () { return c.get_percentage(); }, null),
        raw: c
      });
    }
    return out;
  }

  /**
   * Analyse a verse.
   * @param {string} text the padyam (lines separated by \n)
   * @param {Object} [options] see DEFAULTS
   * @returns {Object|null} structured result, or null for empty input
   */
  function analyze(text, options) {
    var B = business();
    if (!B) throw new Error('Chandam not initialised — call Chandam.init() and await ready().');
    if (text == null || !String(text).trim().length) return null;

    var opts = buildOptions(options);
    var res = B.determine(String(text), opts);
    if (res == null) return null;

    var rule = safe(function () { return res.get_rule(); }, null);
    var mr = safe(function () { return res.get_matchResult(); }, null);
    var padyam = safe(function () { return res.get_padyam(); }, null);

    var pct = mr ? safe(function () { return mr.get_percentage(); }, null) : null;
    var html = (padyam && mr) ? safe(function () { return padyam.build(mr); }, '') : '';
    var errorsText = mr ? safe(function () { return mr.showErrors(0); }, '') : '';
    // engine's plain-text error formatter can emit a stray "(undefined)" token
    errorsText = (errorsText || '').replace(/\(undefined\)/g, '').trim();

    return {
      input: String(text),
      matched: pct === 100,
      meter: {
        name: rule ? safe(function () { return rule.get_name(); }, null) : null,
        shortName: rule ? safe(function () { return rule.get_shortName(); }, null) : null,
        identifier: rule ? safe(function () { return rule.get_identifier(); }, null) : null
      },
      score: {
        percentage: pct,
        value: mr ? safe(function () { return mr.get_score(); }, null) : null,
        total: mr ? safe(function () { return mr.get_total(); }, null) : null
      },
      ganavibhajana: parseGanavibhajana(html),
      errors: errorsText || '',
      candidates: parseCandidates(res),
      html: html,        // raw engine HTML for the gana table, if you'd rather render it directly
      raw: res           // escape hatch: the live engine result object
    };
  }

  global.Chandam = {
    init: init,
    ready: ready,
    isReady: isReady,
    analyze: analyze,
    buildOptions: buildOptions,
    LANGUAGES: LANGUAGES,
    DEFAULTS: DEFAULTS,
    _modules: modules
  };

})(typeof window !== 'undefined' ? window : this);
