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
  RotateCcw,
  Trash2,
  ArrowRight
} from 'lucide-react'
import { askAIChat, streamAIChat, clearAIChat } from '../services/aiService'

export default function AIAssistantModal({
  patientId = null,
  activePatientId = null,
  patientName = null,
  role = 'patient'
}) {
  const isDoctor = role === 'doctor'
  const currentPatientId = activePatientId !== null ? activePatientId : patientId

  // Derive stable scoped context key for conversation isolation
  const contextKey = isDoctor
    ? (currentPatientId ? `doctor_pt_${currentPatientId}` : 'doctor_general')
    : 'patient_self'

  const getInitialGreeting = () => {
    if (isDoctor) {
      return `Hello Doctor. I am your AI Clinical Assistant for ${patientName || 'this patient'}. How can I assist with clinical history, report comparisons, or lab trends?`
    }
    return "Hello! I'm your AI Health Assistant. I can help you understand your reports, track lab trends, and clarify medical terms. What would you like to know?"
  }

  // Conversation storage dictionary per contextKey to enforce strict isolation between patients
  const [conversations, setConversations] = useState(() => ({
    [contextKey]: [
      {
        sender: 'assistant',
        text: getInitialGreeting(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: [],
        tools: []
      }
    ]
  }))

  const [messages, setMessages] = useState(() => conversations[contextKey] || [
    {
      sender: 'assistant',
      text: getInitialGreeting(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      sources: [],
      tools: []
    }
  ])

  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const messagesEndRef = useRef(null)
  const activeKeyRef = useRef(contextKey)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (isOpen) {
      scrollToBottom()
    }
  }, [messages, isOpen])

  // Context Switch Handler: When doctor switches from Patient A to Patient B
  useEffect(() => {
    if (activeKeyRef.current !== contextKey) {
      activeKeyRef.current = contextKey
      const existing = conversations[contextKey]
      if (existing && existing.length > 0) {
        setMessages(existing)
      } else {
        const fresh = [
          {
            sender: 'assistant',
            text: getInitialGreeting(),
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            sources: [],
            tools: []
          }
        ]
        setMessages(fresh)
        setConversations((prev) => ({
          ...prev,
          [contextKey]: fresh
        }))
      }
    }
  }, [contextKey, currentPatientId, patientName])

  // Keep conversations cache synchronized with active message list
  const updateActiveMessages = (newMessages) => {
    setMessages(newMessages)
    setConversations((prev) => ({
      ...prev,
      [contextKey]: typeof newMessages === 'function' ? newMessages(prev[contextKey] || []) : newMessages
    }))
  }

  const handleSend = async (textToSend = null) => {
    const query = textToSend || inputMessage
    if (!query.trim() || loading) return

    const now = new Date()
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    const userMsg = { sender: 'user', text: query, timestamp: timeStr }
    if (!textToSend) setInputMessage('')
    setLoading(true)

    const respTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    // Build bounded conversation history strictly from current patient context
    const currentHistory = messages
      .filter((m) => m.text && !m.isError && m.text !== getInitialGreeting())
      .slice(-4)
      .map((m) => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text
      }))

    // Progressive placeholder for streaming rendering
    const placeholderMsg = {
      sender: 'assistant',
      text: '',
      timestamp: respTime,
      sources: [],
      tools: [],
      suggestedQuestions: [],
      isEmergency: false,
      emergencyNotice: null
    }

    const updatedWithUserAndPlaceholder = [...messages, userMsg, placeholderMsg]
    updateActiveMessages(updatedWithUserAndPlaceholder)

    try {
      const payload = {
        message: query,
        patient_id: currentPatientId,
        active_patient_id: currentPatientId,
        conversation_history: currentHistory
      }

      await streamAIChat(payload, {
        onMetadata: (data) => {
          setLoading(false)
          updateActiveMessages((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last && last.sender === 'assistant') {
              last.isEmergency = Boolean(data.is_emergency)
              last.emergencyNotice = data.emergency_notice
              last.tools = data.tools_used || []
              last.sources = data.sources || []
            }
            return next
          })
        },
        onToken: (token) => {
          setLoading(false)
          updateActiveMessages((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last && last.sender === 'assistant') {
              last.text += token
            }
            return next
          })
        },
        onComplete: (data) => {
          setLoading(false)
          updateActiveMessages((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last && last.sender === 'assistant') {
              if (data.answer) last.text = data.answer
              last.suggestedQuestions = data.suggested_questions || []
              if (data.sources) last.sources = data.sources
              if (data.tools_used) last.tools = data.tools_used
              if (data.is_emergency !== undefined) last.isEmergency = Boolean(data.is_emergency)
              if (data.emergency_notice) last.emergencyNotice = data.emergency_notice
            }
            return next
          })
        },
        onError: (err) => {
          console.error('Stream error:', err)
          setLoading(false)
          updateActiveMessages((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last && last.sender === 'assistant') {
              last.text = 'Sorry, I encountered an issue retrieving that information. Please try again or inspect standard reports.'
              last.isError = true
            }
            return next
          })
        }
      })
    } catch (err) {
      setLoading(false)
      updateActiveMessages((prev) => {
        const next = [...prev]
        const last = next[next.length - 1]
        if (last && last.sender === 'assistant') {
          last.text = 'Sorry, I encountered an issue retrieving that information. Please try again or inspect standard reports.'
          last.isError = true
        }
        return next
      })
    } finally {
      setLoading(false)
    }
  }

  // Clear Chat execution: Clears ONLY AI conversation context; medical records remain intact
  const handleConfirmClearChat = async () => {
    setShowClearConfirm(false)
    const freshGreeting = [
      {
        sender: 'assistant',
        text: getInitialGreeting(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: [],
        tools: []
      }
    ]
    setMessages(freshGreeting)
    setConversations((prev) => ({
      ...prev,
      [contextKey]: freshGreeting
    }))

    try {
      await clearAIChat({
        patient_id: currentPatientId,
        active_patient_id: currentPatientId
      })
    } catch (err) {
      console.warn('Backend clear chat sync note:', err)
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
        <div className="relative bg-white rounded-2xl shadow-2xl border border-slate-200/90 w-[calc(100vw-2rem)] sm:w-[460px] h-[580px] sm:h-[620px] max-h-[85vh] flex flex-col overflow-hidden transition-all duration-200">
          {/* Header with Visual Context & Clear Chat Control */}
          <div className="bg-white border-b border-slate-200/80 p-3.5 sm:px-5 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-[#0F766E] text-white flex items-center justify-center shrink-0 shadow-xs">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-slate-900 tracking-tight leading-snug">
                  AI Assistant
                </h3>
                <p className="text-xs text-slate-500 font-medium">
                  {isDoctor
                    ? (patientName ? `Patient: ${patientName}` : 'Context: Patient Workspace')
                    : 'Your Health Information'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setShowClearConfirm(true)}
                title="Clear Conversation"
                aria-label="Clear Conversation"
                className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:text-rose-700 hover:bg-rose-50 rounded-lg border border-slate-200 hover:border-rose-200 transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5 text-slate-500 hover:text-rose-600" />
                <span className="hidden sm:inline">Clear Chat</span>
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                aria-label="Close Assistant"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Clear Chat Confirmation Modal */}
          {showClearConfirm && (
            <div className="absolute inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
              <div className="bg-white rounded-2xl p-5 max-w-xs w-full shadow-2xl border border-slate-200 space-y-4 animate-in fade-in zoom-in-95 duration-150">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center shrink-0">
                    <Trash2 className="w-4 h-4" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="font-bold text-sm text-slate-900">Clear this conversation?</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      This only clears the AI conversation. Your medical records will not be deleted.
                    </p>
                  </div>
                </div>
                <div className="flex items-center justify-end gap-2 pt-1 border-t border-slate-100">
                  <button
                    onClick={() => setShowClearConfirm(false)}
                    className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmClearChat}
                    className="px-3.5 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-lg shadow-xs transition-colors cursor-pointer"
                  >
                    Clear Chat
                  </button>
                </div>
              </div>
            </div>
          )}

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
                        : msg.isEmergency
                        ? 'bg-amber-50/95 text-amber-950 border border-amber-300 rounded-tl-xs'
                        : msg.isError
                        ? 'bg-rose-50 text-rose-800 border border-rose-200/90 rounded-tl-xs'
                        : 'bg-white text-slate-800 border border-slate-200/90 rounded-tl-xs'
                    }`}
                  >
                    {msg.isEmergency && (
                      <div className="mb-2.5 pb-2 border-b border-amber-200/80 flex items-center gap-1.5 text-amber-800 font-semibold text-[11px]">
                        <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        <span>Clinical Triage Notice</span>
                      </div>
                    )}
                    <p className="whitespace-pre-wrap">
                      {msg.text || (msg.sender === 'assistant' && !msg.isEmergency && !msg.isError ? (
                        <span className="inline-flex items-center gap-1 text-slate-400">
                          <span className="inline-block w-1.5 h-3 bg-teal-600 animate-pulse rounded-xs" />
                          <span className="text-[11px]">Thinking...</span>
                        </span>
                      ) : '')}
                    </p>

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

                    {/* Tools used (auditability for clinician) */}
                    {isDoctor && msg.tools && msg.tools.length > 0 && (
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

            {/* Interactive Prompt Chips */}
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
