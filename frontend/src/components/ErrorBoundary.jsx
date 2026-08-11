import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught render error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex flex-col items-center justify-center p-8 bg-bgSurface/50 border border-red-500/20 rounded-3xl text-center backdrop-blur-xl">
          <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400 mb-4 font-mono text-xl font-bold">
            !
          </div>
          <h3 className="font-display text-2xl font-bold text-textPrimary mb-2">
            Component Render Error
          </h3>
          <p className="font-body text-textMuted text-sm max-w-md mb-6 leading-relaxed">
            An unexpected error occurred while rendering this section. You can try refreshing or resetting the component.
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-6 py-2.5 bg-accentPrimary text-black font-mono text-xs font-bold uppercase tracking-wider rounded-full hover:brightness-110 transition-all cursor-pointer shadow-[0_0_15px_rgba(210,248,91,0.3)]"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
