import {
  ArrowDownRight,
  ArrowUpRight,
  BedDouble,
  Building2,
  CalendarClock,
  CheckCircle2,
  IndianRupee,
  Info,
  MapPin,
  Scale,
  TrendingUp,
} from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, errorMessage } from '../api/client';
import type { ApiResponse, ValuationResult } from '../api/types';
import {
  Badge,
  Button,
  Card,
  CheckList,
  EmptyState,
  ErrorBanner,
  Field,
  MetaBar,
  PageHeader,
  SectionTitle,
  Spinner,
  Stat,
} from '../components/UI';
import { formatCurrency, formatNumber, titleCase } from '../lib/format';

const AMENITIES = [
  { value: 'parking', label: 'Parking' },
  { value: 'gym', label: 'Gym' },
  { value: 'pool', label: 'Swimming pool' },
  { value: 'security', label: '24×7 security' },
  { value: 'power_backup', label: 'Power backup' },
  { value: 'lift', label: 'Lift' },
  { value: 'garden', label: 'Garden' },
  { value: 'clubhouse', label: 'Clubhouse' },
];

const OUTLOOK_TONE = {
  growing: 'success',
  stable: 'info',
  declining: 'danger',
} as const;

export function Valuation() {
  const [propertyType, setPropertyType] = useState('apartment');
  const [city, setCity] = useState('Pune');
  const [locality, setLocality] = useState('Baner');
  const [area, setArea] = useState('1200');
  const [age, setAge] = useState('5');
  const [bedrooms, setBedrooms] = useState('2');
  const [quality, setQuality] = useState('premium');
  const [condition, setCondition] = useState('good');
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>(['parking', 'lift', 'security']);
  const [response, setResponse] = useState<ApiResponse<ValuationResult> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (response) resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [response]);

  function toggleAmenity(value: string) {
    setSelectedAmenities((current) =>
      current.includes(value) ? current.filter((item) => item !== value) : [...current, value],
    );
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const areaValue = Number(area);
    if (!Number.isFinite(areaValue) || areaValue < 100) {
      setError('Area must be at least 100 sq ft.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      setResponse(
        await api.estimateValuation({
          property_type: propertyType,
          city,
          locality: locality || null,
          area_sqft: areaValue,
          age_years: Number(age) || 0,
          bedrooms: Number(bedrooms) || 0,
          quality,
          condition,
          amenities: selectedAmenities,
          currency: 'INR',
        }),
      );
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const result = response?.result;
  const marker = result
    ? Math.max(4, Math.min(96, ((result.estimated_value - result.value_range_low) / (result.value_range_high - result.value_range_low)) * 100))
    : 0;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Valuation intelligence"
        title="Real Estate Valuation"
        description="Estimate indicative market value, understand the drivers and get a defensible range for planning conversations."
        actions={<Badge tone="accent">Structured data</Badge>}
      />

      <div className="workbench">
        <Card className="form-card">
          <SectionTitle title="Property profile" description="Structured inputs keep the valuation consistent." />
          <form onSubmit={submit} className="stack">
            <div className="form-grid">
              <Field label="Property type">
                <select value={propertyType} onChange={(event) => setPropertyType(event.target.value)}>
                  <option value="apartment">Apartment</option>
                  <option value="villa">Villa</option>
                  <option value="plot">Plot</option>
                  <option value="commercial">Commercial</option>
                  <option value="office">Office</option>
                  <option value="retail">Retail</option>
                </select>
              </Field>
              <Field label="Condition">
                <select value={condition} onChange={(event) => setCondition(event.target.value)}>
                  <option value="poor">Poor</option>
                  <option value="fair">Fair</option>
                  <option value="good">Good</option>
                  <option value="excellent">Excellent</option>
                </select>
              </Field>
            </div>
            <div className="form-grid">
              <Field label="City">
                <input value={city} onChange={(event) => setCity(event.target.value)} maxLength={80} />
              </Field>
              <Field label="Locality" hint="Optional">
                <input
                  value={locality}
                  onChange={(event) => setLocality(event.target.value)}
                  maxLength={120}
                  placeholder="e.g. Baner"
                />
              </Field>
            </div>
            <div className="form-grid">
              <Field label="Area (sq ft)">
                <input type="number" min={100} step={10} value={area} onChange={(event) => setArea(event.target.value)} />
              </Field>
              <Field label="Age (years)">
                <input type="number" min={0} max={100} value={age} onChange={(event) => setAge(event.target.value)} />
              </Field>
            </div>
            <div className="form-grid">
              <Field label="Bedrooms">
                <input
                  type="number"
                  min={0}
                  max={20}
                  value={bedrooms}
                  onChange={(event) => setBedrooms(event.target.value)}
                />
              </Field>
              <Field label="Specification">
                <select value={quality} onChange={(event) => setQuality(event.target.value)}>
                  <option value="basic">Basic</option>
                  <option value="standard">Standard</option>
                  <option value="premium">Premium</option>
                  <option value="luxury">Luxury</option>
                </select>
              </Field>
            </div>

            <div className="field">
              <span className="field-label">Amenities</span>
              <div className="chip-grid">
                {AMENITIES.map((amenity) => (
                  <button
                    key={amenity.value}
                    type="button"
                    className={`chip ${selectedAmenities.includes(amenity.value) ? 'chip-active' : ''}`}
                    onClick={() => toggleAmenity(amenity.value)}
                  >
                    {selectedAmenities.includes(amenity.value) && <CheckCircle2 size={13} />}
                    {amenity.label}
                  </button>
                ))}
              </div>
            </div>

            {error && <ErrorBanner message={error} />}
            <Button type="submit" loading={loading} className="button-block">
              {loading ? 'Estimating value…' : 'Estimate property value'}
            </Button>
            <p className="form-footnote">
              Indicative city-level benchmark model. Not a substitute for a registered valuer.
            </p>
          </form>
        </Card>

        <div className="result-column" ref={resultRef}>
          {loading && (
            <Card>
              <Spinner label="Valuing the property" />
            </Card>
          )}

          {!loading && !result && (
            <Card>
              <EmptyState
                icon={<IndianRupee size={24} />}
                title="Your valuation will appear here"
                description="Complete the property profile to get an estimated value, a plausible range, value drivers and comparable benchmarks."
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
                      <Badge tone={OUTLOOK_TONE[result.market_outlook]} dot>
                        Market: {titleCase(result.market_outlook)}
                      </Badge>
                      <Badge tone="neutral">{titleCase(result.property_type)}</Badge>
                      <Badge tone="info">{Math.round(result.confidence * 100)}% confidence</Badge>
                    </div>
                    <span className="valuation-label">Estimated market value</span>
                    <h2>{formatCurrency(result.estimated_value, 'INR')}</h2>
                    <p className="valuation-range">
                      Likely range {formatCurrency(result.value_range_low, 'INR')} –{' '}
                      {formatCurrency(result.value_range_high, 'INR')}
                    </p>
                  </div>
                  <div className="valuation-location">
                    <MapPin size={17} />
                    <span>{result.locality ? `${result.locality}, ` : ''}{result.city}</span>
                    <small>{formatNumber(result.area_sqft)} sq ft</small>
                  </div>
                </div>

                <div className="range-viz">
                  <div className="range-bar">
                    <div className="range-fill" />
                    <div className="range-marker" style={{ left: `${marker}%` }}>
                      <span />
                    </div>
                  </div>
                  <div className="range-labels">
                    <span>{formatCurrency(result.value_range_low, 'INR', true)}</span>
                    <span>{formatCurrency(result.value_range_high, 'INR', true)}</span>
                  </div>
                </div>

                <p className="valuation-summary">{result.summary}</p>

                <div className="stats-grid stats-grid-compact">
                  <Stat
                    label="Price per sq ft"
                    value={formatCurrency(result.price_per_sqft, 'INR')}
                    icon={<Scale size={15} />}
                    tone="accent"
                  />
                  <Stat
                    label="Bedrooms"
                    value={formatNumber(Number(bedrooms))}
                    icon={<BedDouble size={15} />}
                    tone="info"
                  />
                  <Stat
                    label="Age"
                    value={`${formatNumber(Number(age))} yr`}
                    icon={<CalendarClock size={15} />}
                  />
                  <Stat
                    label="Outlook"
                    value={titleCase(result.market_outlook)}
                    icon={<TrendingUp size={15} />}
                    tone={result.market_outlook === 'growing' ? 'success' : 'warn'}
                  />
                </div>
              </Card>

              <div className="two-col">
                <Card>
                  <SectionTitle title="Value drivers" right={<Info size={17} className="muted-icon" />} />
                  <div className="factor-list">
                    {result.valuation_factors.map((factor) => (
                      <div key={factor.factor} className={`factor factor-${factor.impact}`}>
                        <span className="factor-icon">
                          {factor.impact === 'positive' ? (
                            <ArrowUpRight size={15} />
                          ) : factor.impact === 'negative' ? (
                            <ArrowDownRight size={15} />
                          ) : (
                            <Scale size={15} />
                          )}
                        </span>
                        <div>
                          <strong>{factor.factor}</strong>
                          <p>{factor.description}</p>
                        </div>
                        <Badge tone={factor.impact === 'positive' ? 'success' : factor.impact === 'negative' ? 'danger' : 'neutral'}>
                          {titleCase(factor.impact)}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card>
                  <SectionTitle title="Comparable benchmarks" right={<Building2 size={18} className="muted-icon" />} />
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Comparable</th>
                          <th>Area</th>
                          <th>Rate</th>
                          <th>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.comparable_sales.map((sale, index) => (
                          <tr key={sale.description}>
                            <td>Comparable {index + 1}</td>
                            <td>{formatNumber(sale.area_sqft)} sq ft</td>
                            <td>{formatCurrency(sale.price_per_sqft, 'INR')}</td>
                            <td>{formatCurrency(sale.estimated_value, 'INR', true)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="form-footnote">Benchmarks are synthetic indicators for planning, not registered transactions.</p>
                </Card>
              </div>

              <div className="two-col">
                <Card>
                  <SectionTitle title="Recommendations" />
                  <CheckList items={result.recommendations} tone="accent" />
                </Card>
                <Card>
                  <SectionTitle title="Assumptions" />
                  <CheckList items={result.assumptions} tone="info" />
                </Card>
              </div>

              <Card className="disclaimer-card">
                <Info size={16} />
                <p>{result.disclaimer}</p>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
