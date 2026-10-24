import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { HealthProvider } from './lib/health';
import './styles/main.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <HealthProvider>
        <App />
      </HealthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
