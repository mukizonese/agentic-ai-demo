export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  agentResponses?: AgentResponse[]
  processingTime?: number
  isError?: boolean
}

export interface AgentResponse {
  agent_name: string
  response: string
  processing_time: number
  sources?: string[]
}

export interface ChatResponse {
  response: string
  agent_responses: AgentResponse[]
  total_processing_time: number
  session_id: string
}

export interface ChatRequest {
  message: string
  user_id?: string
  session_id?: string
}

export interface MCPConfig {
  llm_backend: {
    use_ollama: boolean
    use_openai: boolean
    use_hf: boolean
    ollama_model: string
  }
  vector_db: {
    use_pinecone: boolean
    use_local_vectordb: boolean
    local_vectordb_type: string
  }
  environment: string
}

export interface AgentStatus {
  status: string
  agents: {
    support_agent: string
    product_agent: string
    knowledge_agent: string
  }
  services: {
    llm_service: string
    vector_service: string
  }
} 