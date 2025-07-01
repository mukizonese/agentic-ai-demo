'use client'

import React, { createContext, useContext, useReducer, useCallback } from 'react'
import { chatAPI } from '@/lib/api'
import type { ChatMessage, ChatResponse, AgentResponse } from '@/types/chat'

interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  sessionId: string
}

type ChatAction =
  | { type: 'SEND_MESSAGE_START'; payload: { message: string } }
  | { type: 'SEND_MESSAGE_SUCCESS'; payload: { response: ChatResponse } }
  | { type: 'SEND_MESSAGE_ERROR'; payload: { error: string } }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'SET_SESSION_ID'; payload: { sessionId: string } }

interface ChatContextType extends ChatState {
  sendMessage: (message: string) => Promise<void>
  clearMessages: () => void
  setSessionId: (sessionId: string) => void
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

const initialState: ChatState = {
  messages: [],
  isLoading: false,
  error: null,
  sessionId: 'default'
}

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SEND_MESSAGE_START':
      return {
        ...state,
        isLoading: true,
        error: null,
        messages: [
          ...state.messages,
          {
            id: Date.now().toString(),
            role: 'user',
            content: action.payload.message,
            timestamp: new Date(),
          }
        ]
      }
    
    case 'SEND_MESSAGE_SUCCESS':
      return {
        ...state,
        isLoading: false,
        messages: [
          ...state.messages,
          {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: action.payload.response.response,
            timestamp: new Date(),
            agentResponses: action.payload.response.agent_responses,
            processingTime: action.payload.response.total_processing_time,
          }
        ]
      }
    
    case 'SEND_MESSAGE_ERROR':
      return {
        ...state,
        isLoading: false,
        error: action.payload.error,
        messages: [
          ...state.messages,
          {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: `I apologize, but I encountered an error: ${action.payload.error}`,
            timestamp: new Date(),
            isError: true,
          }
        ]
      }
    
    case 'CLEAR_MESSAGES':
      return {
        ...state,
        messages: [],
        error: null
      }
    
    case 'SET_SESSION_ID':
      return {
        ...state,
        sessionId: action.payload.sessionId
      }
    
    default:
      return state
  }
}

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState)
  
  const sendMessage = useCallback(async (message: string) => {
    dispatch({ type: 'SEND_MESSAGE_START', payload: { message } })
    
    try {
      const response = await chatAPI.sendMessage({
        message,
        session_id: state.sessionId,
        user_id: 'anonymous'
      })
      
      dispatch({ type: 'SEND_MESSAGE_SUCCESS', payload: { response } })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      dispatch({ type: 'SEND_MESSAGE_ERROR', payload: { error: errorMessage } })
    }
  }, [state.sessionId])
  
  const clearMessages = useCallback(() => {
    dispatch({ type: 'CLEAR_MESSAGES' })
  }, [])
  
  const setSessionId = useCallback((sessionId: string) => {
    dispatch({ type: 'SET_SESSION_ID', payload: { sessionId } })
  }, [])
  
  const value: ChatContextType = {
    ...state,
    sendMessage,
    clearMessages,
    setSessionId,
  }
  
  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const context = useContext(ChatContext)
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider')
  }
  return context
} 