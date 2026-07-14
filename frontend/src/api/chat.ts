const API_BASE = import.meta.env.VITE_API_BASE_URL as string;

export interface ChatMessage {
  role: 'user' | 'agent';
  content: string;
}

export interface HistoryMessage {
  role: string;
  content: string;
}

interface ChatApiResponse {
  response: string;
  session_id: string;
}

export async function sendChatMessage(
  message: string,
  sessionId: string,
  history: HistoryMessage[] = [],
): Promise<string> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId, history }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail ?? 'Chat request failed');
  }

  const data: ChatApiResponse = await res.json();
  return data.response;
}
