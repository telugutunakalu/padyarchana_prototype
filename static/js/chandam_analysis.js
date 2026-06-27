/*!
 * chandam_analysis.js — thin adapter that wires the embeddable Chandam engine
 * (static/chandam/chandam-lib.js + chandam.te.app.min.js) into the padyarchana
 * poem page. It lazily warms up the 712 KB engine on first use and renders the
 * structured Chandam.analyze() result as app-styled HTML (chandam-* classes
 * defined in static/css/styles.css).
 *
 * Public API (window.ChandamAnalysis):
 *   ensureReady()        -> Promise, resolves once Chandam.analyze() is usable
 *   renderHtml(result)   -> HTML string for a Chandam.analyze() result
 *
 * Only the verse text is ever passed to the engine by the caller.
 */
(function (global) {
  'use strict';

  var ENGINE_PATH = '/static/chandam/chandam.te.app.min.js';
  var _ready = null;

  // Warm up the engine exactly once; reuse the promise on subsequent clicks.
  function ensureReady() {
    if (!global.Chandam) {
      return Promise.reject(new Error('Chandam library not loaded (chandam-lib.js missing).'));
    }
    if (!_ready) {
      _ready = global.Chandam.init({ enginePath: ENGINE_PATH });
    }
    return _ready;
  }

  function esc(s) {
    return String(s).replace(/[&<>]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
    });
  }

  // Analyze verse text. Single entry point with a load guard. We deliberately
  // pass the text through VERBATIM — exactly what the native chandam tool does.
  // The engine is whitespace-sensitive (a పాదాంత syllable's weight can flip on a
  // trailing space, which is actually what yields the correct meter for some
  // padyalu), so normalizing/trimming here would make our results diverge from
  // the official tool. Do NOT trim.
  function analyze(text, options) {
    if (!global.Chandam) throw new Error('Chandam library not loaded (chandam-lib.js missing).');
    return global.Chandam.analyze(text == null ? '' : String(text), options);
  }

  // Normalize a meter name for comparison. Telugu meter names have classical
  // ("ము") and modern ("ం") endings for the same meter (కందము ≡ కందం) plus stray
  // spaces (కమల విలసితము ≡ కమలవిలసిత). Strip those so the recorded vs detected
  // check doesn't flag spelling variants as a mismatch. Verified against all
  // meters in the DB: every name that collapses together is a true variant.
  function meterKey(name) {
    return String(name == null ? '' : name).replace(/\s+/g, '').replace(/(ము|ం)$/, '');
  }

  // The engine's yati marker may cover more than one akshara (e.g. line 1's
  // span wraps "జీ వ", later lines just "జీ"). Build a lookup of every akshara
  // inside the yati span so we highlight each one, matching the native tool.
  function yatiSetOf(yatiAkshara) {
    var set = {};
    String(yatiAkshara == null ? '' : yatiAkshara).split(/\s+/).forEach(function (tok) {
      if (tok) set[tok] = true;
    });
    return set;
  }

  // Render one laghu/guru mark as a chip ('G' -> guru U, 'L' -> laghu I).
  function markChip(m) {
    var guru = (m === 'G');
    return '<span class="chandam-mk ' + (guru ? 'chandam-mk--g' : 'chandam-mk--l') + '" title="' +
           (guru ? 'గురువు' : 'లఘువు') + '">' + (guru ? 'U' : 'I') + '</span>';
  }

  // The engine pads each line with blank ganas to a fixed column count; drop
  // those so only real ganas (the extra ones flagged as errors included) show.
  function realGanas(line) {
    return (line.ganas || []).filter(function (g) {
      return (g.name && g.name.length) || (g.aksharas && g.aksharas.length);
    });
  }

  // Parse the engine's plain-text errors into structured rows for a table.
  // Lines look like:
  //   "1 వ పాదము-తప్పు: గణాల సంఖ్య - కావలసినది: 4 - ఉన్నది: 5"
  //   "2 వ పాదము-4 వ స్థానము-తప్పు: గణ స్వభావం - కావలసినది: సూర్య - ఉన్నది: తెలియదు(రి సె)"
  // Anything that doesn't match falls back to a raw single-cell row.
  function parseErrors(text) {
    if (!text) return [];
    return String(text).split('\n').map(function (ln) {
      ln = ln.trim();
      if (!ln) return null;
      var paadam   = (ln.match(/(\d+)\s*వ\s*పాదము/) || [])[1] || '';
      var sthanam  = (ln.match(/(\d+)\s*వ\s*స్థానము/) || [])[1] || '';
      var tappu    = (ln.match(/తప్పు:\s*(.+?)\s*-\s*కావలసినది:/) || [])[1] || '';
      var expected = (ln.match(/కావలసినది:\s*(.+?)\s*-\s*ఉన్నది:/) || [])[1] || '';
      var actual   = (ln.match(/ఉన్నది:\s*(.+)$/) || [])[1] || '';
      if (!paadam && !tappu) return { raw: ln };
      return { paadam: paadam, sthanam: sthanam, tappu: tappu, expected: expected, actual: actual };
    }).filter(Boolean);
  }

  /**
   * Build app-styled HTML from a Chandam.analyze() result. Mirrors the native
   * Chandam layout — summary, గణ విభజన table (one row per పాదం with a status
   * stamp and stacked గణం / గురు-లఘు / అక్షరాలు cells), దోషాలు error table and
   * numbered సమీప ఫలితాలు — re-skinned to the app theme.
   * @param {Object} r result object (see chandam-lib.js)
   * @param {string} [recordedMeter] the poem's recorded meter name.
   * @returns {string} HTML
   */
  function renderHtml(r, recordedMeter) {
    if (!r) return '';

    var detected = r.meter && r.meter.name ? r.meter.name : '—';
    var pct = (r.score && r.score.percentage != null) ? Math.round(r.score.percentage) : 0;
    var scoreNote = (r.score && r.score.value != null && r.score.total != null)
      ? r.score.value + '/' + r.score.total : '';
    var ok = !!r.matched;

    var h = '<div class="chandam-result">';

    // Header strip.
    h += '<div class="chandam-result-head">' +
         '<span class="chandam-result-title telugu-text">ఛందస్సు విశ్లేషణ</span>' +
         '<span class="chandam-result-sub">Chandassu analysis</span>' +
         '</div>';

    h += '<div class="chandam-result-body">';

    // Summary banner: detected meter + match badge + score.
    h += '<div class="chandam-summary">' +
         '<div class="chandam-summary-main">' +
           '<span class="chandam-summary-label">గుర్తించిన ఛందస్సు</span>' +
           '<span class="chandam-summary-meter telugu-text">' + esc(detected) + '</span>' +
         '</div>' +
         '<div class="chandam-summary-side">' +
           '<span class="chandam-badge ' + (ok ? 'chandam-badge--ok' : 'chandam-badge--bad') + '">' +
             (ok ? '✓ సరిపోయింది' : '✗ సరిపోలేదు') + '</span>' +
           '<span class="chandam-score">' + pct + '%' + (scoreNote ? ' · ' + scoreNote : '') + '</span>' +
         '</div>' +
         '</div>';

    // Agreement with the poem's recorded meter.
    if (recordedMeter) {
      var agrees = meterKey(recordedMeter) === meterKey(detected);
      h += '<div class="chandam-recorded telugu-text">' +
           '<span class="chandam-recorded-label">నమోదైన ఛందస్సు:</span> ' + esc(recordedMeter) + ' ' +
           '<span class="chandam-tag ' + (agrees ? 'chandam-tag--ok' : 'chandam-tag--diff') + '">' +
           (agrees ? '✓ సరిపోలింది' : '⚠ తేడా ఉంది') + '</span></div>';
    }

    // గణ విభజన: one table row per పాదం — status stamp + stacked gana cells.
    var lines = r.ganavibhajana || [];
    if (lines.length) {
      h += '<div class="chandam-subhead telugu-text">గణ విభజన</div>';
      h += '<div class="chandam-table-wrap"><table class="chandam-gv"><tbody>';
      lines.forEach(function (line, i) {
        h += '<tr>';
        h += '<td class="chandam-stamp ' + (line.ok ? 'chandam-stamp--ok' : 'chandam-stamp--bad') + '">' +
             '<span class="chandam-stamp-num">పా' + (i + 1) + '</span>' +
             '<span class="chandam-stamp-mark">' + (line.ok ? '✓' : '✗') + '</span></td>';
        realGanas(line).forEach(function (g) {
          var showCode = g.code && g.name.indexOf(g.code) === -1;
          var ySet = g.yati ? yatiSetOf(g.yatiAkshara) : null;
          h += '<td class="chandam-cell ' + (g.ok ? 'chandam-gana--ok' : 'chandam-gana--err') + '">' +
               '<div class="chandam-cell-name telugu-text">' + esc(g.name || '—') + '</div>' +
               (showCode ? '<div class="chandam-cell-code telugu-text">' + esc(g.code) + '</div>' : '') +
               '<div class="chandam-cell-marks">' + g.marks.map(markChip).join('') + '</div>' +
               '<div class="chandam-cell-syl telugu-text">' + g.aksharas.map(function (a) {
                 return (ySet && ySet[a])
                   ? '<span class="chandam-yati" title="యతి">' + esc(a) + '</span>'
                   : esc(a);
               }).join(' ') + '</div>' +
               '</td>';
        });
        h += '</tr>';
      });
      h += '</tbody></table></div>';

      // Legend.
      h += '<div class="chandam-legend">' +
           '<span><span class="chandam-mk chandam-mk--g">U</span>గురువు</span>' +
           '<span><span class="chandam-mk chandam-mk--l">I</span>లఘువు</span>' +
           '<span><span class="chandam-yati">అ</span>యతి</span>' +
           '</div>';
    }

    // దోషాలు: structured error table.
    var errs = parseErrors(r.errors);
    if (errs.length) {
      h += '<div class="chandam-subhead chandam-subhead--err telugu-text">⚠ దోషాలు</div>';
      h += '<div class="chandam-table-wrap"><table class="chandam-errtable telugu-text"><thead><tr>' +
           '<th>పాదము</th><th>స్థానము</th><th>తప్పు</th><th>కావలసినది</th><th>ఉన్నది</th>' +
           '</tr></thead><tbody>';
      errs.forEach(function (e) {
        if (e.raw) {
          h += '<tr><td colspan="5" style="text-align:left;">' + esc(e.raw) + '</td></tr>';
          return;
        }
        h += '<tr>' +
             '<td>' + esc(e.paadam || '—') + '</td>' +
             '<td>' + esc(e.sthanam || '—') + '</td>' +
             '<td>' + esc(e.tappu || '—') + '</td>' +
             '<td>' + esc(e.expected || '—') + '</td>' +
             '<td>' + esc(e.actual || '—') + '</td>' +
             '</tr>';
      });
      h += '</tbody></table></div>';
    }

    // సమీప ఫలితాలు: numbered candidate meters (top 8).
    if (r.candidates && r.candidates.length) {
      var top = r.candidates.slice(0, 8);
      h += '<div class="chandam-subhead telugu-text">సమీప ఫలితాలు</div>';
      h += '<ol class="chandam-cands-list">';
      top.forEach(function (c) {
        h += '<li><span class="chandam-cand-name telugu-text">' + esc(c.name) + '</span>' +
             '<span class="chandam-cand-pct">' + Math.round(c.percentage) + '%</span></li>';
      });
      h += '</ol>';
      if (r.candidates.length > top.length) {
        h += '<div class="chandam-cands-more telugu-text">… మరో ' +
             (r.candidates.length - top.length) + ' ఫలితాలు</div>';
      }
    }

    h += '</div></div>'; // body + result
    return h;
  }

  global.ChandamAnalysis = {
    ensureReady: ensureReady,
    analyze: analyze,
    renderHtml: renderHtml
  };

})(typeof window !== 'undefined' ? window : this);
