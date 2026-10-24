import {
  AlertOctagon,
  Camera,
  Eye,
  Ruler,
  ScanLine,
  Stethoscope,
  Wrench,
} from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, errorMessage } from '../api/client';
import type { ApiResponse, CrackResult } from '../api/types';
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
  SectionTitle,
  Spinner,
  Stat,
} from '../components/UI';
import { severityTone, titleCase } from '../lib/format';

export function Crack() {
  const [image, setImage] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [structureType, setStructureType] = useState('auto');
  const [response, setResponse] = useState<ApiResponse<CrackResult> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fileError, setFileError] = useState('');
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (response) resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [response]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!image) {
      setError('A close-up photograph of the crack is required for visual screening.');
      return;
    }
    setLoading(true);
    setError('');
    const form = new FormData();
    form.append('image', image);
    form.append('description', description);
    form.append('structure_type', structureType);
    try {
      setResponse(await api.analyzeCrack(form));
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
        eyebrow="Structural screening"
        title="Crack Analysis"
        description="Classify crack patterns, estimate severity and get a clear inspection and repair recommendation."
        actions={<Badge tone="info">Vision</Badge>}
      />

      <div className="workbench">
        <Card className="form-card">
          <SectionTitle title="Crack evidence" description="Use a well-lit, perpendicular close-up." />
          <form onSubmit={submit} className="stack">
            <ImageDropzone file={image} onFile={setImage} onError={setFileError} required />
            {fileError && <span className="field-error">{fileError}</span>}

            <Field label="Structure element">
              <select value={structureType} onChange={(event) => setStructureType(event.target.value)}>
                <option value="auto">Auto-detect</option>
                <option value="wall">Wall</option>
                <option value="beam">Beam</option>
                <option value="column">Column</option>
                <option value="slab">Slab</option>
                <option value="foundation">Foundation</option>
                <option value="ceiling">Ceiling</option>
                <option value="plaster">Plaster / finish</option>
              </select>
            </Field>

            <Field label="Inspector notes" hint="Optional">
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={3}
                maxLength={1200}
                placeholder="e.g. Diagonal crack near the beam-column joint, wider at the top, noticed after plastering…"
              />
            </Field>

            {error && <ErrorBanner message={error} />}
            <Button type="submit" loading={loading} className="button-block">
              {loading ? 'Screening image…' : 'Analyze crack'}
            </Button>
            <p className="form-footnote">
              Include a ruler or reference object in frame for better scale estimation.
            </p>
          </form>
        </Card>

        <div className="result-column" ref={resultRef}>
          {loading && (
            <Card>
              <Spinner label="Screening the surface" />
            </Card>
          )}

          {!loading && !result && (
            <Card>
              <EmptyState
                icon={<ScanLine size={24} />}
                title="Crack screening results will appear here"
                description="Upload a close-up photo. The AI classifies the pattern, estimates measurements and flags whether a structural engineer is required."
              />
            </Card>
          )}

          {!loading && result && response && (
            <div className="result-stack">
              <MetaBar meta={response.meta} />

              <Card className="result-hero-card">
                <div className="result-hero-main">
                  <RiskGauge score={result.severity_score} level={result.severity} label="Severity score" />
                  <div className="result-summary">
                    <div className="badge-row">
                      <Badge tone={severityTone(result.severity) as any} dot>
                        {titleCase(result.severity)} severity
                      </Badge>
                      <Badge tone="neutral">{titleCase(result.crack_type)} crack</Badge>
                      <Badge tone="info">{Math.round(result.confidence * 100)}% confidence</Badge>
                      <Badge tone={(result.detected ? 'warn' : 'success') as any}>
                        {result.detected ? 'Crack detected' : 'No clear crack'}
                      </Badge>
                    </div>
                    <h2>{result.affected_element}</h2>
                    <p>{result.summary}</p>
                    <div className="badge-row">
                      <Badge tone={severityTone(result.urgency) as any}>Urgency: {titleCase(result.urgency.replace('_', ' '))}</Badge>
                      <Badge tone="neutral">Image quality: {titleCase(result.image_quality)}</Badge>
                    </div>
                  </div>
                </div>

                <div className="stats-grid stats-grid-compact">
                  <Stat
                    label="Estimated width"
                    value={result.measurements.estimated_width_mm !== null ? `${result.measurements.estimated_width_mm} mm` : '—'}
                    icon={<Ruler size={15} />}
                    tone="warn"
                  />
                  <Stat
                    label="Estimated length"
                    value={result.measurements.estimated_length_cm !== null ? `${result.measurements.estimated_length_cm} cm` : '—'}
                    icon={<Ruler size={15} />}
                    tone="warn"
                  />
                  <Stat
                    label="Measurement confidence"
                    value={`${Math.round(result.measurements.confidence * 100)}%`}
                    icon={<Camera size={15} />}
                    tone="info"
                  />
                </div>
              </Card>

              {result.requires_professional_inspection && (
                <div className={`banner ${result.severity === 'critical' ? 'banner-danger' : 'banner-warning'}`}>
                  <AlertOctagon size={18} />
                  <div>
                    <strong>Professional inspection required</strong>
                    <p>
                      This pattern meets the escalation threshold. Restrict access and have a qualified
                      structural engineer verify the finding on site.
                    </p>
                  </div>
                </div>
              )}

              <div className="two-col">
                <Card>
                  <SectionTitle title="Probable causes" right={<Stethoscope size={18} className="muted-icon" />} />
                  <CheckList items={result.probable_causes} tone="warn" />
                </Card>
                <Card>
                  <SectionTitle title="Recommended actions" right={<Wrench size={18} className="muted-icon" />} />
                  <CheckList items={result.recommended_actions} tone="accent" />
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
