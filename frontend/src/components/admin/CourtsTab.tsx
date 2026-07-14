import { useCallback, useEffect, useState } from 'react';
import { getCourts, createCourt, updateCourt, deleteCourt } from '../../api/courts';
import type { Court, CourtFormData } from '../../api/courts';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import './CourtsTab.css';

const EMPTY_FORM: CourtFormData = { name: '', type: 'Hard', location: '', price: 0 };

export default function CourtsTab() {
  const [courts, setCourts] = useState<Court[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Court | null>(null);
  const [form, setForm] = useState<CourtFormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadCourts = useCallback(async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const data = await getCourts();
      setCourts(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load courts');
    } finally {
      if (showLoading) setLoading(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    loadCourts(false).finally(() => setLoading(false));
  }, [loadCourts]);

  function openAdd() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(court: Court) {
    setEditing(court);
    setForm({ name: court.name, type: court.type, location: court.location, price: court.price });
    setFormError(null);
    setFormOpen(true);
  }

  function closeForm() {
    setFormOpen(false);
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
  }

  async function handleSave() {
    if (!form.name.trim() || !form.location.trim()) {
      setFormError('Name and location are required.');
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      if (editing) {
        await updateCourt(editing.court_id, form);
      } else {
        await createCourt(form);
      }
      await loadCourts();
      closeForm();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(court: Court) {
    if (!window.confirm(`Delete "${court.name}"? This cannot be undone.`)) return;
    try {
      await deleteCourt(court.court_id);
      await loadCourts();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Delete failed');
    }
  }

  return (
    <div className="courts-tab">
      <div className="courts-tab-header">
        <h1 className="admin-page-title">Courts</h1>
        <button className="btn-add-court" onClick={openAdd}>
          <Plus size={16} strokeWidth={1.5} />
          Add Court
        </button>
      </div>

      {loading && <div className="admin-state-msg">Loading…</div>}
      {error && <div className="admin-state-msg admin-state-error">{error}</div>}

      {!loading && !error && courts.length === 0 && (
        <div className="admin-state-msg">No courts yet. Add one to get started.</div>
      )}

      {!loading && !error && courts.length > 0 && (
        <table className="admin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Location</th>
              <th>Price / hour</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {courts.map((c) => (
              <tr key={c.court_id}>
                <td>{c.name}</td>
                <td>
                  <span className={`type-badge type-${c.type.toLowerCase()}`}>{c.type}</span>
                </td>
                <td>{c.location}</td>
                <td>Rp{c.price.toLocaleString('id-ID')}/hr</td>
                <td>
                  <div className="actions-cell">
                    <button className="btn-action btn-edit" onClick={() => openEdit(c)}>
                      <Pencil size={14} strokeWidth={1.5} />
                      Edit
                    </button>
                    <button className="btn-action btn-delete" onClick={() => handleDelete(c)}>
                      <Trash2 size={14} strokeWidth={1.5} />
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {formOpen && (
        <div className="modal-overlay" onClick={closeForm}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">{editing ? 'Edit Court' : 'Add Court'}</h2>
            {formError && <p className="modal-form-error">{formError}</p>}

            <div className="modal-field">
              <label>Name</label>
              <input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Court A"
              />
            </div>

            <div className="modal-field">
              <label>Type</label>
              <select
                value={form.type}
                onChange={(e) => setForm((f) => ({ ...f, type: e.target.value as CourtFormData['type'] }))}
              >
                <option>Clay</option>
                <option>Hard</option>
                <option>Grass</option>
              </select>
            </div>

            <div className="modal-field">
              <label>Location</label>
              <input
                value={form.location}
                onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                placeholder="e.g. Downtown"
              />
            </div>

            <div className="modal-field">
              <label>Price per hour (IDR)</label>
              <input
                type="number"
                min="0"
                step="1000"
                value={form.price}
                onChange={(e) => setForm((f) => ({ ...f, price: parseInt(e.target.value, 10) || 0 }))}
              />
            </div>

            <div className="modal-actions">
              <button className="btn-modal-cancel" onClick={closeForm}>Cancel</button>
              <button className="btn-modal-save" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : editing ? 'Save Changes' : 'Add Court'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
