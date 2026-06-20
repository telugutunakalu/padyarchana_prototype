/**
 * JSON-based deep clone — works on Alpine's reactive Proxy objects, which
 * structuredClone rejects (the Proxy traps non-enumerable Symbol keys Alpine
 * uses for reactivity tracking and structuredClone refuses to serialize them).
 * JSON.stringify only sees own enumerable string-keyed props, which is exactly
 * the surface we want to snapshot. Falls back to the original on any failure.
 */
function _deepClone(value) {
  if (value === null || typeof value !== 'object') return value;
  try {
    return JSON.parse(JSON.stringify(value));
  } catch (_) {
    // Last-ditch: spread copy (shallow, but never throws on Alpine proxies).
    return Array.isArray(value) ? [...value] : { ...value };
  }
}

/**
 * Shared edit-mode behaviour for the admin user.
 *
 * Each detail page (poem / poet / meter) calls editablePage(...) once, gets
 * back an object that it merges into its existing x-data via Alpine's data().
 * Templates wrap each editable field with
 *   <template x-if="!editing">…display…</template>
 *   <template x-if="editing">…input…</template>
 * and call markDirty() on @input.
 *
 * Save sends a PUT with only the whitelisted fields. On 401 we redirect to
 * /login with ?next= so the user can come back to the same page.
 */
window.editablePage = function (initialModel, apiPath, editableFields) {
  return {
    // --- state ---
    model: _deepClone(initialModel || {}),
    original: _deepClone(initialModel || {}),
    editing: false,
    saving: false,
    dirty: false,
    saveError: '',
    saveOk: false,

    // --- helpers ---
    get canEdit() {
      return !!window.IS_ADMIN;
    },
    markDirty() {
      this.dirty = true;
      this.saveOk = false;
    },
    startEdit() {
      if (!this.canEdit) return;
      this.original = _deepClone(this.model);
      this.editing = true;
      this.dirty = false;
      this.saveError = '';
      this.saveOk = false;
    },
    cancelEdit() {
      // Overwrite fields in place so Alpine's reactive bindings stay valid.
      // Replacing `this.model` wholesale would break the host page (which
      // may keep references to the same model object elsewhere).
      const fresh = _deepClone(this.original);
      for (const k of Object.keys(this.model)) {
        if (!(k in fresh)) delete this.model[k];
      }
      Object.assign(this.model, fresh);
      this.editing = false;
      this.dirty = false;
      this.saveError = '';
    },
    addPadartham() {
      if (!Array.isArray(this.model.prathipadartham)) this.model.prathipadartham = [];
      this.model.prathipadartham.push({ word: '', meaning: '' });
      this.markDirty();
    },
    removePadartham(idx) {
      this.model.prathipadartham.splice(idx, 1);
      this.markDirty();
    },
    movePadartham(idx, delta) {
      const arr = this.model.prathipadartham;
      const j = idx + delta;
      if (j < 0 || j >= arr.length) return;
      const t = arr[idx]; arr[idx] = arr[j]; arr[j] = t;
      this.markDirty();
    },

    async save() {
      if (!this.canEdit || !this.dirty || this.saving) return;
      this.saving = true;
      this.saveError = '';
      this.saveOk = false;

      // Build the payload: only fields whose change is actually allowed.
      const payload = {};
      for (const f of editableFields) {
        if (this.model[f] !== undefined) payload[f] = this.model[f];
      }
      // Drop empty padartham rows so we never persist {word:"", meaning:""}.
      if (Array.isArray(payload.prathipadartham)) {
        payload.prathipadartham = payload.prathipadartham.filter(
          (e) => (e.word || '').trim() || (e.meaning || '').trim()
        );
      }

      try {
        const res = await fetch(apiPath, {
          method: 'PUT',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (res.status === 401) {
          const next = encodeURIComponent(window.location.pathname + window.location.search);
          window.location.href = `/login?next=${next}`;
          return;
        }
        if (res.status === 403) {
          this.saveError = 'You do not have permission to edit. Login as admin.';
          return;
        }
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          this.saveError = body.detail || `Save failed (HTTP ${res.status})`;
          return;
        }
        const saved = await res.json();
        // Merge server values into model so the displayed state matches what
        // was just persisted (handles server-side normalization, e.g. counts).
        Object.assign(this.model, saved);
        this.original = _deepClone(this.model);
        this.editing = false;
        this.dirty = false;
        this.saveOk = true;
        setTimeout(() => { this.saveOk = false; }, 3000);
      } catch (err) {
        this.saveError = String(err && err.message ? err.message : err);
      } finally {
        this.saving = false;
      }
    },
  };
};
