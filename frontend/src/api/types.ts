export type Provider = 'gemini' | 'openai' | 'demo' | 'fallback' | 'open-meteo';
export type Severity = 'low' | 'medium' | 'high' | 'critical';

export interface ApiMeta {
  request_id: string;
  feature: string;
  provider: Provider;
  model: string | null;
  generated_at: string;
  latency_ms: number;
  demo_mode: boolean;
  notices: string[];
  app_version: string;
}

export interface ApiResponse<T> {
  meta: ApiMeta;
  result: T;
}

export interface ApiErrorDetail {
  field?: string | null;
  message: string;
}

export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
    request_id: string;
    details: ApiErrorDetail[];
  };
}

export interface HealthResult {
  status: 'ok' | 'degraded';
  app_name: string;
  version: string;
  environment: string;
  ai_provider: Provider;
  ai_model: string | null;
  demo_mode: boolean;
  ai_configured: boolean;
  features: string[];
  uptime_seconds: number;
  server_time: string;
  docs_url: string;
}

export interface Hazard {
  id: string;
  title: string;
  category: string;
  severity: Severity;
  likelihood: string;
  location: string;
  description: string;
  corrective_action: string;
  ppe_required: string[];
}

export interface SafetyResult {
  risk_score: number;
  risk_level: 'low' | 'moderate' | 'high' | 'critical';
  summary: string;
  hazards: Hazard[];
  ppe: {
    overall: string;
    observed: string[];
    missing: string[];
    score: number;
  };
  immediate_actions: string[];
  positive_observations: string[];
  confidence: number;
  image_quality: string;
  disclaimer: string;
}

export interface CrackResult {
  detected: boolean;
  crack_type: string;
  severity: 'minor' | 'moderate' | 'severe' | 'critical';
  severity_score: number;
  summary: string;
  affected_element: string;
  probable_causes: string[];
  measurements: {
    estimated_length_cm: number | null;
    estimated_width_mm: number | null;
    confidence: number;
  };
  recommended_actions: string[];
  urgency: string;
  requires_professional_inspection: boolean;
  confidence: number;
  image_quality: string;
  disclaimer: string;
}

export interface MaterialItem {
  name: string;
  quantity: number;
  unit: string;
  unit_cost: number;
  estimated_cost: number;
  notes: string;
}

export interface ScheduleTask {
  id: string;
  name: string;
  phase: string;
  duration_days: number;
  start_day: number;
  end_day: number;
  start_date: string;
  end_date: string;
  depends_on: string[];
}

export interface RoomLayout {
  name: string;
  room_type: string;
  x_ft: number;
  y_ft: number;
  width_ft: number;
  length_ft: number;
  area_sqft: number;
}

export interface PlanningResult {
  project_type: string;
  built_up_area_sqft: number;
  floors: number;
  location: string;
  quality: string;
  currency: 'INR' | 'USD';
  cost: {
    structural: number;
    finishing: number;
    mep: number;
    labor: number;
    permits: number;
    contingency: number;
    total: number;
    cost_per_sqft: number;
  };
  materials: MaterialItem[];
  schedule: {
    total_duration_days: number;
    start_date: string;
    end_date: string;
    tasks: ScheduleTask[];
    critical_path: string[];
  };
  concept: {
    style: string;
    description: string;
    key_features: string[];
    color_palette: { name: string; hex: string }[];
    sustainability_notes: string[];
  };
  floor_plan: {
    total_width_ft: number;
    total_length_ft: number;
    typical_floor_area_sqft: number;
    rooms: RoomLayout[];
    notes: string[];
  };
  assumptions: string[];
  risks: string[];
  recommendations: string[];
}

export interface ValuationResult {
  property_type: string;
  city: string;
  locality: string | null;
  area_sqft: number;
  currency: string;
  estimated_value: number;
  value_range_low: number;
  value_range_high: number;
  price_per_sqft: number;
  confidence: number;
  market_outlook: 'declining' | 'stable' | 'growing';
  summary: string;
  comparable_sales: {
    description: string;
    area_sqft: number;
    price_per_sqft: number;
    estimated_value: number;
  }[];
  valuation_factors: { factor: string; impact: string; description: string }[];
  recommendations: string[];
  assumptions: string[];
  disclaimer: string;
}

export interface AssistantResult {
  answer: string;
  action_items: string[];
  safety_alerts: string[];
  follow_up_questions: string[];
  references: string[];
  confidence: number;
  disclaimer: string;
}

export interface KnowledgeResult {
  topic: string;
  answer: string;
  key_points: string[];
  practical_tips: string[];
  references: { title: string; source: string }[];
  related_topics: string[];
  confidence: number;
  disclaimer: string;
}

export interface WeatherResult {
  location: {
    name: string;
    region: string | null;
    country: string | null;
    latitude: number;
    longitude: number;
    timezone: string;
  };
  current: {
    temperature_c: number;
    feels_like_c: number;
    humidity_pct: number;
    wind_speed_kmh: number;
    precipitation_mm: number;
    weather_code: number;
    condition: string;
    is_day: boolean;
  };
  forecast: {
    date: string;
    min_c: number;
    max_c: number;
    precipitation_probability_pct: number;
    precipitation_mm: number;
    wind_max_kmh: number;
    condition: string;
  }[];
  advisories: { severity: 'low' | 'medium' | 'high'; activity: string; advice: string }[];
  work_windows: { date: string; window: string; suitability: string; reason: string }[];
  summary: string;
  data_source: string;
  disclaimer: string;
}

export interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface ProjectContext {
  project_type: string;
  stage: string;
  location: string;
  notes: string;
}
