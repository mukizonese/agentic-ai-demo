'use client'

import { useState } from 'react'
import { X, MessageSquare, Plus, Trash2, Settings, Info } from 'lucide-react'
import { useChat } from '@/contexts/ChatContext'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { clearMessages, sessionId, setSessionId } = useChat()
  const [sessions] = useState(['default', 'session-1', 'session-2'])

  const handleNewChat = () => {
    clearMessages()
    const newSessionId = `session-${Date.now()}`
    setSessionId(newSessionId)
    onClose()
  }

  const handleClearChat = () => {
    clearMessages()
    onClose()
  }

  const handleSessionSelect = (selectedSessionId: string) => {
    setSessionId(selectedSessionId)
    clearMessages()
    onClose()
  }

  return (
    <>
      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 lg:shadow-none lg:border-r lg:border-gray-200
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-200 p-4 lg:hidden">
            <h2 className="text-lg font-semibold text-gray-900">Menu</h2>
            <button
              onClick={onClose}
              className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <div className="flex-1 overflow-y-auto p-4">
            {/* New Chat */}
            <button
              onClick={handleNewChat}
              className="w-full mb-4 flex items-center space-x-3 rounded-lg bg-primary-600 px-4 py-3 text-white hover:bg-primary-700 transition-colors"
            >
              <Plus className="h-5 w-5" />
              <span className="font-medium">New Chat</span>
            </button>

            {/* Chat Sessions */}
            <div className="mb-6">
              <h3 className="mb-3 text-sm font-medium text-gray-700">Chat Sessions</h3>
              <div className="space-y-1">
                {sessions.map((session) => (
                  <button
                    key={session}
                    onClick={() => handleSessionSelect(session)}
                    className={`
                      w-full flex items-center space-x-3 rounded-lg px-3 py-2 text-left text-sm transition-colors
                      ${session === sessionId 
                        ? 'bg-primary-100 text-primary-700' 
                        : 'text-gray-600 hover:bg-gray-100'
                      }
                    `}
                  >
                    <MessageSquare className="h-4 w-4" />
                    <span className="truncate">{session}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-1">
              <button
                onClick={handleClearChat}
                className="w-full flex items-center space-x-3 rounded-lg px-3 py-2 text-left text-sm text-gray-600 hover:bg-gray-100 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                <span>Clear Current Chat</span>
              </button>
              
              <button className="w-full flex items-center space-x-3 rounded-lg px-3 py-2 text-left text-sm text-gray-600 hover:bg-gray-100 transition-colors">
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </button>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 p-4">
            <div className="rounded-lg bg-gray-50 p-3">
              <div className="flex items-start space-x-2">
                <Info className="h-4 w-4 text-gray-500 mt-0.5" />
                <div className="text-xs text-gray-600">
                  <p className="font-medium mb-1">Multi-Agent AI</p>
                  <p>Powered by Support, Product, and Knowledge agents working together.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
} 