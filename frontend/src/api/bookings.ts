const API_BASE = import.meta.env.VITE_API_BASE_URL as string;

export interface BookingFormData {
  location: string;
  courtType: string;
  date: string;
  time: string;
  duration: string;
  players: string;
}

export interface BookingAgentResponse {
  response: string;
}

export interface Booking {
  booking_id: string;
  slot_id: string;
  court: string;
  date: string;
  time: string;
  created_at: string;
}

export async function sendBookingMessage(form: BookingFormData): Promise<BookingAgentResponse> {
  const message =
    `I want to book a ${form.courtType} court at ${form.location} ` +
    `on ${form.date} at ${form.time} for ${form.duration} hour(s) with ${form.players} player(s).`;

  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error((err as { detail?: string }).detail ?? 'Booking request failed');
  }

  return res.json() as Promise<BookingAgentResponse>;
}

export async function getBookings(): Promise<Booking[]> {
  const res = await fetch(`${API_BASE}/bookings`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error((err as { detail?: string }).detail ?? 'Failed to load bookings');
  }
  const data = await res.json() as { bookings: Booking[] };
  return data.bookings ?? [];
}
