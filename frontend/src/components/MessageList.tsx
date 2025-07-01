'use client'

import { format } from 'date-fns'
import { Clock, User, Bot } from 'lucide-react'
import type { ChatMessage } from '@/types/chat'

interface MessageListProps {
  messages: ChatMessage[]
}

export default function MessageList({ messages }: MessageListProps) {
  const getAgentBadgeClass = (agentName: string) => {
    const name = agentName.toLowerCase()
    if (name.includes('support')) return 'agent-badge support'
    if (name.includes('product')) return 'agent-badge product'
    if (name.includes('knowledge')) return 'agent-badge knowledge'
    return 'agent-badge general'
  }

  return (
    <div className="space-y-6">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div className={`chat-message ${message.role} animate-slide-up`}>
            {/* Message Header */}
            <div className="mb-2 flex items-center space-x-2">
              {message.role === 'user' ? (
                <User className="h-4 w-4" />
              ) : (
                <Bot className="h-4 w-4" />
              )}
              <span className="text-sm font-medium">
                {message.role === 'user' ? 'You' : 'AI Assistant'}
              </span>
              <span className="text-xs opacity-70">
                {format(message.timestamp, 'HH:mm')}
              </span>
            </div>

            {/* Message Content */}
            <div className="mb-3">
              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                {message.content}
              </p>
            </div>

            {/* Agent Responses (for assistant messages) */}
            {message.role === 'assistant' && message.agentResponses && (
              <div className="space-y-3 border-t border-gray-200 pt-3">
                <div className="text-xs font-medium text-gray-600">
                  Agent Responses:
                </div>
                {message.agentResponses.map((agent, index) => (
                  <div key={index} className="rounded bg-gray-50 p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className={getAgentBadgeClass(agent.agent_name)}>
                        {agent.agent_name}
                      </span>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <Clock className="h-3 w-3" />
                        <span>{(agent.processing_time * 1000).toFixed(0)}ms</span>
                      </div>
                    </div>
                    
                    <p className="mb-2 text-xs text-gray-700">
                      {agent.response}
                    </p>
                    
                    {agent.sources && agent.sources.length > 0 && (
                      <div className="text-xs">
                        <span className="font-medium text-gray-600">Sources: </span>
                        <span className="text-gray-500">
                          {agent.sources.join(', ')}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Processing Time */}
            {message.role === 'assistant' && message.processingTime && (
              <div className="mt-2 flex items-center space-x-1 text-xs text-gray-500">
                <Clock className="h-3 w-3" />
                <span>Total: {(message.processingTime * 1000).toFixed(0)}ms</span>
              </div>
            )}

            {/* Error State */}
            {message.isError && (
              <div className="mt-2 rounded bg-red-50 p-2 text-xs text-red-700">
                ⚠️ This message was generated due to an error.
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
} 