import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  CalendarRange,
  CheckCircle2,
  CloudSun,
  Cpu,
  FileJson,
  HardHat,
  IndianRupee,
  Layers3,
  MessageSquareText,
  ScanLine,
  ShieldCheck,
  Sparkles,
  Terminal,
  WifiOff,
  Zap,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge, Card, EmptyState, PageHeader, Stat } from '../components/UI';
import { useHealth } from '../lib/health';

const FEATURES = [
  {
    to: '/safety',
    icon: HardHat,
    title: 'Site Safety Monitor',
    description: 'Image-led hazard detection, PPE compliance, risk scoring and corrective actions.',
    tag: 'Vision + text',
  },
  {
    to: '/crack',
    icon: ScanLine,
    title: 'Crack Analysis',
    description: 'Crack type, severity, probable cause, measurements and inspection urgency.',
    tag: 'Vision',
  },
  {
    to: '/planning',
    icon: CalendarRange,
    title: 'Project Planner',
    description: 'Material quantities, cost breakdown, CPM schedule, design concept and floor plan.',
    tag: 'Structured data',
  },
  {
    to: '/valuation',
    icon: IndianRupee,
    title: 'Real Estate Valuation',
    description: 'Indicative value range, price per sq ft, comparables and market outlook.',
    tag: 'Structured data',
  },
  {
    to: '/assistant',
    icon: MessageSquareText,
    title: 'Daily Site Assistant',
    description: 'Field-ready answers with action items, safety alerts and follow-up questions.',
    tag: 'Text + context',
  },
  {
    to: '/weather',
    icon: CloudSun,
    title: 'Weather Advisory',
    description: 'Live forecast translated into construction-specific work windows and warnings.',
    tag: 'Live weather',
  },
  {
    to: '/knowledge',
    icon: BookOpen,
    title: 'Knowledge Hub',
    description: 'Practical construction guidance with standards references and related topics.',
    tag: 'Knowledge',
  },
];

const PIPELINE = [
  { icon: Layers3, title: 'Multimodal input', text: 'Image, text and structured project data are validated on arrival.' },
  { icon: Cpu, title: 'AI analysis', text: 'Gemini or OpenAI handles live analysis; a deterministic engine guarantees offline demos.' },
  { icon: FileJson, title: 'Schema validation', text: 'Every response is validated with Pydantic strict models before it leaves the API.' },
  { icon: ShieldCheck, title: 'Stable UI', text: 'React renders only contract-approved fields — no brittle parsing or surprise shapes.' },
];

