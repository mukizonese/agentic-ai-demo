'use client'

import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react'
import { chatAPI } from '@/lib/api'
import type { AgentStatus as AgentStatusType, MCPConfig } from '@/types/chat'

export default function AgentStatus() {
  const [status, setStatus] = useState<AgentStatusType | null>(null)
  const [config, setConfig] = useState<MCPConfig | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const [statusData, configData] = await Promise.all([
        chatAPI.getAgentStatus(),
        chatAPI.getConfig()
      ])
      
      setStatus(statusData)
      setConfig(configData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (serviceStatus: string) => {
    switch (serviceStatus) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'not_initialized':
        return <Clock className="h-4 w-4 text-yellow-500" />
      default:
        return <XCircle className="h-4 w-4 text-red-500" />
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2">
        <RefreshCw className="h-4 w-4 animate-spin" />
        <span className="text-sm text-gray-600">Loading agent status...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-4">
        <div className="flex items-center space-x-2">
          <XCircle className="h-4 w-4 text-red-500" />
          <span className="text-sm text-red-700">Error: {error}</span>
          <button
            onClick={fetchStatus}
            className="ml-auto text-xs text-red-600 hover:text-red-800"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
        <button
          onClick={fetchStatus}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Overall Status */}
      <div className="rounded-lg bg-white p-4 shadow-sm border">
        <div className="flex items-center space-x-2">
          {getStatusIcon(status?.status || 'unknown')}
          <span className="font-medium">
            Overall Status: {status?.status || 'Unknown'}
          </span>
        </div>
      </div>

      {/* Agents Status */}
      <div className="rounded-lg bg-white p-4 shadow-sm border">
        <h4 className="mb-3 font-medium text-gray-900">AI Agents</h4>
        <div className="space-y-2">
          {status?.agents && Object.entries(status.agents).map(([agent, agentStatus]) => (
            <div key={agent} className="flex items-center justify-between">
              <span className="text-sm text-gray-700 capitalize">
                {agent.replace('_', ' ')}
              </span>
              <div className="flex items-center space-x-2">
                {getStatusIcon(agentStatus)}
                <span className="text-xs text-gray-500 capitalize">{agentStatus}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Services Status */}
      <div className="rounded-lg bg-white p-4 shadow-sm border">
        <h4 className="mb-3 font-medium text-gray-900">Services</h4>
        <div className="space-y-2">
          {status?.services && Object.entries(status.services).map(([service, serviceStatus]) => (
            <div key={service} className="flex items-center justify-between">
              <span className="text-sm text-gray-700 capitalize">
                {service.replace('_', ' ')}
              </span>
              <div className="flex items-center space-x-2">
                {getStatusIcon(serviceStatus)}
                <span className="text-xs text-gray-500 capitalize">{serviceStatus}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Configuration */}
      {config && (
        <div className="rounded-lg bg-white p-4 shadow-sm border">
          <h4 className="mb-3 font-medium text-gray-900">Configuration</h4>
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium text-gray-700">LLM Backend: </span>
              <span className="text-gray-600">
                {config.llm_backend.use_ollama && `Ollama (${config.llm_backend.ollama_model})`}
                {config.llm_backend.use_openai && 'OpenAI'}
                {config.llm_backend.use_hf && 'HuggingFace'}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Vector DB: </span>
              <span className="text-gray-600">
                {config.vector_db.use_pinecone ? 'Pinecone' : 
                 config.vector_db.use_local_vectordb ? `Local ${config.vector_db.local_vectordb_type}` : 
                 'None'}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Environment: </span>
              <span className="text-gray-600 capitalize">{config.environment}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 