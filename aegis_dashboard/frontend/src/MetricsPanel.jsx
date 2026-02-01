import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

function MetricsPanel() {
  const [metrics, setMetrics] = useState({
    requests: [],
    deception: [],
    activeSessions: 0,
    cryptoErrors: 0
  });
  const [coreBUrl, setCoreBUrl] = useState("http://localhost:8001");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/metrics?target=${encodeURIComponent(coreBUrl)}`);
      const text = await res.text();

      if (res.status !== 200) throw new Error(text);

      parsePrometheus(text);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const parsePrometheus = (text) => {
    const lines = text.split('\n');
    let totalHonest = 0;
    let totalDeceptive = 0;
    let sessions = 0;
    let cErrors = 0;

    // Simple parser for MVP
    lines.forEach(line => {
      if (line.startsWith('#')) return;
      if (!line) return;

      if (line.startsWith('aegis_requests_total')) {
        const val = parseFloat(line.split(' ')[1]);
        if (line.includes('status="success_honest"')) totalHonest += val;
        if (line.includes('status="success_deceptive"')) totalDeceptive += val;
      }
      if (line.startsWith('aegis_active_sessions')) {
        sessions = parseFloat(line.split(' ')[1]);
      }
      if (line.startsWith('aegis_crypto_errors')) {
        cErrors = parseFloat(line.split(' ')[1]);
      }
    });

    setMetrics({
      requests: [
        { name: 'Honest', value: totalHonest },
        { name: 'Deceptive', value: totalDeceptive },
      ],
      activeSessions: sessions,
      cryptoErrors: cErrors
    });
  };

  useEffect(() => {
    const interval = setInterval(fetchMetrics, 5000);
    fetchMetrics(); // Initial fetch
    return () => clearInterval(interval);
  }, [coreBUrl]);

  return (
    <div className="max-w-4xl mx-auto p-6 mt-10 border-t border-gray-700 pt-10">
      <h2 className="text-3xl font-bold text-aegis-green mb-6">LIVE THREAT MONITOR</h2>

      <div className="mb-6 flex gap-4">
        <input
          value={coreBUrl}
          onChange={(e) => setCoreBUrl(e.target.value)}
          className="bg-black border border-gray-600 text-white p-2 rounded w-64"
          placeholder="Core B URL (http://localhost:8001)"
        />
        <button onClick={fetchMetrics} className="text-aegis-green border border-aegis-green px-4 py-2 rounded hover:bg-aegis-green hover:text-black">
          Refresh
        </button>
      </div>

      {error && <div className="text-red-500 mb-4">Error: {error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* CARD 1: SESSIONS */}
        <div className="bg-aegis-panel p-6 rounded border border-gray-700 shadow-lg text-center">
          <h3 className="text-gray-400 text-sm uppercase">Active Secure Sessions</h3>
          <p className="text-5xl font-bold text-white mt-2">{metrics.activeSessions}</p>
        </div>

        {/* CARD 2: CRYPTO ERRORS */}
        <div className="bg-aegis-panel p-6 rounded border border-gray-700 shadow-lg text-center">
          <h3 className="text-gray-400 text-sm uppercase">Crypto/Auth Errors</h3>
          <p className={`text-5xl font-bold mt-2 ${metrics.cryptoErrors > 0 ? 'text-red-500' : 'text-green-500'}`}>
            {metrics.cryptoErrors}
          </p>
        </div>

        {/* CARD 3: DECEPTION RATE */}
        <div className="bg-aegis-panel p-6 rounded border border-gray-700 shadow-lg flex flex-col items-center justify-center">
           <h3 className="text-gray-400 text-sm uppercase mb-2">Deception Ratio</h3>
           <div className="w-full h-32">
             <ResponsiveContainer width="100%" height="100%">
               <BarChart data={metrics.requests}>
                 <XAxis dataKey="name" stroke="#8884d8" />
                 <Tooltip contentStyle={{backgroundColor: '#0d1117', border: '1px solid #333'}} />
                 <Bar dataKey="value" fill="#00ff41" />
               </BarChart>
             </ResponsiveContainer>
           </div>
        </div>
      </div>
    </div>
  );
}

export default MetricsPanel;
