import { Component, type ErrorInfo, type ReactNode } from 'react';

interface State {
  hasError: boolean;
  message: string;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { hasError: false, message: '' };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ConstructIQ UI error', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="fatal-error">
          <h1>Something went wrong in the interface</h1>
          <p>{this.state.message || 'An unexpected rendering error occurred.'}</p>
          <button type="button" className="button button-primary" onClick={() => window.location.reload()}>
            Reload application
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
