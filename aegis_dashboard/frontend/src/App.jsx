import React from 'react';
import ConfigWizard from './ConfigWizard';
import MetricsPanel from './MetricsPanel';

function App() {
  return (
    <div className="min-h-screen bg-aegis-dark text-white font-mono selection:bg-aegis-green selection:text-black">
      <ConfigWizard />
      <MetricsPanel />
    </div>
  );
}

export default App;