export function Dashboard() {
  const { health, error, loading, refresh } = useHealth();

  return (
    <div className="page page-dashboard">
      <PageHeader
        eyebrow="AI-powered construction intelligence"
        title="Build smarter. Safer. Faster."
        description="One workspace for safety review, structural screening, planning, valuation, site assistance, weather and construction knowledge — all backed by strict JSON contracts."
        actions={
          <>
            <Link to="/safety" className="button button-primary">
              Analyze a site <ArrowRight size={16} />
            </Link>
            <Link to="/planning" className="button button-secondary">
              Plan a project
            </Link>
          </>
        }
      />

      {error && (
        <div className="banner banner-danger" role="alert">
          <WifiOff size={18} />
          <div>
            <strong>Backend is not connected.</strong>
            <p>
              Start FastAPI with <code>uvicorn app.main:app --reload</code> from the{' '}
              <code>backend</code> folder, then refresh.
            </p>
          </div>
          <button type="button" className="banner-action" onClick={() => void refresh()}>
            Retry
          </button>
        </div>
      )}

      {health?.demo_mode && (
        <div className="banner banner-info">
          <Sparkles size={18} />
          <div>
            <strong>Demo intelligence engine is active.</strong>
            <p>
              Every module works without an API key. Add <code>GEMINI_API_KEY</code> or{' '}
              <code>OPENAI_API_KEY</code> to <code>backend/.env</code> to switch to live multimodal AI.
            </p>
          </div>
          <Badge tone="warn" dot>
            Demo mode
          </Badge>
        </div>
      )}

      <div className="hero-panel">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="pulse-dot" /> {loading && !health ? 'Connecting to API' : health ? 'Platform online' : 'Offline preview'}
          </div>
          <h2>From site photo to decision, in one flow.</h2>
          <p>
            Upload a site photograph and get a prioritized hazard register in seconds. Feed a project
            brief and receive quantities, a schedule and a concept plan. Ask a field question and get
            actions your team can execute today.
          </p>
          <div className="hero-tags">
            <Badge tone="accent">Multimodal</Badge>
            <Badge tone="info">Schema-first</Badge>
            <Badge tone="success">Demo-ready</Badge>
            <Badge tone="neutral">FastAPI + React</Badge>
          </div>
        </div>
        <div className="hero-signal" aria-hidden="true">
          <div className="signal-ring signal-ring-3" />
          <div className="signal-ring signal-ring-2" />
          <div className="signal-ring signal-ring-1" />
          <div className="signal-core">
            <Sparkles size={26} />
          </div>
          <div className="signal-label">AI core</div>
        </div>
      </div>

      <div className="stats-grid">
        <Stat label="AI modules" value="7" hint="Safety through knowledge" icon={<Layers3 size={16} />} tone="accent" />
        <Stat
          label="Input modes"
          value="3"
          hint="Image · text · structured data"
          icon={<Cpu size={16} />}
          tone="info"
        />
        <Stat
          label="AI engine"
          value={health?.demo_mode ? 'Demo' : health ? 'Live' : '—'}
          hint={health?.ai_model || (error ? 'Backend offline' : 'Checking…')}
          icon={<Zap size={16} />}
          tone={health?.demo_mode ? 'warn' : 'success'}
        />
        <Stat
          label="Response contract"
          value="Strict JSON"
          hint="Pydantic validated"
          icon={<FileJson size={16} />}
          tone="success"
        />
      </div>

      <section>
        <div className="section-title">
          <div>
            <h2>Intelligence modules</h2>
            <p>Each module is a complete workflow with a stable, documented JSON contract.</p>
          </div>
          <Badge tone="neutral">{FEATURES.length} modules</Badge>
        </div>
        <div className="feature-grid">
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <Link to={feature.to} key={feature.to} className="feature-card">
                <div className="feature-top">
                  <span className="feature-icon">
                    <Icon size={20} />
                  </span>
                  <ArrowUpRight size={16} className="feature-arrow" />
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
                <span className="feature-tag">{feature.tag}</span>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="two-col">
        <Card>
          <div className="section-title">
            <div>
              <h2>How a request moves</h2>
              <p>Reliability comes from validating at every hand-off.</p>
            </div>
            <CheckCircle2 size={18} className="muted-icon" />
          </div>
          <div className="pipeline">
            {PIPELINE.map((step, index) => {
              const Icon = step.icon;
              return (
                <div className="pipeline-step" key={step.title}>
                  <span className="pipeline-icon">
                    <Icon size={17} />
                  </span>
                  <div>
                    <strong>
                      <span className="pipeline-index">{String(index + 1).padStart(2, '0')}</span>{' '}
                      {step.title}
                    </strong>
                    <p>{step.text}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        <Card className="quickstart-card">
          <div className="section-title">
            <div>
              <h2>Run it locally</h2>
              <p>Two terminals. No API key required.</p>
            </div>
            <Terminal size={18} className="muted-icon" />
          </div>
          <div className="code-block">
            <pre>
              <code>{`# backend
cd backend
.venv\\Scripts\\activate
uvicorn app.main:app --reload

# frontend
cd frontend
npm run dev`}</code>
            </pre>
          </div>
          <div className="quickstart-meta">
            <span>
              <CheckCircle2 size={14} /> Backend docs at <code>/docs</code>
            </span>
            <span>
              <CheckCircle2 size={14} /> Frontend on port 5173
            </span>
            <span>
              <CheckCircle2 size={14} /> Demo mode works offline
            </span>
          </div>
        </Card>
      </section>

      {!health && !loading && !error && (
        <Card>
          <EmptyState
            title="Waiting for the backend"
            description="The dashboard will populate as soon as /api/health responds."
          />
        </Card>
      )}
    </div>
  );
}
