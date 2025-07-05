'use client'

import { useState, useEffect } from 'react'

// LangflowChatEmbed component for embedding a Langflow chat widget
function LangflowChatEmbed({ flowId, windowTitle }: { flowId: string; windowTitle: string }) {
  useEffect(() => {
    // Inject the Langflow embed script only once
    if (!document.getElementById('langflow-embed-script')) {
      const script = document.createElement('script');
      script.id = 'langflow-embed-script';
      script.src = 'https://cdn.jsdelivr.net/gh/logspace-ai/langflow-embedded-chat@v1.0.7/dist/build/static/js/bundle.min.js';
      script.async = true;
      document.body.appendChild(script);
    }
  }, []);

  // Remove any previous widgets before rendering a new one
  useEffect(() => {
    const prev = document.getElementById('langflow-chat-widget');
    if (prev) prev.remove();
    // Create the <langflow-chat> element
    const chat = document.createElement('langflow-chat');
    chat.setAttribute('id', 'langflow-chat-widget');
    chat.setAttribute('window_title', windowTitle);
    chat.setAttribute('flow_id', flowId);
    chat.setAttribute('host_url', 'http://localhost:7860');
    // Force a fresh session on each mount/flow switch
    chat.setAttribute('session_id', `${flowId}-${Date.now()}`);
    // Add to the container
    const container = document.getElementById('langflow-chat-container');
    if (container) container.appendChild(chat);
  }, [flowId, windowTitle]);

  return <div id="langflow-chat-container" className="w-full flex justify-center" />;
}

const FLOWS = [
  {
    key: 'support',
    label: 'Dynamic Support Agent',
    flowId: '8aa4a30e-59bb-4e20-ad2f-4a5d31a96f9d',
  },
  {
    key: 'product',
    label: 'Dynamic Product Agent',
    flowId: 'REPLACE_WITH_PRODUCT_FLOW_ID',
  },
  {
    key: 'combined',
    label: 'Combined Agent',
    flowId: 'REPLACE_WITH_COMBINED_FLOW_ID',
  },
];

export default function LangflowDemoPage() {
  const [selected, setSelected] = useState('support');
  const flow = FLOWS.find(f => f.key === selected);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-8">
      <h1 className="text-2xl font-bold mb-6">Langflow Agentic Demos</h1>
      <div className="flex space-x-4 mb-8">
        {FLOWS.map(f => (
          <button
            key={f.key}
            onClick={() => setSelected(f.key)}
            className={`px-4 py-2 rounded border ${selected === f.key ? 'bg-blue-600 text-white' : 'bg-white text-blue-600 border-blue-600'} transition`}
          >
            {f.label}
          </button>
        ))}
      </div>
      {flow && (
        <div className="w-full max-w-2xl flex flex-col items-center">
          <LangflowChatEmbed flowId={flow.flowId} windowTitle={flow.label} />
          {/* <a
            href={`http://localhost:7860/playground/${flow.flowId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 px-4 py-2 rounded border bg-white text-blue-600 border-blue-600 hover:bg-blue-50 transition font-medium"
          >
            View in Playground
          </a> */}
        </div>
      )}
    </div>
  );
}
