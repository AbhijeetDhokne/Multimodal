import {
  AlertTriangle,
  ClipboardCheck,
  Eye,
  HardHat,
  MapPin,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  ThumbsUp,
} from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, errorMessage } from '../api/client';
import type { ApiResponse, SafetyResult } from '../api/types';
import {
  Badge,
  Button,
  Card,
  CheckList,
  EmptyState,
  ErrorBanner,
  Field,
  ImageDropzone,
  MetaBar,
  PageHeader,
  RiskGauge,
  ScoreRing,
  SectionTitle,
  Spinner,
} from '../components/UI';
import { severityTone, titleCase } from '../lib/format';

const SAMPLE_NOTE =
  'Crew is working near the Level 2 slab edge. One worker is not wearing a helmet, temporary electrical cables are lying across a wet access route, and loose debris is blocking the stair landing.';

export function Safety() {
  const [image, setImage] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [projectType, setProjectType] = useState('residential');
  const [location, setLocation] = useState('North tower, Level 2');
  const [activity, setActivity] = useState('Slab and reinforcement work');
  const [response, setResponse] = useState<ApiResponse<SafetyResult> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fileError, setFileError] = useState('');
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (response) resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [response]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!image && !description.trim()) {
      setError('Upload a site image or add a short description so the AI has evidence to analyze.');
      return;
    }
    setLoading(true);
    setError('');
    const form = new FormData();
    if (image) form.append('image', image);
    form.append('description', description);
    form.append('project_type', projectType);
    form.append('location', location || 'Project site');
    form.append('work_activity', activity || 'General construction');
    try {
      setResponse(await api.analyzeSafety(form));
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
        eyebrow="Safety intelligence"
        title="Site Safety Monitor"
        description="Detect hazards, verify PPE compliance and convert observations into prioritized corrective actions."
        actions={<Badge tone="accent">Vision + context</Badge>}
      />

      <div className="workbench">
        <Card className="form-card">
          <SectionTitle title="Inspection input" description="A photo is optional, but improves visual confidence." />
          <form onSubmit={submit} className="stack">
            <ImageDropzone
              file={image}
              onFile={setImage}
              onError={setFileError}
              required={false}
            />
            {fileError && <span className="field-error">{fileError}</span>}

            <Field label="Observation notes" hint="Optional if a photo is provided">
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={4}
                maxLength={1500}
                placeholder="Describe the work front, visible hazards, PPE, access, housekeeping…"
              />
            </Field>
            <button
              type="button"
              className="text-button"
              onClick={() => setDescription(SAMPLE_NOTE)}
            >
              <Sparkles size={14} /> Use a sample observation
            </button>

            <div className="form-grid">
              <Field label="Project type">
                <select value={projectType} onChange={(event) => setProjectType(event.target.value)}>
                  <option value="residential">Residential</option>
                  <option value="commercial">Commercial</option>
                  <option value="industrial">Industrial</option>
                  <option value="infrastructure">Infrastructure</option>
                  <option value="renovation">Renovation</option>
                </select>
              </Field>
              <Field label="Work activity">
                <input
                  value={activity}
                  onChange={(event) => setActivity(event.target.value)}
                  maxLength={100}
                  placeholder="e.g. Slab work"
                />
              </Field>
            </div>
            <Field label="Location on site">
              <input
                value={location}
                onChange={(event) => setLocation(event.target.value)}
                maxLength={100}
                placeholder="e.g. North tower, Level 2"
              />
            </Field>

            {error && <ErrorBanner message={error} />}
            <Button type="submit" loading={loading} className="button-block">
              {loading ? 'Analyzing site…' : 'Run safety analysis'}
            </Button>
            <p className="form-footnote">
              Images are processed in memory for analysis and are not stored by this application.
            </p>
          </form>
        </Card>

        <div className="result-column" ref={resultRef}>
          {loading && (
            <Card>
              <Spinner label="Inspecting the work front" />
            </Card>
          )}

          {!loading && !result && (
            <Card>
              <EmptyState
                icon={<HardHat size={24} />}
                title="Your safety briefing will appear here"
                description="Upload a site photo or describe the work front. The AI returns hazards, PPE findings, a risk score and immediate actions."
              />
            </Card>
          )}

          {!loading && result && response && (
            <div className="result-stack">
              <MetaBar meta={response.meta} />

              <Card className="result-hero-card">
                <div className="result-hero-main">
                  <RiskGauge score={result.risk_score} level={result.risk_level} />
                  <div className="result-summary">
                    <div className="badge-row">
                      <Badge tone={severityTone(result.risk_level) as any} dot>
                        {titleCase(result.risk_level)} risk
                      </Badge>
                      <Badge tone="neutral">{titleCase(result.image_quality.replace('_', ' '))} image</Badge>
                      <Badge tone="info">{Math.round(result.confidence * 100)}% confidence</Badge>
                    </div>
                    <h2>Site safety assessment</h2>
                    <p>{result.summary}</p>
                  </div>
                </div>
                <div className="ppe-strip">
                  <ScoreRing
                    score={result.ppe.score}
                    label="PPE"
                    tone={result.ppe.score >= 80 ? '#34d399' : result.ppe.score >= 55 ? '#fbbf24' : '#f87171'}
                  />
                  <div className="ppe-copy">
                    <div className="ppe-heading">
                      <ShieldCheck size={17} />
                      <strong>PPE compliance: {titleCase(result.ppe.overall.replace('_', ' '))}</strong>
                    </div>
                    <div className="tag-row">
                      {result.ppe.observed.map((item) => (
                        <Badge key={item} tone="success">
                          {item}
                        </Badge>
                      ))}
                      {result.ppe.missing.map((item) => (
                        <Badge key={item} tone="danger">
                          Missing: {item}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>

              <Card>
                <SectionTitle
                  title={`Hazard register · ${result.hazards.length}`}
                  description="Prioritize controls before the next work shift."
                  right={<AlertTriangle size={18} className="muted-icon" />}
                />
                <div className="hazard-list">
                  {result.hazards.map((hazard) => (
                    <article key={hazard.id} className={`hazard-card hazard-${severityTone(hazard.severity)}`}>
                      <div className="hazard-head">
                        <div className="hazard-title">
                          <span className={`severity-dot tone-${severityTone(hazard.severity)}`} />
                          <h3>{hazard.title}</h3>
                        </div>
                        <div className="badge-row">
                          <Badge tone={severityTone(hazard.severity) as any}>{titleCase(hazard.severity)}</Badge>
                          <Badge tone="neutral">{titleCase(hazard.likelihood.replace('_', ' '))} likelihood</Badge>
                        </div>
                      </div>
                      <div className="hazard-meta">
                        <span>
                          <MapPin size={13} /> {hazard.location}
                        </span>
                        <span>{titleCase(hazard.category)}</span>
                      </div>
                      <p>{hazard.description}</p>
                      <div className="hazard-action">
                        <ClipboardCheck size={16} />
                        <div>
                          <strong>Corrective action</strong>
                          <p>{hazard.corrective_action}</p>
                        </div>
                      </div>
                      {hazard.ppe_required.length > 0 && (
                        <div className="tag-row">
                          {hazard.ppe_required.map((item) => (
                            <span key={item} className="tag">
                              {item}
                            </span>
                          ))}
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              </Card>

              <div className="two-col">
                <Card>
                  <SectionTitle title="Immediate actions" right={<ShieldAlert size={18} className="muted-icon" />} />
                  <CheckList items={result.immediate_actions} tone="danger" />
                </Card>
                <Card>
                  <SectionTitle title="Positive observations" right={<ThumbsUp size={18} className="muted-icon" />} />
                  <CheckList items={result.positive_observations} tone="success" />
                </Card>
              </div>

              <Card className="disclaimer-card">
                <Eye size={16} />
                <p>{result.disclaimer}</p>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
