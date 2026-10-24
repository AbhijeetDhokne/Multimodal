import {
  BookOpen,
  CalendarRange,
  CloudSun,
  HardHat,
  IndianRupee,
  Key,
  LayoutDashboard,
  Menu,
  MessageSquareText,
  ScanLine,
  WifiOff,
  X,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { titleCase } from '../lib/format';
import { useHealth } from '../lib/health';
import { apiKeyStore, setApiKey, clearApiKey, type AIProvider } from '../lib/apiKeyStore';
import { Badge, BrandMark } from './UI';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/safety', label: 'Site Safety', icon: HardHat },
  { to: '/crack', label: 'Crack Analysis', icon: ScanLine },
  { to: '/planning', label: 'Project Planner', icon: CalendarRange },
  { to: '/valuation', label: 'Valuation', icon: IndianRupee },
  { to: '/assistant', label: 'Site Assistant', icon: MessageSquareText },
  { to: '/weather', label: 'Weather Advisory', icon: CloudSun },
  { to: '/knowledge', label: 'Knowledge Hub', icon: BookOpen },
];

const PAGE_META: Record<string, string> = {
  '/': 'Command center',
  '/safety': 'Computer-vision safety review',
  '/crack': 'Structural crack screening',
  '/planning': 'AI-assisted project planning',
  '/valuation': 'Property valuation intelligence',
  '/assistant': 'Daily site copilot',
  '/weather': 'Weather-aware planning',
  '/knowledge': 'Construction knowledge',
};

export function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [keyInput, setKeyInput] = useState(apiKeyStore.apiKey);
  const [providerInput, setProviderInput] = useState(apiKeyStore.provider);
  const { health, error, loading, refresh } = useHealth();
  const location = useLocation();

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  const activeMeta = PAGE_META[location.pathname] || 'ConstructIQ';
  const providerLabel = error
    ? 'API offline'
    : loading && !health
      ? 'Connecting…'
      : health?.demo_mode
        ? 'Demo AI'
        : health
          ? `${titleCase(health.ai_provider)} live`
          : 'Unknown';

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-brand">
          <BrandMark size={38} />
          <div>
            <strong>ConstructIQ</strong>
            <span>Construction Intelligence</span>
          </div>
          <button
            type="button"
            className="icon-button sidebar-close"
            onClick={() => setMenuOpen(false)}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav" aria-label="Primary">
          <span className="nav-section">Workspace</span>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className={`status-dot ${error ? 'status-off' : health?.demo_mode ? 'status-warn' : 'status-on'}`} />
            <div>
              <strong>{error ? 'Backend unreachable' : health?.demo_mode ? 'Demo engine' : 'AI connected'}</strong>
              <span>{health?.ai_model || (error ? 'Start FastAPI on :8000' : 'Deterministic fallback')}</span>
            </div>
          </div>

          <div className="sidebar-ai-key">
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#5b6b7e', marginBottom: 8 }}>
              AI Provider Key <Key size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', gap: 8 }}>
                <select
                  value={providerInput}
                  onChange={(e) => setProviderInput(e.target.value as AIProvider)}
                  style={{
                    flex: 1,
                    background: 'var(--surface)',
                    border: '1px solid var(--border)',
                    color: 'var(--text)',
                    padding: '6px 8px',
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                >
                  <option value="auto">Auto</option>
                  <option value="gemini">Gemini</option>
                  <option value="openai">OpenAI</option>
                </select>
                {apiKeyStore.apiKey ? (
                  <button
                    type="button"
                    onClick={() => clearApiKey()}
                    style={{
                      background: 'transparent',
                      border: '1px solid var(--border)',
                      color: 'var(--muted)',
                      padding: '6px 10px',
                      borderRadius: 6,
                      fontSize: 12,
                      cursor: 'pointer',
                    }}
                  >
                    Clear
                  </button>
                ) : null}
              </div>
              <input
                type="password"
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                placeholder="Paste your Gemini/OpenAI API key"
                style={{
                  width: '100%',
                  background: 'var(--surface)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  padding: '8px 10px',
                  borderRadius: 6,
                  fontSize: 12,
                }}
              />
              <button
                type="button"
                onClick={() => setApiKey(keyInput, providerInput)}
                disabled={!keyInput.trim()}
                style={{
                  width: '100%',
                  background: keyInput.trim() ? 'var(--accent)' : 'var(--surface)',
                  color: keyInput.trim() ? '#0b1017' : 'var(--muted)',
                  border: 'none',
                  padding: '8px 10px',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: keyInput.trim() ? 'pointer' : 'not-allowed',
                  opacity: keyInput.trim() ? 1 : 0.5,
                }}
              >
                Save key
              </button>
              {apiKeyStore.apiKey && (
                <div style={{ fontSize: 11, color: '#2dd4bf', marginTop: 6 }}>
                  Key stored in browser memory only. Sent per-request; never saved on server.
                </div>
              )}
            </div>
          </div>

          <div className="sidebar-version">
            <span>v{health?.version || '1.0.0'}</span>
            <span>FastAPI + React</span>
          </div>
        </div>
      </aside>

      {menuOpen && <div className="sidebar-backdrop" onClick={() => setMenuOpen(false)} />}

      <div className="app-main">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="icon-button menu-button"
              onClick={() => setMenuOpen(true)}
              aria-label="Open navigation"
            >
              <Menu size={20} />
            </button>
            <div className="breadcrumb">
              <span>ConstructIQ</span>
              <span className="breadcrumb-sep">/</span>
              <strong>{activeMeta}</strong>
            </div>
          </div>
          <div className="topbar-right">
            <Badge tone={error ? 'danger' : health?.demo_mode ? 'warn' : 'success'} dot>
              {error ? (
                <>
                  <WifiOff size={12} /> {providerLabel}
                </>
              ) : (
                providerLabel
              )}
            </Badge>
            {health?.ai_model && <span className="topbar-model">{health.ai_model}</span>}
            <button type="button" className="topbar-refresh" onClick={() => void refresh()} title="Refresh backend status">
              Refresh
            </button>
          </div>
        </header>

        <main className="content">
          <Outlet />
        </main>

        <footer className="app-footer">
          <span>ConstructIQ · AI-powered multimodal construction intelligence</span>
          <span>Strict JSON contracts · FastAPI · React · Vite</span>
        </footer>
      </div>
    </div>
  );
}
