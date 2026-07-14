import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';
import { sendChatMessage, type ChatMessage } from '../api/chat';
import './Chatbot.css';

const SESSION_ID = 'chatbot';

const WELCOME: ChatMessage = {
  role: 'agent',
  content:
    "Hi! I'm your Courtenis assistant. Ask me anything — available courts, booking slots, or recommendations.",
};

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 160);
    }
  }, [isOpen]);

  async function handleSend() {
    const text = input.trim();
    if (!text || isLoading) return;

    // Snapshot history before the new user message — map 'agent' → 'assistant'
    // so the backend SDK receives the correct role names.
    const history = messages.map((m) => ({
      role: m.role === 'agent' ? 'assistant' : m.role,
      content: m.content,
    }));

    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setInput('');
    setIsLoading(true);

    try {
      const reply = await sendChatMessage(text, SESSION_ID, history);
      setMessages((prev) => [...prev, { role: 'agent', content: reply }]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Something went wrong.';
      setMessages((prev) => [...prev, { role: 'agent', content: `Sorry, I ran into an error: ${msg}` }]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chatbot">
      <div className={`chatbot-panel${isOpen ? ' open' : ''}`} role="dialog" aria-label="Courtenis chat assistant">
        <div className="chatbot-header">
          <span className="chatbot-header-title">Courtenis Assistant</span>
          <button
            className="chatbot-close"
            onClick={() => setIsOpen(false)}
            aria-label="Close chat"
          >
            <X size={16} strokeWidth={1.5} />
          </button>
        </div>

        <div className="chatbot-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`chatbot-bubble-row ${msg.role}`}>
              <div className={`chatbot-bubble ${msg.role}`}>{msg.content}</div>
            </div>
          ))}

          {isLoading && (
            <div className="chatbot-bubble-row agent">
              <div className="typing-indicator">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chatbot-input-row">
          <input
            ref={inputRef}
            className="chatbot-input"
            type="text"
            placeholder="Ask me anything…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
          <button
            className="chatbot-send"
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            aria-label="Send message"
          >
            <Send size={16} strokeWidth={1.5} />
          </button>
        </div>
      </div>

      <button
        className="chatbot-toggle"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? (
          <X size={22} strokeWidth={1.5} />
        ) : (
          <MessageCircle size={22} strokeWidth={1.5} />
        )}
      </button>
    </div>
  );
}
