import axios from 'axios'
import type { ChatRequest, ChatResponse, MCPConfig, AgentStatus } from '@/types/chat'

const API_BASE_URL = process.env.NEXT_PUBLIC_MCP_SERVER_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message)
    
    if (error.response?.status === 503) {
      throw new Error('The AI service is currently initializing. Please try again in a moment.')
    } else if (error.response?.status >= 500) {
      throw new Error('Server error occurred. Please try again later.')
    } else if (error.response?.status === 404) {
      throw new Error('Service not found. Please check your connection.')
    } else if (error.code === 'ECONNREFUSED' || error.code === 'NETWORK_ERROR') {
      throw new Error('Unable to connect to the AI service. Please check if the server is running.')
    }
    
    throw error
  }
)

export const chatAPI = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/chat', request)
    return response.data
  },

  async getHealth(): Promise<{ status: string; service: string; agents_initialized: boolean }> {
    const response = await apiClient.get('/health')
    return response.data
  },

  async getConfig(): Promise<MCPConfig> {
    const response = await apiClient.get<MCPConfig>('/config')
    return response.data
  },

  async getAgentStatus(): Promise<AgentStatus> {
    const response = await apiClient.get<AgentStatus>('/agents/status')
    return response.data
  },
}

export const healthCheck = async (): Promise<boolean> => {
  try {
    await chatAPI.getHealth()
    return true
  } catch (error) {
    console.error('Health check failed:', error)
    return false
  }
}

export default apiClient 