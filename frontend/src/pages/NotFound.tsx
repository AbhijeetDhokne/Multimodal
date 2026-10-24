import { AlertCircle } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { Card, EmptyState, PageHeader } from '../components/UI';

export function NotFound() {
  const { pathname } = useLocation();

  return (
    <div className="page">
      <PageHeader
        eyebrow="Not found"
        title="Page not found"
        description={`The path “${pathname}” doesn't exist in ConstructIQ.`}
      />

      <div style={{ maxWidth: 520, margin: '0 auto' }}>
        <Card className="form-card">
          <EmptyState
            icon={<AlertCircle size={32} />}
            title="Page not found"
            description="Check the URL or return to the dashboard and pick a module from the sidebar."
          />
          <div style={{ marginTop: 18, display: 'flex', gap: 10, justifyContent: 'center' }}>
            <button
              type="button"
              className="button button-primary"
              onClick={() => {
                window.location.href = '/';
              }}
            >
              Go to dashboard
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
}
