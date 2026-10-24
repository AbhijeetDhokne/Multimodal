import {
  CloudSun,
  CloudRain,
  Sun,
  Wind,
  Thermometer,
  Droplet,
  CalendarClock,
  AlertTriangle,
  ShieldCheck,
  Clock,
} from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, errorMessage } from '../api/client';
import type { ApiResponse, WeatherResult } from '../api/types';
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
import { formatDate, titleCase } from '../lib/format';

export function Weather() {
  const [city, setCity] = useState('Pune');
  const [lat, setLat] = useState<string>('');
  const [lon, setLon] = useState<string>('');
  const [response, setResponse] = useState<ApiResponse<WeatherResult> | null>(null);
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
      const parsedLat = lat.trim() ? Number(lat) : undefined;
      const parsedLon = lon.trim() ? Number(lon) : undefined;
      if ((parsedLat !== undefined) !== (parsedLon !== undefined)) {
        setError('Provide both latitude and longitude, or neither.');
        setLoading(false);
        return;
      }
      setResponse(await api.weather({ city: city.trim() || undefined, lat: parsedLat, lon: parsedLon }));
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
        eyebrow="Weather advisory"
        title="Weather Advisory"
        description="Live forecast translated into construction-specific work windows and site warnings."
        actions={<Badge tone="info">Live weather</Badge>}
      />

      <div className="workbench">
        <Card className="form-card">
          <SectionTitle title="Location" description="Enter a city, or latitude/longitude for a precise site." />
          <form onSubmit={submit} className="stack">
            <div className="form-grid">
              <Field label="City">
                <input
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  maxLength={80}
                  placeholder="e.g. Pune"
                />
              </Field>
              <Field label="Mode hint">
                <select value={lat || lon ? 'coords' : 'city'} onChange={() => {}}>
                  <option value="city">City lookup (Open-Meteo)</option>
                  <option value="coords">Latitude / Longitude</option>
                </select>
              </Field>
            </div>
            <div className="form-grid">
              <Field label="Latitude">
                <input type="number" step="any" value={lat} onChange={(e) => setLat(e.target.value)} placeholder="-90 to 90" />
              </Field>
              <Field label="Longitude">
                <input type="number" step="any" value={lon} onChange={(e) => setLon(e.target.value)} placeholder="-180 to 180" />
              </Field>
            </div>
            {error && <ErrorBanner message={error} />}
            <Button type="submit" loading={loading} className="button-block">
              {loading ? 'Fetching forecast…' : 'Get weather advisory'}
            </Button>
            <p className="form-footnote">
              Powered by Open-Meteo (no API key required). Use official warnings for go/no-go decisions.
            </p>
          </form>
        </Card>

        <div className="result-column" ref={resultRef}>
          {loading && (
            <Card>
              <Spinner label="Fetching weather" />
            </Card>
          )}

          {!loading && !result && (
            <Card>
              <EmptyState
                icon={<CloudSun size={24} />}
                title="Your weather advisory will appear here"
                description="Enter a city or coordinates to get current conditions, a 7-day forecast, and work-window guidance."
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
                      <Badge tone={result.data_source === 'demo' ? 'warn' : 'success'} dot>
                        {titleCase(result.data_source)}
                      </Badge>
                      <Badge tone="neutral">{result.location.country || result.location.region || ''}</Badge>
                    </div>
                    <span className="valuation-label">Current conditions · {result.location.name}</span>
                    <h2>{result.current.temperature_c.toFixed(1)}°C</h2>
                    <p className="valuation-range">
                      {result.current.condition} · {result.current.humidity_pct}% humidity · wind {result.current.wind_speed_kmh.toFixed(0)} km/h
                    </p>
                  </div>
                  <div className="valuation-location">
                    <MapPinIcon size={17} />
                    <span>
                      {result.location.latitude.toFixed(4)}, {result.location.longitude.toFixed(4)}
                    </span>
                  </div>
                </div>

                <p className="valuation-summary">{result.summary}</p>

                <div className="stats-grid stats-grid-compact">
                  <Stat label="Temperature" value={`${result.current.temperature_c.toFixed(1)}°C`} icon={<Thermometer size={15} />} tone="warn" />
                  <Stat label="Feels like" value={`${result.current.feels_like_c.toFixed(1)}°C`} icon={<Thermometer size={15} />} tone="info" />
                  <Stat label="Humidity" value={`${result.current.humidity_pct}%`} icon={<Droplet size={15} />} tone="info" />
                  <Stat label="Wind" value={`${result.current.wind_speed_kmh.toFixed(0)} km/h`} icon={<Wind size={15} />} tone="accent" />
                </div>
              </Card>

              <div className="two-col">
                <Card>
                  <SectionTitle
                    title="Site advisories"
                    description={`${result.advisories.length} weather-based recommendations.`}
                    right={<AlertTriangle size={18} className="muted-icon" />}
                  />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
                    {result.advisories.map((adv, i) => (
                      <div key={i} style={{ padding: '8px 10px', borderRadius: 7, border: `1px solid var(--border)`, background: 'var(--surface)', fontSize: 12.5, lineHeight: 1.5 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8, marginBottom: 3 }}>
                          <strong style={{ color: 'var(--text)' }}>{adv.activity}</strong>
                          <Badge tone={adv.severity === 'high' ? 'danger' : adv.severity === 'medium' ? 'warn' : 'success'} dot>
                            {titleCase(adv.severity)}
                          </Badge>
                        </div>
                        <p style={{ margin: 0, color: 'var(--muted)' }}>{adv.advice}</p>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card>
                  <SectionTitle
                    title="Work windows (next 5 days)"
                    description="Best hours for normal site activities."
                    right={<Clock size={18} className="muted-icon" />}
                  />
                  <div style={{ marginTop: 8 }}>
                    {result.work_windows.map((w) => (
                      <div key={w.date} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', borderBottom: '1px solid var(--border)', fontSize: 12.5 }}>
                        <div>
                          <div style={{ color: 'var(--text)', fontWeight: 600 }}>{formatDate(w.date)}</div>
                          <div style={{ color: 'var(--muted)', fontSize: 11.5 }}>{w.window}</div>
                        </div>
                        <Badge tone={w.suitability === 'good' ? 'success' : w.suitability === 'caution' ? 'warn' : 'danger'} dot>
                          {titleCase(w.suitability)}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              <Card className="disclaimer-card">
                <ShieldCheck size={16} />
                <p>{result.disclaimer}</p>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MapPinIcon({ size = 17 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  );
}
