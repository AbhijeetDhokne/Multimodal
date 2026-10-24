import {
  AlertCircle,
  Check,
  Copy,
  Image as ImageIcon,
  Info,
  Loader2,
  UploadCloud,
  X,
} from 'lucide-react';
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
  type ReactNode,
} from 'react';
import type { ApiMeta, RoomLayout } from '../api/types';
import { titleCase } from '../lib/format';

export function BrandMark({ size = 34 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" className="brand-mark">
      <rect width="64" height="64" rx="14" fill="#0b1017" />
      <path
        d="M14 50V25l18-10 18 10v25"
        fill="none"
        stroke="#f4a62a"
        strokeWidth="4"
        strokeLinejoin="round"
      />
      <path
        d="M24 50V34h16v16"
        fill="none"
        stroke="#2dd4bf"
        strokeWidth="4"
        strokeLinejoin="round"
      />
      <path d="M14 50h36" stroke="#f4a62a" strokeWidth="4" strokeLinecap="round" />
    </svg>
  );
}

type Tone = 'neutral' | 'accent' | 'success' | 'warn' | 'danger' | 'info';

export function Badge({
  children,
  tone = 'neutral',
  dot = false,
  className = '',
}: {
  children: ReactNode;
  tone?: Tone;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span className={`badge badge-${tone} ${className}`}>
      {dot && <span className="badge-dot" />}
      {children}
    </span>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}

export function Card({
  children,
  className = '',
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return <div className={`card ${padded ? 'card-padded' : ''} ${className}`}>{children}</div>;
}

export function Field({
  label,
  hint,
  error,
  children,
  className = '',
}: {
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <label className={`field ${className}`}>
      <span className="field-label">
        {label}
        {hint && <span className="field-hint">{hint}</span>}
      </span>
      {children}
      {error && <span className="field-error">{error}</span>}
    </label>
  );
}

export function Button({
  children,
  variant = 'primary',
  loading = false,
  className = '',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  loading?: boolean;
}) {
  return (
    <button
      className={`button button-${variant} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && <Loader2 size={16} className="spin" />}
      {children}
    </button>
  );
}

export function SectionTitle({
  title,
  description,
  right,
}: {
  title: string;
  description?: string;
  right?: ReactNode;
}) {
  return (
    <div className="section-title">
      <div>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {right}
    </div>
  );
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="banner banner-danger" role="alert">
      <AlertCircle size={18} />
      <span>{message}</span>
      {onRetry && (
        <button type="button" onClick={onRetry} className="banner-action">
          Retry
        </button>
      )}
    </div>
  );
}

export function MetaBar({ meta }: { meta: ApiMeta }) {
  const [copied, setCopied] = useState(false);
  const providerTone: Tone =
    meta.provider === 'demo' || meta.provider === 'fallback' ? 'warn' : 'success';

  async function copyId() {
    try {
      await navigator.clipboard.writeText(meta.request_id);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="meta-bar">
      <div className="meta-row">
        <Badge tone={providerTone} dot>
          {meta.provider === 'demo'
            ? 'Demo AI'
            : meta.provider === 'fallback'
              ? 'Fallback engine'
              : meta.provider === 'open-meteo'
                ? 'Open-Meteo live'
                : `${titleCase(meta.provider)} live`}
        </Badge>
        {meta.model && <span className="meta-item">{meta.model}</span>}
        <span className="meta-item">{meta.latency_ms} ms</span>
        <button type="button" className="meta-item meta-copy" onClick={copyId} title="Copy request ID">
          <Copy size={12} />
          {copied ? 'Copied' : meta.request_id.slice(0, 8)}
        </button>
      </div>
      {meta.notices.length > 0 && (
        <div className="meta-notices">
          {meta.notices.map((notice) => (
            <div key={notice} className="meta-notice">
              <Info size={14} />
              <span>{notice}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
}: {
  icon?: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon || <ImageIcon size={22} />}</div>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

export function Spinner({ label = 'Analyzing' }: { label?: string }) {
  return (
    <div className="loading-block">
      <div className="loading-orb">
        <Loader2 size={22} className="spin" />
      </div>
      <div>
        <strong>{label}</strong>
        <p>Running multimodal analysis and validating the JSON contract…</p>
      </div>
    </div>
  );
}

export function ImageDropzone({
  file,
  onFile,
  onError,
  required = false,
}: {
  file: File | null;
  onFile: (file: File | null) => void;
  onError?: (message: string) => void;
  required?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const preview = useMemo(() => (file ? URL.createObjectURL(file) : ''), [file]);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  function accept(next: File | null) {
    if (!next) {
      onFile(null);
      return;
    }
    if (!next.type.startsWith('image/')) {
      onError?.('Please choose a JPG, PNG, or WebP image.');
      return;
    }
    if (next.size > 8 * 1024 * 1024) {
      onError?.('Image is larger than 8 MB. Please compress or resize it.');
      return;
    }
    onError?.('');
    onFile(next);
  }

  function handleInput(event: ChangeEvent<HTMLInputElement>) {
    accept(event.target.files?.[0] || null);
    event.target.value = '';
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    accept(event.dataTransfer.files?.[0] || null);
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleInput}
        hidden
      />
      {file && preview ? (
        <div className="image-preview">
          <img src={preview} alt="Selected construction site" />
          <div className="image-preview-actions">
            <Badge tone="success">
              {file.name.length > 28 ? `${file.name.slice(0, 25)}…` : file.name}
            </Badge>
            <button type="button" className="icon-button" onClick={() => onFile(null)} aria-label="Remove image">
              <X size={16} />
            </button>
          </div>
        </div>
      ) : (
        <div
          className={`dropzone ${dragging ? 'dropzone-active' : ''}`}
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') inputRef.current?.click();
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <div className="dropzone-icon">
            <UploadCloud size={22} />
          </div>
          <strong>{required ? 'Upload a construction image' : 'Upload a site photograph'}</strong>
          <p>Drag & drop or click to browse · JPG, PNG, WebP · max 8 MB</p>
        </div>
      )}
    </div>
  );
}

export function RiskGauge({
  score,
  level,
  label = 'Risk score',
}: {
  score: number;
  level: string;
  label?: string;
}) {
  const safeScore = Math.max(0, Math.min(100, score));
  const tone = ['critical', 'high'].includes(level.toLowerCase())
    ? '#f87171'
    : ['moderate', 'medium', 'severe'].includes(level.toLowerCase())
      ? '#fbbf24'
      : '#34d399';
  const arc = Math.PI * 70;
  return (
    <div className="gauge">
      <svg viewBox="0 0 180 108" role="img" aria-label={`${label}: ${score} out of 100`}>
        <path d="M20 94 A70 70 0 0 1 160 94" className="gauge-track" />
        <path
          d="M20 94 A70 70 0 0 1 160 94"
          className="gauge-value"
          style={{
            stroke: tone,
            strokeDasharray: `${(safeScore / 100) * arc} ${arc}`,
          }}
        />
      </svg>
      <div className="gauge-center">
        <strong style={{ color: tone }}>{score}</strong>
        <span>{level}</span>
      </div>
      <div className="gauge-caption">{label}</div>
    </div>
  );
}

export function ScoreRing({
  score,
  label,
  tone = '#2dd4bf',
}: {
  score: number;
  label: string;
  tone?: string;
}) {
  const circumference = 2 * Math.PI * 26;
  const safe = Math.max(0, Math.min(100, score));
  return (
    <div className="score-ring">
      <svg viewBox="0 0 64 64" role="img" aria-label={`${label}: ${score}%`}>
        <circle cx="32" cy="32" r="26" className="ring-track" />
        <circle
          cx="32"
          cy="32"
          r="26"
          className="ring-value"
          style={{
            stroke: tone,
            strokeDasharray: `${(safe / 100) * circumference} ${circumference}`,
          }}
        />
      </svg>
      <div className="score-ring-center">
        <strong>{score}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

export function Stat({
  label,
  value,
  hint,
  icon,
  tone,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  tone?: Tone;
}) {
  return (
    <div className="stat">
      <div className="stat-top">
        <span>{label}</span>
        {icon && <span className={`stat-icon tone-${tone || 'neutral'}`}>{icon}</span>}
      </div>
      <strong>{value}</strong>
      {hint && <span className="stat-hint">{hint}</span>}
    </div>
  );
}

export function CheckList({ items, tone = 'accent' }: { items: string[]; tone?: Tone }) {
  return (
    <ul className={`check-list check-${tone}`}>
      {items.map((item) => (
        <li key={item}>
          <span className="check-icon">
            <Check size={12} />
          </span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

const ROOM_COLORS: Record<string, string> = {
  living: '#25443c',
  bedroom: '#22364d',
  kitchen: '#45351d',
  bathroom: '#263746',
  dining: '#2f4034',
  balcony: '#2a3a2c',
  circulation: '#1b2532',
  office: '#213a4d',
  meeting: '#2c3651',
  reception: '#433a24',
  pantry: '#3b3323',
  utility: '#2a2f38',
  storage: '#30343c',
  industrial: '#3a3023',
  loading: '#342b22',
  control: '#233a44',
  welfare: '#333f2c',
};

export function FloorPlan({ rooms, width, length }: { rooms: RoomLayout[]; width: number; length: number }) {
  return (
    <div className="floor-plan">
      <svg viewBox={`0 0 ${width} ${length}`} role="img" aria-label="Conceptual typical floor plan">
        <rect x="0" y="0" width={width} height={length} fill="#0f151d" stroke="#33465b" strokeWidth="0.35" />
        {rooms.map((room) => {
          const fontSize = Math.max(0.55, Math.min(2.2, Math.min(room.width_ft, room.length_ft) * 0.13));
          const label = room.name.length > 18 ? `${room.name.slice(0, 16)}…` : room.name;
          return (
            <g key={`${room.name}-${room.x_ft}-${room.y_ft}`}>
              <rect
                x={room.x_ft}
                y={room.y_ft}
                width={room.width_ft}
                height={room.length_ft}
                fill={ROOM_COLORS[room.room_type] || '#252c36'}
                stroke="#40536a"
                strokeWidth="0.18"
              />
              <text
                x={room.x_ft + room.width_ft / 2}
                y={room.y_ft + room.length_ft / 2 - fontSize * 0.2}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#e7eef7"
                fontSize={fontSize}
                fontFamily="Inter, Segoe UI, sans-serif"
                fontWeight="600"
              >
                {label}
              </text>
              <text
                x={room.x_ft + room.width_ft / 2}
                y={room.y_ft + room.length_ft / 2 + fontSize * 1.15}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#9fb0c3"
                fontSize={fontSize * 0.62}
                fontFamily="Inter, Segoe UI, sans-serif"
              >
                {room.area_sqft.toFixed(0)} sq ft
              </text>
              <title>
                {room.name} · {room.width_ft} × {room.length_ft} ft · {room.area_sqft} sq ft
              </title>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
