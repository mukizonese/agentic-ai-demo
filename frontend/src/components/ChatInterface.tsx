'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { useChat } from '@/contexts/ChatContext'
import MessageList from './MessageList'
import AgentStatus from './AgentStatus'

export default function ChatInterface() {
  const { messages, isLoading, sendMessage } = useChat()
  const [input, setInput] = useState('')
  const [showStatus, setShowStatus] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!input.trim() || isLoading) return

    const message = input.trim()
    setInput('')
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    await sendMessage(message)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    
    // Auto-resize textarea
    const textarea = e.target
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
  }

  const exampleQuestions = [
    "How do I reset my password?",
    "What products do you have under $200?",
    "Tell me about the SmartWidget 3000",
    "I'm having trouble with my account",
    "What are your most popular products?",
  ]

  return (
    <div className="flex h-full flex-col">
      {/* Status Panel Toggle */}
      <div className="border-b border-gray-200 bg-white px-4 py-2">
        <button
          onClick={() => setShowStatus(!showStatus)}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          {showStatus ? 'Hide' : 'Show'} Agent Status
        </button>
      </div>

      {/* Agent Status Panel */}
      {showStatus && (
        <div className="border-b border-gray-200 bg-gray-50 p-4">
          <AgentStatus />
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto scrollbar-thin">
          <div className="mx-auto max-w-4xl px-4 py-6">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <div className="mb-8">
                  <h1 className="mb-4 text-3xl font-bold text-gray-900">
                    Welcome to Agentic AI Demo
                  </h1>
                  <p className="text-lg text-gray-600">
                    Chat with our AI agents for support, product information, and general knowledge.
                  </p>
                </div>
                
                <div className="w-full max-w-2xl">
                  <h2 className="mb-4 text-lg font-semibold text-gray-900">
                    Try asking:
                  </h2>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {exampleQuestions.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => setInput(question)}
                        className="rounded-lg border border-gray-200 bg-white p-3 text-left text-sm text-gray-700 transition-colors hover:bg-gray-50 hover:border-gray-300"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <MessageList messages={messages} />
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* Input Form */}
      <div className="border-t border-gray-200 bg-white p-4">
        <form onSubmit={handleSubmit} className="mx-auto max-w-4xl">
          <div className="flex space-x-4">
            <div className="flex-1">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything about support, products, or general questions..."
                className="chat-input min-h-[44px] max-h-[120px]"
                disabled={isLoading}
                rows={1}
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="inline-flex items-center justify-center rounded-lg bg-primary-600 px-4 py-2 text-white transition-colors hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px]"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </div>
          
          {isLoading && (
            <div className="mt-2 flex items-center text-sm text-gray-500">
              <div className="loading-dots mr-2">
                <span style={{ '--delay': 0 } as any}></span>
                <span style={{ '--delay': 1 } as any}></span>
                <span style={{ '--delay': 2 } as any}></span>
              </div>
              Processing your request...
            </div>
          )}
        </form>
      </div>
    </div>
  )
} 