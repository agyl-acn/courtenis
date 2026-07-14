import { useEffect, useState } from 'react';
import { getBookings, type Booking } from '../../api/bookings';
import './BookingsTab.css';

export default function BookingsTab() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBookings()
      .then((data) =>
        setBookings([...data].sort((a, b) => b.created_at.localeCompare(a.created_at)))
      )
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load bookings'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="admin-state-msg">Loading…</div>;
  if (error) return <div className="admin-state-msg admin-state-error">{error}</div>;

  return (
    <div className="bookings-tab">
      <h1 className="admin-page-title">Bookings</h1>
      {bookings.length === 0 ? (
        <div className="admin-state-msg">No bookings yet.</div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>Booking ID</th>
              <th>Court</th>
              <th>Date</th>
              <th>Time</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((b) => (
              <tr key={b.booking_id}>
                <td className="booking-id-cell">{b.booking_id}</td>
                <td>{b.court}</td>
                <td>{b.date}</td>
                <td>{b.time}</td>
                <td>{new Date(b.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
