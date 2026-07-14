const API_BASE = import.meta.env.VITE_API_BASE_URL as string;

export interface Court {
  court_id: string;
  name: string;
  type: 'Clay' | 'Hard' | 'Grass';
  location: string;
  price: number;
}

export interface CourtFormData {
  name: string;
  type: 'Clay' | 'Hard' | 'Grass';
  location: string;
  price: number;
}

export async function getCourts(): Promise<Court[]> {
  const res = await fetch(`${API_BASE}/courts`);
  if (res.status === 404) return [];
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error((err as { detail?: string }).detail ?? 'Failed to load courts');
  }
  const data: unknown = await res.json();
  if (Array.isArray(data)) return data as Court[];
  return ((data as { courts?: Court[] }).courts) ?? [];
}

export async function createCourt(data: CourtFormData): Promise<Court> {
  const res = await fetch(`${API_BASE}/courts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error((err as { detail?: string }).detail ?? 'Failed to create court');
  }
  return res.json() as Promise<Court>;
}

export async function updateCourt(id: string, data: CourtFormData): Promise<Court> {
  const res = await fetch(`${API_BASE}/courts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error((err as { detail?: string }).detail ?? 'Failed to update court');
  }
  return res.json() as Promise<Court>;
}

export async function deleteCourt(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/courts/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error((err as { detail?: string }).detail ?? 'Failed to delete court');
  }
}
