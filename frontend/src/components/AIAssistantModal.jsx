import React, { useState, useRef, useEffect } from 'react'
import { Bot, User, Send, Sparkles, AlertCircle, FileText, CheckCircle2 } from 'lucide-react'
import { askAIChat } from '../services/aiService'

export default function AIAssistantModal({ patientId = null, patientName = null, role = 'patient' }) {
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: role === 'doctor'
        ? `Hello Doctor. I am your Clinical Decision Support Assistant for ${patientName ? patientName : 'this patient'}. How can I assist with clinical history, report comparisons, or lab trends?`
        : 'Hello! I am your AI Health Assistant. Ask me to explain your reports, track lab trends, or clarify medical terms.',
      sources: [],
      tools: []
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (textToSend = null) => {
    const query = textToSend || inputMessage
    if (!query.trim() || loading) return

    const userMsg = { sender: 'user', text: query }
    setMessages((prev) => [...prev, userMsg])
    if (!textToSend) setInputMessage('')
    setLoading(true)

    try {
      const payload = {
        message: query,
        patient_id: patientId
      }
      const data = await askAIChat(payload)

      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: data.answer,
          sources: data.sources || [],
          tools: data.tools_used || [],
          suggestedQuestions: data.suggested_questions || []
        }
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'Sorry, I encountered an issue retrieving that information. Please try again or inspect standard reports.',
          isError: true
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const patientPrompts = [
    'Explain my latest lab report',
    'How has my HbA1c changed over time?',
    'What does high LDL cholesterol mean?',
    'Check my current medicine list'
  ]

  const doctorPrompts = [
    'Summarize patient medical history',
    'Which lab values are abnormal?',
    'Show historical trend for HbA1c',
    'Check for medication warnings'
  ]

  const defaultPrompts = role === 'doctor' ? doctorPrompts : patientPrompts

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {!isOpen ? (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-4 py-3 rounded-full shadow-lg transition-all transform hover:scale-105"
        >
          <Sparkles className="w-5 h-5" />
          <span>AI Clinical Assistant</span>
        </button>
      ) : (
        <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 w-96 sm:w-[480px] h-[580px] flex flex-col overflow-hidden transition-all">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-200" />
              <div>
                <h3 className="font-semibold text-sm">AI Clinical Assistant</h3>
                <p className="text-xs text-indigo-200">
                  {role === 'doctor' ? `Context: ${patientName || 'Patient'}` : 'Grounded Decision Support'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-indigo-200 hover:text-white text-lg font-bold px-2 py-1"
            >
              ✕
            </button>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-gray-50">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 shrink-0 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-none'
                      : msg.isError
                      ? 'bg-red-50 text-red-700 border border-red-200 rounded-bl-none'
                      : 'bg-white text-gray-800 border border-gray-200 shadow-sm rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {/* Sources metadata */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-100 flex flex-wrap gap-1">
                      <span className="text-[10px] text-gray-400 font-semibold flex items-center gap-1">
                        <FileText className="w-3 h-3" /> Sources:
                      </span>
                      {msg.sources.map((s, i) => (
                        <span key={i} className="text-[9px] bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded font-medium">
                          {s.source}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Tools used */}
                  {msg.tools && msg.tools.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {msg.tools.map((t, i) => (
                        <span key={i} className="text-[9px] bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded font-mono">
                          ⚡ {t}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Context-aware Suggested Questions */}
                  {msg.suggestedQuestions && msg.suggestedQuestions.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-100 space-y-1.5">
                      <span className="text-[10px] text-indigo-600 font-semibold flex items-center gap-1">
                        <Sparkles className="w-3 h-3 text-indigo-500" /> Suggested Follow-ups:
                      </span>
                      <div className="flex flex-col gap-1">
                        {msg.suggestedQuestions.map((sq, sqIdx) => (
                          <button
                            key={sqIdx}
                            onClick={() => handleSend(sq)}
                            className="text-[10px] text-left bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-2.5 py-1 rounded-lg border border-indigo-100 transition-all hover:translate-x-0.5 font-medium flex items-center justify-between"
                          >
                            <span>{sq}</span>
                            <span className="text-indigo-400 text-[10px]">→</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                {msg.sender === 'user' && (
                  <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 shrink-0 mt-1">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-2 items-center text-xs text-gray-500 italic">
                <Bot className="w-4 h-4 text-indigo-500 animate-spin" />
                <span>AI Agent reasoning over grounded context...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          <div className="p-2 bg-white border-t border-gray-100 flex gap-1.5 overflow-x-auto">
            {defaultPrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(p)}
                className="text-[10px] whitespace-nowrap bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full border border-indigo-100 transition-colors"
              >
                {p}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <div className="p-3 bg-white border-t border-gray-200 flex gap-2 items-center">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={role === 'doctor' ? 'Ask AI about patient data...' : 'Ask AI about your health...'}
              className="flex-1 border border-gray-300 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !inputMessage.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white p-2 rounded-xl transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
