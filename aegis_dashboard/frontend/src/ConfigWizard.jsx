import React, { useState } from 'react';

function ConfigWizard() {
  const [formData, setFormData] = useState({
    backend_url: "http://host.docker.internal:8080",
    core_a_port: 8000,
    core_b_grpc_port: 50051,
    core_b_http_port: 8001,
    session_ttl: 600,
    use_redis: false,
    redis_url: "redis://redis:6379"
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleDownload = async () => {
    try {
      const response = await fetch('/api/generate-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) throw new Error("Generation failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "aegis_config.zip";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold text-aegis-green mb-2">AEGIS CONTROL CENTER</h1>
        <p className="text-gray-400">Generate your secure moving-target defense configuration</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

        {/* NETWORK SETTINGS */}
        <div className="bg-aegis-panel p-6 rounded border border-gray-700 shadow-lg">
          <h2 className="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-2">Network Configuration</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Target Backend URL</label>
              <input
                type="text"
                name="backend_url"
                value={formData.backend_url}
                onChange={handleChange}
                className="w-full bg-black border border-gray-600 rounded p-2 text-white focus:border-aegis-green outline-none"
              />
              <p className="text-xs text-gray-500 mt-1">The actual service you want to protect</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Core A Port</label>
                <input
                  type="number"
                  name="core_a_port"
                  value={formData.core_a_port}
                  onChange={handleChange}
                  className="w-full bg-black border border-gray-600 rounded p-2 text-white focus:border-aegis-green outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Core B gRPC Port</label>
                <input
                  type="number"
                  name="core_b_grpc_port"
                  value={formData.core_b_grpc_port}
                  onChange={handleChange}
                  className="w-full bg-black border border-gray-600 rounded p-2 text-white focus:border-aegis-green outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* SECURITY SETTINGS */}
        <div className="bg-aegis-panel p-6 rounded border border-gray-700 shadow-lg">
          <h2 className="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-2">Security Policy</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Session TTL (seconds)</label>
              <input
                type="number"
                name="session_ttl"
                value={formData.session_ttl}
                onChange={handleChange}
                className="w-full bg-black border border-gray-600 rounded p-2 text-white focus:border-aegis-green outline-none"
              />
              <p className="text-xs text-gray-500 mt-1">Key rotation interval (lower = safer but more overhead)</p>
            </div>

            <div className="flex items-center space-x-3 mt-6">
              <input
                type="checkbox"
                name="use_redis"
                checked={formData.use_redis}
                onChange={handleChange}
                className="w-5 h-5 accent-aegis-green"
              />
              <label className="text-sm text-gray-300">Enable Redis Rate Limiting</label>
            </div>

            {formData.use_redis && (
               <div>
               <label className="block text-sm text-gray-400 mb-1">Redis URL</label>
               <input
                 type="text"
                 name="redis_url"
                 value={formData.redis_url}
                 onChange={handleChange}
                 className="w-full bg-black border border-gray-600 rounded p-2 text-white focus:border-aegis-green outline-none"
               />
             </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-10 text-center">
        <button
          onClick={handleDownload}
          className="bg-aegis-green hover:bg-green-400 text-black font-bold py-3 px-8 rounded shadow-lg transform transition hover:scale-105"
        >
          DOWNLOAD CONFIGURATION
        </button>
        <p className="text-sm text-gray-500 mt-4">Generates docker-compose.yml and README</p>
      </div>
    </div>
  );
}

export default ConfigWizard;
