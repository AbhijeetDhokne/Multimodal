import {
  BookOpen,
  FileText,
  Search,
  Link,
  BookMarked,
  AlertTriangle,
} from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, errorMessage } from '../api/client';
import type { ApiResponse, KnowledgeResult } from '../api/types';
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorBanner,
  Field,
  MetaBar,
  PageHeader,
  SectionTitle,
  Spinner,
  Stat,
} from '../components/UI';

const TOPICS = [
  'concrete',
  'steel',
  'safety',
  'quality',
  'scheduling',
  'costing',
  'procurement',
  'excavation',
  'waterproofing',
  'green_building',
  'contracts',
  'general',
];

export function Knowledge() {
  const [question, setQuestion] = useState('What is the required concrete curing period?');
  const [topic, setTopic] = useState('general');
  const [level, setLevel] = useState('intermediate');
  const [response, setResponse] = useState<ApiResponse<KnowledgeResult> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (response) resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [response]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      setResponse(await api.askKnowledge({ question, topic, experience_level: level }));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const result = response?.result;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Knowledge hub"
        title="Construction Knowledge"
        description="Practical construction guidance with standards references and related topics."
        actions={<Badge tone="accent">Knowledge</Badge>}
      />

      <div className="workbench">
        <Card className="form-card">
          <SectionTitle title="Ask a question" description="Select a topic and experience level for targeted guidance." />
          <form onSubmit={submit} className="stack">
            <Field label="Question">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={4}
                maxLength={1500}
                placeholder="e.g. What is the required lap length for Fe500D rebar?"
              />
            </Field>
            <div className="form-grid">
              <Field label="Topic">
                <select value={topic} onChange={(e) => setTopic(e.target.value)}>
                  {TOPICS.map((t) => (
                    <option key={t} value={t}>
                      {titleCase(t)}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Experience level">
                <select value={level} onChange={(e) => setLevel(e.target.value)}>
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="expert">Expert</option>
                </select>
              </Field>
            </div>
            {error && <ErrorBanner message={error} />}
            <Button type="submit" loading={loading} className="button-block">
              {loading ? 'Looking up guidance…' : 'Get answer'}
            </Button>
            <p className="form-footnote">
              Answers are educational guidance — always follow the latest local codes and project specifications.
            </p>
          </form>
        </Card>

        <div className="result-column" ref={resultRef}>
          {loading && (
            <Card>
              <Spinner label="Searching knowledge base" />
            </Card>
          )}

          {!loading && !result && (
            <Card>
              <EmptyState
                icon={<BookOpen size={24} />}
                title="Your answer will appear here"
                description="Ask a construction question and get key points, practical tips, and standards references."
              />
            </Card>
          )}

          {!loading && result && response && (
            <div className="result-stack">
              <MetaBar meta={response.meta} />

              <Card className="valuation-hero">
                <div className="valuation-head">
                  <div>
                    <div className="badge-row">
                      <Badge tone="neutral" dot>{titleCase(result.topic)}</Badge>
                      <Badge tone="info">{Math.round(result.confidence * 100)}% confidence</Badge>
                    </div>
                    <span className="valuation-label">Answer</span>
                    <h2>{result.answer.length > 120 ? result.answer.slice(0, 120) + '…' : result.answer}</h2>
                  </div>
                </div>

                <div style={{ marginTop: 14 }}>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: 14, fontWeight: 700, color: 'var(--text)' }}>Full answer</h3>
                  <p style={{ margin: '0 0 14px 0', color: 'var(--text)', lineHeight: 1.6, fontSize: 13.5 }}>{result.answer}</p>

                  <SectionTitle title="Key points" />
                  <ul style={{ margin: '0 0 12px 0', paddingLeft: 18, color: 'var(--text)', fontSize: 13, lineHeight: 1.7 }}>
                    {result.key_points.map((p) => (
                      <li key={p} style={{ marginBottom: 5 }}>{p}</li>
                    ))}
                  </ul>

                  {result.practical_tips.length > 0 && (
                    <>
                      <SectionTitle title="Practical tips" right={<FileText size={17} className="muted-icon" />} />
                      <ul style={{ margin: '0 0 14px 0', paddingLeft: 18, color: 'var(--text)', fontSize: 13, lineHeight: 1.7 }}>
                        {result.practical_tips.map((t) => (
                          <li key={t} style={{ marginBottom: 5 }}>{t}</li>
                        ))}
                      </ul>
                    </>
                  )}

                  {result.references.length > 0 && (
                    <>
                      <SectionTitle title="References" right={<BookMarked size={17} className="muted-icon" />} />
                      <ul style={{ margin: '0 0 14px 0', paddingLeft: 18, color: 'var(--text)', fontSize: 13, lineHeight: 1.7 }}>
                        {result.references.map((r) => (
                          <li key={r.title} style={{ marginBottom: 4 }}>
                            <strong>{r.title}</strong> — {r.source}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}

                  {result.related_topics.length > 0 && (
                    <>
                      <SectionTitle title="Related topics" />
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
                        {result.related_topics.map((t) => (
                          <Badge key={t} tone="neutral">{titleCase(t)}</Badge>
                        ))}
                      </div>
                    </>
                  )}
                </div>

                <div style={{ marginTop: 14 }}>
                  <Card className="disclaimer-card">
                    <AlertTriangle size={16} />
                    <p>{result.disclaimer}</p>
                  </Card>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function titleCase(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join('');
}
