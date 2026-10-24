import { Route, Routes } from 'react-router-dom';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Layout } from './components/Layout';
import { Assistant } from './pages/Assistant';
import { Crack } from './pages/Crack';
import { Dashboard } from './pages/Dashboard';
import { Knowledge } from './pages/Knowledge';
import { NotFound } from './pages/NotFound';
import { Planning } from './pages/Planning';
import { Safety } from './pages/Safety';
import { Valuation } from './pages/Valuation';
import { Weather } from './pages/Weather';

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="safety" element={<Safety />} />
          <Route path="crack" element={<Crack />} />
          <Route path="planning" element={<Planning />} />
          <Route path="valuation" element={<Valuation />} />
          <Route path="assistant" element={<Assistant />} />
          <Route path="weather" element={<Weather />} />
          <Route path="knowledge" element={<Knowledge />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}
