import { useState } from 'react';
import {
  MapPin,
  Layers,
  Calendar,
  Clock,
  Timer,
  Users,
  ChevronDown,
} from 'lucide-react';
import { sendBookingMessage, type BookingFormData } from '../api/bookings';
import './BookingCard.css';

const LOCATIONS = ['Baseline Grounds', 'Net & Rally Club', 'Ace Courts'];
const COURT_TYPES = ['Clay', 'Hard', 'Grass'];
const DURATIONS = ['1', '1.5', '2', '3'];
const PLAYERS_OPTIONS = ['1', '2', '3', '4'];

export default function BookingCard() {
  const [form, setForm] = useState<BookingFormData>({
    location: '',
    courtType: '',
    date: '',
    time: '',
    duration: '',
    players: '',
  });
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  function handleChange(field: keyof BookingFormData, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setFeedback(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setFeedback(null);
    try {
      const res = await sendBookingMessage(form);
      setFeedback({ type: 'success', text: res.response });
    } catch (err) {
      setFeedback({ type: 'error', text: err instanceof Error ? err.message : 'Something went wrong.' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="booking-card">
      <div className="booking-card-header">
        <p className="booking-card-header-sub">Reserve your slot in seconds</p>
        <h2 className="booking-card-header-title">Book a Court</h2>
      </div>

      <form className="booking-card-body" onSubmit={handleSubmit}>
        {/* Location */}
        <div className="booking-field full">
          <label className="booking-field-label">Location</label>
          <div className="booking-field-input-wrap">
            <span className="booking-field-icon">
              <MapPin size={16} strokeWidth={1.5} />
            </span>
            <select
              className="booking-select"
              value={form.location}
              onChange={(e) => handleChange('location', e.target.value)}
              required
            >
              <option value="">Select location</option>
              {LOCATIONS.map((l) => <option key={l}>{l}</option>)}
            </select>
            <span className="booking-field-chevron">
              <ChevronDown size={16} strokeWidth={1.5} />
            </span>
          </div>
        </div>

        {/* Court Type */}
        <div className="booking-field full">
          <label className="booking-field-label">Court Type</label>
          <div className="booking-field-input-wrap">
            <span className="booking-field-icon">
              <Layers size={16} strokeWidth={1.5} />
            </span>
            <select
              className="booking-select"
              value={form.courtType}
              onChange={(e) => handleChange('courtType', e.target.value)}
              required
            >
              <option value="">Select type</option>
              {COURT_TYPES.map((t) => <option key={t}>{t}</option>)}
            </select>
            <span className="booking-field-chevron">
              <ChevronDown size={16} strokeWidth={1.5} />
            </span>
          </div>
        </div>

        {/* Date + Time */}
        <div className="booking-form-row">
          <div className="booking-field">
            <label className="booking-field-label">Date</label>
            <div className="booking-field-input-wrap">
              <span className="booking-field-icon">
                <Calendar size={16} strokeWidth={1.5} />
              </span>
              <input
                type="date"
                className="booking-input"
                value={form.date}
                onChange={(e) => handleChange('date', e.target.value)}
                required
              />
            </div>
          </div>
          <div className="booking-field">
            <label className="booking-field-label">Time</label>
            <div className="booking-field-input-wrap">
              <span className="booking-field-icon">
                <Clock size={16} strokeWidth={1.5} />
              </span>
              <input
                type="time"
                className="booking-input"
                value={form.time}
                onChange={(e) => handleChange('time', e.target.value)}
                required
              />
            </div>
          </div>
        </div>

        {/* Duration + Players */}
        <div className="booking-form-row">
          <div className="booking-field">
            <label className="booking-field-label">Duration (hrs)</label>
            <div className="booking-field-input-wrap">
              <span className="booking-field-icon">
                <Timer size={16} strokeWidth={1.5} />
              </span>
              <select
                className="booking-select"
                value={form.duration}
                onChange={(e) => handleChange('duration', e.target.value)}
                required
              >
                <option value="">Select</option>
                {DURATIONS.map((d) => <option key={d} value={d}>{d} hr{d !== '1' ? 's' : ''}</option>)}
              </select>
              <span className="booking-field-chevron">
                <ChevronDown size={16} strokeWidth={1.5} />
              </span>
            </div>
          </div>
          <div className="booking-field">
            <label className="booking-field-label">Players</label>
            <div className="booking-field-input-wrap">
              <span className="booking-field-icon">
                <Users size={16} strokeWidth={1.5} />
              </span>
              <select
                className="booking-select"
                value={form.players}
                onChange={(e) => handleChange('players', e.target.value)}
                required
              >
                <option value="">Select</option>
                {PLAYERS_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
              <span className="booking-field-chevron">
                <ChevronDown size={16} strokeWidth={1.5} />
              </span>
            </div>
          </div>
        </div>

        {feedback && (
          <div className={`booking-feedback ${feedback.type}`}>
            {feedback.text}
          </div>
        )}

        <button className="booking-cta" type="submit" disabled={loading}>
          {loading ? 'Checking availability…' : 'Book Court Now'}
        </button>
      </form>
    </div>
  );
}
