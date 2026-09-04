import React, { useState, useRef, useEffect } from 'react'
import {
  Bot,
  User,
  Send,
  MessageSquare,
  FileText,
  TrendingUp,
  Droplet,
  BarChart2,
  ShieldAlert,
  X,
  Activity,
  Brain,
  ArrowRight
} from 'lucide-react'
import { askAIChat } from '../services/aiService'

export default function AIAssistantModal({ patientId = null, patientName = null, role = 'patient' }) {
  const isDoctor = role === 'doctor'

  const initialGreeting = isDoctor
    ? `Hello Doctor. I am your AI Clinical Assistant for ${patientName ? patientName : 'this patient'}. How can I assist with clinical history, report comparisons, or lab trends?`
    : "Hello! I'm your AI Health Assistant. I can help you understand your reports, track lab trends, and clarify medical terms. What would you like to know?"

  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: initialGreeting,
      timestamp: '10:24 AM',
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
    if (isOpen) {
      scrollToBottom()
    }
  }, [messages, isOpen])

  const handleSend = async (textToSend = null) => {
    const query = textToSend || inputMessage
    if (!query.trim() || loading) return

    const now = new Date()
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    const userMsg = { sender: 'user', text: query, timestamp: timeStr }
    setMessages((prev) => [...prev, userMsg])
    if (!textToSend) setInputMessage('')
    setLoading(true)

    try {
      const payload = {
        message: query,
        patient_id: patientId
      }
      const data = await askAIChat(payload)

      const respTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: data.answer,
          timestamp: respTime,
          sources: data.sources || [],
          tools: data.tools_used || [],
          suggestedQuestions: data.suggested_questions || []
        }
      ])
    } catch (err) {
      const respTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'Sorry, I encountered an issue retrieving that information. Please try again or inspect standard reports.',
          timestamp: respTime,
          isError: true
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const patientInteractivePrompts = [
    { icon: FileText, text: 'Explain my latest lab report' },
    { icon: TrendingUp, text: 'How has my HbA1c changed over time?' },
    { icon: Droplet, text: 'What does high LDL cholesterol mean?' },
    { icon: BarChart2, text: 'Show me trends in my hemoglobin' }
  ]

  const doctorInteractivePrompts = [
    { icon: FileText, text: 'Summarize patient medical history' },
    { icon: TrendingUp, text: 'Which lab values are abnormal?' },
    { icon: BarChart2, text: 'Show historical trend for HbA1c' },
    { icon: ShieldAlert, text: 'Check for medication warnings' }
  ]

  const promptList = isDoctor ? doctorInteractivePrompts : patientInteractivePrompts

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {!isOpen ? (
        <div className="relative group">
          <button
            onClick={() => setIsOpen(true)}
            title="AI Clinical Assistant"
            aria-label="AI Clinical Assistant"
            className="w-14 h-14 rounded-full bg-[#0F766E] hover:bg-teal-800 text-white flex items-center justify-center shadow-xl hover:shadow-2xl transition-all duration-200 border border-teal-400/20 active:scale-95 cursor-pointer"
          >
            <Bot className="w-7 h-7 text-white" />
          </button>
          <div className="absolute right-0 bottom-full mb-2.5 hidden group-hover:block whitespace-nowrap bg-slate-900 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-lg border border-slate-800 pointer-events-none transition-opacity">
            AI Clinical Assistant
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-2xl border border-slate-200/90 w-[calc(100vw-2rem)] sm:w-[450px] h-[580px] sm:h-[620px] max-h-[85vh] flex flex-col overflow-hidden transition-all duration-200">
          {/* Header (Clean white clinical surface with MedPulse branding) */}
          <div className="bg-white border-b border-slate-200/80 p-4 sm:px-5 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-[#0F766E] text-white flex items-center justify-center shrink-0 shadow-xs">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-slate-900 tracking-tight leading-snug">
                  AI Clinical Assistant
                </h3>
                <p className="text-xs text-slate-500 font-medium">
                  {isDoctor ? `Context: ${patientName || 'Patient Workspace'}` : 'Your health intelligence companion'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
              aria-label="Close Assistant"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Chat Messages Area */}
          <div className="flex-1 p-4 sm:p-5 overflow-y-auto space-y-4 bg-slate-50/60">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-[#0F766E] text-white flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className="max-w-[84%] space-y-1">
                  <div
                    className={`rounded-2xl p-4 text-xs leading-relaxed shadow-2xs ${
                      msg.sender === 'user'
                        ? 'bg-[#0F766E] text-white rounded-tr-xs font-medium'
                        : msg.isError
                        ? 'bg-rose-50 text-rose-800 border border-rose-200/90 rounded-tl-xs'
                        : 'bg-white text-slate-800 border border-slate-200/90 rounded-tl-xs'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.text}</p>

                    {/* Sources metadata */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap gap-1">
                        <span className="text-[10px] text-slate-400 font-semibold flex items-center gap-1">
                          <FileText className="w-3 h-3 text-slate-400" /> Sources:
                        </span>
                        {msg.sources.map((s, i) => (
                          <span key={i} className="text-[9px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium border border-slate-200">
                            {s.source}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Tools used */}
                    {msg.tools && msg.tools.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {msg.tools.map((t, i) => (
                          <span key={i} className="text-[9px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded font-mono border border-emerald-200/60">
                            ⚡ {t}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Context-aware Suggested Questions */}
                    {msg.suggestedQuestions && msg.suggestedQuestions.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-slate-100 space-y-1.5">
                        <span className="text-[10px] text-teal-700 font-semibold flex items-center gap-1">
                          <MessageSquare className="w-3 h-3 text-teal-600" /> Suggested Follow-ups:
                        </span>
                        <div className="flex flex-col gap-1.5">
                          {msg.suggestedQuestions.map((sq, sqIdx) => (
                            <button
                              key={sqIdx}
                              onClick={() => handleSend(sq)}
                              className="text-[11px] text-left bg-teal-50/80 hover:bg-teal-100 text-teal-900 px-3 py-2 rounded-xl border border-teal-200/80 transition-all font-medium flex items-center justify-between"
                            >
                              <span>{sq}</span>
                              <ArrowRight className="w-3 h-3 text-teal-600 shrink-0 ml-1" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Timestamp */}
                  <p className={`text-[10px] font-medium text-slate-400 px-1 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
                    {msg.timestamp || '10:24 AM'}
                  </p>
                </div>

                {msg.sender === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {/* Interactive Prompt Chips rendered right inside chat area for quick start */}
            {messages.length === 1 && (
              <div className="space-y-2 pt-1 pl-11 pr-2">
                {promptList.map((promptItem, pIdx) => {
                  const PromptIcon = promptItem.icon
                  return (
                    <button
                      key={pIdx}
                      onClick={() => handleSend(promptItem.text)}
                      className="w-full text-left bg-white hover:bg-teal-50/80 text-slate-800 hover:text-teal-900 border border-teal-200/80 hover:border-teal-300 rounded-xl px-3.5 py-2.5 text-xs font-semibold flex items-center gap-2.5 shadow-2xs transition-all cursor-pointer"
                    >
                      <PromptIcon className="w-4 h-4 text-[#0F766E] shrink-0" />
                      <span className="flex-1">{promptItem.text}</span>
                    </button>
                  )
                })}
              </div>
            )}

            {loading && (
              <div className="flex gap-2.5 items-center text-xs text-slate-600 font-medium bg-white p-3.5 rounded-2xl border border-slate-200/90 shadow-2xs w-max">
                <Activity className="w-4 h-4 text-[#0F766E] animate-spin shrink-0" />
                <span>AI Clinical Assistant analyzing clinical context...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Input Section */}
          <div className="bg-white border-t border-slate-200/80 p-3.5 sm:px-4 space-y-2 shrink-0">
            <div className="flex gap-2 items-center">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder={isDoctor ? 'Ask AI about patient history...' : 'Ask anything about your health...'}
                className="flex-1 bg-slate-50 border border-slate-200/90 rounded-xl px-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-all"
              />
              <button
                onClick={() => handleSend()}
                disabled={loading || !inputMessage.trim()}
                className="w-9 h-9 bg-[#0F766E] hover:bg-teal-800 disabled:opacity-40 text-white rounded-xl flex items-center justify-center shrink-0 transition-all shadow-xs cursor-pointer"
                aria-label="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>

            {/* Medical Disclaimer */}
            <div className="text-[10px] text-slate-400 text-center flex items-center justify-center gap-1 font-medium pt-0.5">
              <ShieldAlert className="w-3 h-3 text-slate-400 shrink-0" />
              <span>AI responses are for informational purposes only and are not a substitute for medical advice.</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
