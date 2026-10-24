import {
  Bot,
  BookMarked,
  ListChecks,
  Send,
  ShieldAlert,
  Sparkles,
  Trash2,
  User,
} from 'lucide-react';
import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { api, errorMessage } from '../api/client';
import type { ApiMeta, AssistantResult } from '../api/types';
import { Badge, Button, Card, ErrorBanner, Field, PageHeader, SectionTitle } from '../components/UI';
import { titleCase } from '../lib/format';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  result?: AssistantResult;
  meta?: ApiMeta;
}

const QUICK_PROMPTS = [
  'How do I recover a two-week schedule delay?',
  'Prepare a toolbox talk for slab edge work.',
  'What should I check before a concrete pour?',
  'Create a daily site report checklist.',
];

let messageCounter = 0;
function nextId() {
  messageCounter += 1;
  return `m-${Date.now()}-${messageCounter}`;
}

export function Assistant() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: nextId(),
      role: 'assistant',
      content:
        'Site assistant online. Ask me about safety, sequencing, quality, cost, procurement or documentation. I will keep the answer field-ready and include actions your team can own.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [projectType, setProjectType] = useState('commercial');
  const [stage, setStage] = useState('structure');
  const [location, setLocation] = useState('Pune');
  const [notes, setNotes] = useState('Cast-in-situ RCC frame, 6 floors, active slab work.');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, loading]);

  async function send(text?: string) {
    const message = (text ?? input).trim();
    if (!message || loading) return;
    const history = messages
      .filter((item) => item.role === 'user' || item.result)
      .map((item) => ({ role: item.role, content: item.content }));
    const userMessage: Message = { id: nextId(), role: 'user', content: message };
    setMessages((current) => [...current, userMessage]);
    setInput('');
    setError('');
    setLoading(true);
    try {
      const response = await api.chat({
        message,
        project_context: {
          project_type: projectType,
          stage,
          location: location || null,
          notes: notes || null,
        },
        conversation: history.slice(-10),
      });
      setMessages((current) => [
        ...current,
        {
          id: nextId(),
          role: 'assistant',
          content: response.result.answer,
          result: response.result,
          meta: response.meta,
        },
      ]);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Daily site copilot"
        title="Site Assistant"
        description="A field-ready assistant that answers with context, owner-ready actions and safety calls."
        actions={
          <Button variant="secondary" onClick={() => setMessages((current) => current.slice(0, 1))}>
            <Trash2 size={15} /> Clear chat
          </Button>
        }
      />

      <div className="assistant-layout">
        <Card className="chat-card" padded={false}>
          <div className="chat-header">
            <div className="chat-identity">
              <span className="chat-avatar">
                <Bot size={19} />
              </span>
              <div>
                <strong>ConstructIQ Assistant</strong>
                <span>Safety · planning · quality · documentation</span>
              </div>
            </div>
            <Badge tone="success" dot>
              Ready
            </Badge>
          </div>

          <div className="chat-messages">
            {messages.map((message) => (
              <article key={message.id} className={`message message-${message.role}`}>
                <span className={`message-avatar ${message.role === 'user' ? 'message-avatar-user' : ''}`}>
                  {message.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </span>
                <div className={`message-body ${message.role === 'user' ? 'message-body-user' : ''}`}>
                  <p className="message-text">{message.content}</p>

                  {message.result && (
                    <>
                      {message.result.action_items.length > 0 && (
                        <div className="message-section">
                          <h4>
                            <ListChecks size={15} /> Action items
                          </h4>
                          <ul className="compact-list">
                            {message.result.action_items.map((item) => (
                              <li key={item}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {message.result.safety_alerts.length > 0 && (
                        <div className="message-alert">
                          <h4>
                            <ShieldAlert size={15} /> Safety alerts
                          </h4>
                          {message.result.safety_alerts.map((alert) => (
                            <p key={alert}>{alert}</p>
                          ))}
                        </div>
                      )}

                      {message.result.references.length > 0 && (
                        <div className="message-section">
                          <h4>
                            <BookMarked size={15} /> References
                          </h4>
                          <p className="message-refs">{message.result.references.join(' · ')}</p>
                        </div>
                      )}

                      {message.result.follow_up_questions.length > 0 && (
                        <div className="followup-row">
                          {message.result.follow_up_questions.map((question) => (
                            <button
                              key={question}
                              type="button"
                              className="followup-chip"
                              onClick={() => void send(question)}
                            >
                              {question}
                            </button>
                          ))}
                        </div>
                      )}

                      <div className="message-footer">
                        <span>{Math.round(message.result.confidence * 100)}% confidence</span>
                        {message.meta && (
                          <span>
                            {message.meta.provider === 'demo' || message.meta.provider === 'fallback'
                              ? 'Demo engine'
                              : titleCase(message.meta.provider)}{' '}
                            · {message.meta.latency_ms} ms
                          </span>
                        )}
                      </div>
                      <p className="message-disclaimer">{message.result.disclaimer}</p>
                    </>
                  )}
                </div>
              </article>
            ))}

            {loading && (
              <article className="message message-assistant">
                <span className="message-avatar">
                  <Bot size={16} />
                </span>
                <div className="message-body typing">
                  <span />
                  <span />
                  <span />
                </div>
              </article>
            )}
            <div ref={endRef} />
          </div>

          <div className="chat-composer">
            {messages.length === 1 && (
              <div className="quick-prompts">
                {QUICK_PROMPTS.map((prompt) => (
                  <button key={prompt} type="button" className="chip" onClick={() => void send(prompt)}>
                    <Sparkles size={12} /> {prompt}
                  </button>
                ))}
              </div>
            )}
            {error && <ErrorBanner message={error} />}
            <div className="composer-row">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
                rows={2}
                maxLength={4000}
                placeholder="Ask the site assistant… (Enter to send, Shift+Enter for a new line)"
              />
              <Button type="button" onClick={() => void send()} loading={loading} disabled={!input.trim()}>
                <Send size={16} /> Send
              </Button>
            </div>
          </div>
        </Card>

        <div className="assistant-side">
          <Card>
            <SectionTitle title="Project context" description="Sent with every message." />
            <div className="stack">
              <Field label="Project type">
                <select value={projectType} onChange={(event) => setProjectType(event.target.value)}>
                  <option value="residential">Residential</option>
                  <option value="commercial">Commercial</option>
                  <option value="industrial">Industrial</option>
                  <option value="infrastructure">Infrastructure</option>
                  <option value="renovation">Renovation</option>
                </select>
              </Field>
              <Field label="Current stage">
                <select value={stage} onChange={(event) => setStage(event.target.value)}>
                  <option value="planning">Planning</option>
                  <option value="procurement">Procurement</option>
                  <option value="foundation">Foundation</option>
                  <option value="structure">Structure</option>
                  <option value="finishing">Finishing</option>
                  <option value="handover">Handover</option>
                  <option value="maintenance">Maintenance</option>
                </select>
              </Field>
              <Field label="Site location">
                <input value={location} onChange={(event) => setLocation(event.target.value)} maxLength={80} />
              </Field>
              <Field label="Project notes">
                <textarea
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  rows={4}
                  maxLength={1200}
                />
              </Field>
            </div>
          </Card>
          <Card className="assistant-tip">
            <Sparkles size={18} />
            <div>
              <strong>Better answers</strong>
              <p>
                Mention the activity, stage and constraint. Ask for a checklist or a decision — not a
                general overview.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
