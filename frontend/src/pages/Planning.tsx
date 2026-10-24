import {
  AlertTriangle,
  Building2,
  CalendarClock,
  Calculator,
  CheckCircle2,
  Clock,
  Layers,
  Lightbulb,
  ListChecks,
  Palette,
  Ruler,
  Sparkles,
} from 'lucide-react';
import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { api, errorMessage } from '../api/client';
import type { ApiResponse, PlanningResult } from '../api/types';
import {
  Badge,
  Button,
  Card,
  CheckList,
  EmptyState,
  ErrorBanner,
  Field,
  FloorPlan,
  MetaBar,
  PageHeader,
  SectionTitle,
  Spinner,
  Stat,
} from '../components/UI';
import { formatCurrency, formatDate, formatNumber, percent, titleCase } from '../lib/format';

const PHASE_COLORS: Record<string, string> = {
  'Pre-construction': '#f4a62a',
  Substructure: '#f97316',
  Superstructure: '#2dd4bf',
  MEP: '#60a5fa',
  Finishing: '#a78bfa',
  Handover: '#34d399',
};

function defaultStartDate() {
  const date = new Date();
  date.setDate(date.getDate() + 30);
  return date.toISOString().slice(0, 10);
}

export function Planning() {
  const [projectType, setProjectType] = useState('residential');
  const [area, setArea] = useState('2500');
  const [floors, setFloors] = useState('2');
  const [location, setLocation] = useState('Pune');
  const [quality, setQuality] = useState('standard');
  const [startDate, setStartDate] = useState(defaultStartDate);
  const [currency, setCurrency] = useState<'INR' | 'USD'>('INR');
  const [notes, setNotes] = useState('');
  const [response, setResponse] = useState<ApiResponse<PlanningResult> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (response) resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [response]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const areaValue = Number(area);
    const floorValue = Number(floors);
    if (!Number.isFinite(areaValue) || areaValue < 200) {
      setError('Built-up area must be at least 200 sq ft.');
      return;
    }
    if (!Number.isInteger(floorValue) || floorValue < 1 || floorValue > 60) {
      setError('Floors must be a whole number between 1 and 60.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const result = await api.createPlan({
        project_type: projectType,
        built_up_area_sqft: areaValue,
        floors: floorValue,
        location,
        quality,
        start_date: startDate,
        currency,
        notes: notes || null,
      });
      setResponse(result);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const result = response?.result;

  const costRows = useMemo(() => {
    if (!result) return [];
    const total = result.cost.total;
    return [
      { label: 'Structural works', value: result.cost.structural, color: '#f97316' },
      { label: 'Finishing', value: result.cost.finishing, color: '#a78bfa' },
      { label: 'MEP services', value: result.cost.mep, color: '#60a5fa' },
      { label: 'Labour', value: result.cost.labor, color: '#2dd4bf' },
      { label: 'Permits & approvals', value: result.cost.permits, color: '#f4a62a' },
      { label: 'Contingency', value: result.cost.contingency, color: '#94a3b8' },
    ].map((row) => ({ ...row, share: percent(row.value, total) }));
  }, [result]);

  return (
    <div className="page">
      <PageHeader
        eyebrow="Planning intelligence"
        title="Project Planner"
        description="Turn a project brief into a costed plan with material quantities, a critical-path schedule, an architectural concept and a typical floor layout."
        actions={<Badge tone="accent">Structured data</Badge>}
      />

      <div className="workbench">
        <Card className="form-card">
          <SectionTitle title="Project brief" description="Costs are deterministic; AI writes the design narrative." />
          <form onSubmit={submit} className="stack">
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
              <Field label="Quality level">
                <select value={quality} onChange={(event) => setQuality(event.target.value)}>
                  <option value="economy">Economy</option>
                  <option value="standard">Standard</option>
                  <option value="premium">Premium</option>
                  <option value="luxury">Luxury</option>
                </select>
              </Field>
            </div>
            <div className="form-grid">
              <Field label="Built-up area (sq ft)">
                <input
                  type="number"
                  min={200}
                  step={50}
                  value={area}
                  onChange={(event) => setArea(event.target.value)}
                />
              </Field>
              <Field label="Floors">
                <input
                  type="number"
                  min={1}
                  max={60}
                  step={1}
                  value={floors}
                  onChange={(event) => setFloors(event.target.value)}
                />
              </Field>
            </div>
            <Field label="Location">
              <input
                value={location}
                onChange={(event) => setLocation(event.target.value)}
                maxLength={80}
                placeholder="City, e.g. Pune"
              />
            </Field>
            <div className="form-grid">
              <Field label="Planned start">
                <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
              </Field>
              <Field label="Currency">
                <select value={currency} onChange={(event) => setCurrency(event.target.value as 'INR' | 'USD')}>
                  <option value="INR">INR (₹)</option>
                  <option value="USD">USD ($)</option>
                </select>
              </Field>
            </div>
            <Field label="Notes" hint="Optional">
              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={3}
                maxLength={1200}
                placeholder="Site constraints, phasing, sustainability targets…"
              />
            </Field>

            {error && <ErrorBanner message={error} />}
            <Button type="submit" loading={loading} className="button-block">
              {loading ? 'Building the plan…' : 'Generate project plan'}
            </Button>
            <p className="form-footnote">
              Cost, quantity and schedule baselines are deterministic estimates, not quotations.
            </p>
          </form>
        </Card>

        <div className="result-column" ref={resultRef}>
          {loading && (
            <Card>
              <Spinner label="Planning the project" />
            </Card>
          )}

          {!loading && !result && (
            <Card>
              <EmptyState
                icon={<Calculator size={24} />}
                title="Your project plan will appear here"
                description="Enter a brief to generate a cost breakdown, material schedule, CPM timeline, concept palette and typical floor plan."
              />
            </Card>
          )}

          {!loading && result && response && (
            <div className="result-stack">
              <MetaBar meta={response.meta} />

              <div className="stats-grid">
                <Stat
                  label="Estimated project cost"
                  value={formatCurrency(result.cost.total, result.currency, true)}
                  hint={`${formatCurrency(result.cost.cost_per_sqft, result.currency)} / sq ft`}
                  icon={<Calculator size={16} />}
                  tone="accent"
                />
                <Stat
                  label="Duration"
                  value={`${result.schedule.total_duration_days} days`}
                  hint={`${formatDate(result.schedule.start_date)} → ${formatDate(result.schedule.end_date)}`}
                  icon={<CalendarClock size={16} />}
                  tone="info"
                />
                <Stat
                  label="Built-up area"
                  value={`${formatNumber(result.built_up_area_sqft)} sq ft`}
                  hint={`${result.floors} floor${result.floors > 1 ? 's' : ''} · ${titleCase(result.quality)}`}
                  icon={<Building2 size={16} />}
                />
                <Stat
                  label="Typical floor"
                  value={`${formatNumber(result.floor_plan.typical_floor_area_sqft)} sq ft`}
                  hint={`${result.floor_plan.rooms.length} conceptual zones`}
                  icon={<Layers size={16} />}
                  tone="success"
                />
              </div>

              <div className="two-col two-col-wide-left">
                <Card>
                  <SectionTitle
                    title="Cost breakdown"
                    description={`Indicative ${result.currency} estimate for ${titleCase(result.location)}.`}
                    right={<Badge tone="neutral">{formatCurrency(result.cost.total, result.currency, true)}</Badge>}
                  />
                  <div className="cost-list">
                    {costRows.map((row) => (
                      <div key={row.label} className="cost-row">
                        <div className="cost-label">
                          <span>
                            <i style={{ background: row.color }} /> {row.label}
                          </span>
                          <strong>{formatCurrency(row.value, result.currency)}</strong>
                        </div>
                        <div className="bar-track">
                          <div className="bar-fill" style={{ width: `${row.share}%`, background: row.color }} />
                        </div>
                        <span className="cost-share">{row.share}%</span>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card>
                  <SectionTitle title="Design concept" right={<Palette size={18} className="muted-icon" />} />
                  <h3 className="concept-style">{result.concept.style}</h3>
                  <p className="concept-description">{result.concept.description}</p>
                  <div className="palette">
                    {result.concept.color_palette.map((swatch) => (
                      <div key={swatch.hex} className="swatch">
                        <span style={{ background: swatch.hex }} />
                        <small>{swatch.name}</small>
                      </div>
                    ))}
                  </div>
                  <CheckList items={result.concept.key_features} tone="accent" />
                </Card>
              </div>

              <Card>
                <SectionTitle
                  title="Construction schedule"
                  description={`${result.schedule.tasks.length} activities · critical path highlighted in amber.`}
                  right={<Clock size={18} className="muted-icon" />}
                />
                <div className="gantt">
                  {result.schedule.tasks.map((task) => {
                    const left = ((task.start_day - 1) / result.schedule.total_duration_days) * 100;
                    const width = (task.duration_days / result.schedule.total_duration_days) * 100;
                    const critical = result.schedule.critical_path.includes(task.id);
                    return (
                      <div className="gantt-row" key={task.id}>
                        <div className="gantt-label" title={task.name}>
                          <span>{task.name}</span>
                          <small>{task.id} · {task.duration_days}d</small>
                        </div>
                        <div className="gantt-track">
                          <div
                            className={`gantt-bar ${critical ? 'gantt-critical' : ''}`}
                            style={{
                              left: `${left}%`,
                              width: `${Math.max(width, 1.5)}%`,
                              background: critical ? undefined : PHASE_COLORS[task.phase] || '#64748b',
                            }}
                            title={`${task.name}: ${task.start_date} → ${task.end_date} (${task.duration_days} days)`}
                          />
                        </div>
                        <div className="gantt-dates">
                          {formatDate(task.start_date)} → {formatDate(task.end_date)}
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="critical-path">
                  <span>Critical path</span>
                  {result.schedule.critical_path.map((taskId) => (
                    <Badge key={taskId} tone="accent">
                      {taskId}
                    </Badge>
                  ))}
                </div>
              </Card>

              <div className="two-col two-col-wide-left">
                <Card>
                  <SectionTitle
                    title="Typical floor plan"
                    description={`${result.floor_plan.total_width_ft} ft × ${result.floor_plan.total_length_ft} ft conceptual layout.`}
                    right={<Ruler size={18} className="muted-icon" />}
                  />
                  <FloorPlan
                    rooms={result.floor_plan.rooms}
                    width={result.floor_plan.total_width_ft}
                    length={result.floor_plan.total_length_ft}
                  />
                  <div className="plan-notes">
                    {result.floor_plan.notes.map((note) => (
                      <span key={note}>
                        <CheckCircle2 size={13} /> {note}
                      </span>
                    ))}
                  </div>
                </Card>

                <Card>
                  <SectionTitle title="Material estimate" right={<Layers size={18} className="muted-icon" />} />
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Material</th>
                          <th>Qty</th>
                          <th>Rate</th>
                          <th>Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.materials.map((material) => (
                          <tr key={material.name} title={material.notes}>
                            <td>{material.name}</td>
                            <td>
                              {formatNumber(material.quantity, 2)} {material.unit}
                            </td>
                            <td>{formatCurrency(material.unit_cost, result.currency)}</td>
                            <td>{formatCurrency(material.estimated_cost, result.currency)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="form-footnote">
                    Material quantities are indicative and include normal wastage allowances.
                  </p>
                </Card>
              </div>

              <Card>
                <SectionTitle title="Sustainability guidance" right={<Sparkles size={18} className="muted-icon" />} />
                <CheckList items={result.concept.sustainability_notes} tone="success" />
              </Card>

              <div className="three-col">
                <Card>
                  <SectionTitle title="Risks" right={<AlertTriangle size={17} className="muted-icon" />} />
                  <CheckList items={result.risks} tone="warn" />
                </Card>
                <Card>
                  <SectionTitle title="Recommendations" right={<Lightbulb size={17} className="muted-icon" />} />
                  <CheckList items={result.recommendations} tone="accent" />
                </Card>
                <Card>
                  <SectionTitle title="Assumptions" right={<ListChecks size={17} className="muted-icon" />} />
                  <CheckList items={result.assumptions} tone="info" />
                </Card>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
