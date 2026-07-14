import { useEffect, useState } from 'react';
import { getBookings, type Booking } from '../../api/bookings';
import { getCourts, type Court } from '../../api/courts';
import StatsCard from './StatsCard';
import './DashboardTab.css';

export default function DashboardTab() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [courts, setCourts] = useState<Court[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getBookings(), getCourts()])
      .then(([b, c]) => {
        setBookings(b);
        setCourts(c);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load stats'))
      .finally(() => setLoading(false));
  }, []);

  const today = new Date().toISOString().slice(0, 10);
  const todaysCount = bookings.filter((b) => b.date === today).length;

  if (loading) return <div className="admin-state-msg">Loading…</div>;
  if (error) return <div className="admin-state-msg admin-state-error">{error}</div>;

  return (
    <div className="dashboard-tab">
      <h1 className="admin-page-title">Dashboard</h1>
      <div className="stats-grid">
        <StatsCard label="Total Bookings" value={bookings.length} />
        <StatsCard label="Active Courts" value={courts.length} />
        <StatsCard label="Today's Bookings" value={todaysCount} />
      </div>
    </div>
  );
}
