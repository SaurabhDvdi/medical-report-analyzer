import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Bell,
  Check,
  X,
  Clock,
  User,
  Loader2,
  AlertCircle,
  Inbox,
  ShieldCheck,
} from 'lucide-react'
import {
  getDoctorNotifications,
  getDoctorNotificationCount,
  markDoctorNotificationsRead,
  acceptDoctorAccessRequest,
  rejectDoctorAccessRequest,
} from '../services/userService'

export default function DoctorNotificationBell() {
  const [isOpen, setIsOpen] = useState(false)
  const [actionError, setActionError] = useState(null)
  const [activeAction, setActiveAction] = useState({}) // { [requestId]: 'accept' | 'reject' }
  const panelRef = useRef(null)
  const queryClient = useQueryClient()

  // 1. Unread count query - lightweight background polling every 15 seconds
  const { data: countData = { count: 0, unread_count: 0 } } = useQuery({
    queryKey: ['doctor-notification-count'],
    queryFn: getDoctorNotificationCount,
    refetchInterval: 15000,
    staleTime: 5000,
  })

  // 2. Notifications list query
  const {
    data: notifications = [],
    isLoading: loadingNotifications,
    isError: errorNotifications,
    refetch: refetchNotifications,
  } = useQuery({
    queryKey: ['doctor-notifications'],
    queryFn: getDoctorNotifications,
    refetchInterval: isOpen ? 10000 : 30000,
    staleTime: 5000,
  })

  // 3. Mark read mutation
  const markReadMutation = useMutation({
    mutationFn: markDoctorNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor-notification-count'] })
    },
  })

  // 4. Accept access request mutation
  const acceptMutation = useMutation({
    mutationFn: (requestId) => acceptDoctorAccessRequest(requestId),
    onMutate: (requestId) => {
      setActionError(null)
      setActiveAction((prev) => ({ ...prev, [requestId]: 'accept' }))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor-notifications'] })
      queryClient.invalidateQueries({ queryKey: ['doctor-notification-count'] })
      queryClient.invalidateQueries({ queryKey: ['patient-access-requests'] })
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      queryClient.invalidateQueries({ queryKey: ['doctor-statistics'] })
      queryClient.invalidateQueries({ queryKey: ['assignment-stats'] })
    },
    onError: () => {
      setActionError('Unable to accept access request. Please try again.')
    },
    onSettled: (data, error, requestId) => {
      setActiveAction((prev) => {
        const next = { ...prev }
        delete next[requestId]
        return next
      })
    },
  })

  // 5. Reject access request mutation
  const rejectMutation = useMutation({
    mutationFn: (requestId) => rejectDoctorAccessRequest(requestId),
    onMutate: (requestId) => {
      setActionError(null)
      setActiveAction((prev) => ({ ...prev, [requestId]: 'reject' }))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor-notifications'] })
      queryClient.invalidateQueries({ queryKey: ['doctor-notification-count'] })
      queryClient.invalidateQueries({ queryKey: ['patient-access-requests'] })
      queryClient.invalidateQueries({ queryKey: ['assignment-stats'] })
    },
    onError: () => {
      setActionError('Unable to reject access request. Please try again.')
    },
    onSettled: (data, error, requestId) => {
      setActiveAction((prev) => {
        const next = { ...prev }
        delete next[requestId]
        return next
      })
    },
  })

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (panelRef.current && !panelRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // Handle bell click
  const handleToggle = () => {
    const nextState = !isOpen
    setIsOpen(nextState)
    setActionError(null)
    if (nextState) {
      refetchNotifications()
      if (countData?.unread_count > 0) {
        markReadMutation.mutate()
      }
    }
  }

  // Pending access requests to display
  const pendingNotifications = notifications.filter(
    (n) => n.status === 'pending'
  )

  // Badge count: pending access requests count
  const badgeCount = countData?.count ?? pendingNotifications.length

  const formatTimestamp = (isoString) => {
    if (!isoString) return 'Just now'
    try {
      const date = new Date(isoString)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins}m ago`
      const diffHours = Math.floor(diffMins / 60)
      if (diffHours < 24) return `${diffHours}h ago`
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return 'Recently'
    }
  }

  return (
    <div className="relative inline-block text-left" ref={panelRef}>
      {/* Bell Button */}
      <button
        type="button"
        id="doctor-notification-bell-btn"
        aria-label="Doctor Notifications"
        onClick={handleToggle}
        className={`relative p-2 rounded-xl transition-all duration-200 border ${
          isOpen
            ? 'bg-teal-50 border-teal-300 text-teal-700 shadow-sm'
            : 'bg-white hover:bg-slate-100 border-slate-200 text-slate-600 hover:text-slate-900'
        }`}
      >
        <Bell className="w-4 h-4 sm:w-4.5 sm:h-4.5" />

        {/* Badge: Displayed only when count > 0 */}
        {badgeCount > 0 && (
          <span
            id="doctor-notification-badge"
            className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-rose-600 text-white text-[10px] font-bold rounded-full flex items-center justify-center border-2 border-white shadow-sm animate-in fade-in zoom-in duration-150"
          >
            {badgeCount > 9 ? '9+' : badgeCount}
          </span>
        )}
      </button>

      {/* Popover / Panel */}
      {isOpen && (
        <div
          id="doctor-notification-panel"
          className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 overflow-hidden transform transition-all duration-200 animate-in fade-in slide-in-from-top-2"
        >
          {/* Panel Header */}
          <div className="px-4 py-3.5 bg-gradient-to-r from-slate-900 to-slate-800 text-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-teal-400" />
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  Notifications
                </h3>
                <p className="text-[11px] text-teal-300 font-medium">
                  Patient Access Requests
                </p>
              </div>
            </div>
            {pendingNotifications.length > 0 && (
              <span className="text-[10px] font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30 px-2 py-0.5 rounded-full">
                {pendingNotifications.length} Pending
              </span>
            )}
          </div>

          {/* Action Error Alert */}
          {actionError && (
            <div className="mx-3 mt-3 p-2.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span className="flex-1">{actionError}</span>
              <button
                type="button"
                onClick={() => setActionError(null)}
                className="text-rose-500 hover:text-rose-700 p-0.5"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Content Area */}
          <div className="max-h-[380px] overflow-y-auto divide-y divide-slate-100 p-2 space-y-2">
            {/* Loading State */}
            {loadingNotifications && (
              <div className="py-10 flex flex-col items-center justify-center text-slate-400 gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-teal-600" />
                <p className="text-xs font-medium">Loading notifications...</p>
              </div>
            )}

            {/* Error State */}
            {!loadingNotifications && errorNotifications && (
              <div className="py-8 px-4 text-center">
                <AlertCircle className="w-6 h-6 text-rose-500 mx-auto mb-2" />
                <p className="text-xs font-bold text-slate-800">
                  Unable to load notifications.
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5 mb-3">
                  Please try again.
                </p>
                <button
                  type="button"
                  onClick={() => refetchNotifications()}
                  className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Empty State */}
            {!loadingNotifications &&
              !errorNotifications &&
              pendingNotifications.length === 0 && (
                <div className="py-10 px-4 text-center">
                  <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 mx-auto mb-2.5 flex items-center justify-center">
                    <Inbox className="w-5 h-5" />
                  </div>
                  <p className="text-xs font-semibold text-slate-800">
                    No new notifications
                  </p>
                  <p className="text-[11px] text-slate-400 mt-1 max-w-[220px] mx-auto">
                    Patient access requests requiring your review will appear here.
                  </p>
                </div>
              )}

            {/* Notification Cards */}
            {!loadingNotifications &&
              !errorNotifications &&
              pendingNotifications.map((notif) => {
                const reqId = notif.access_request_id
                const isAccepting = activeAction[reqId] === 'accept'
                const isRejecting = activeAction[reqId] === 'reject'
                const isBusy = isAccepting || isRejecting

                return (
                  <div
                    key={notif.id}
                    className="p-3.5 bg-slate-50/70 hover:bg-slate-50 rounded-xl border border-slate-200/80 transition-colors space-y-2.5"
                  >
                    {/* Header: Patient Name & Age */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-teal-100 text-teal-800 font-bold flex items-center justify-center text-xs shrink-0">
                          <User className="w-3.5 h-3.5" />
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 leading-tight">
                            {notif.patient_name || 'Patient'}
                          </h4>
                          <p className="text-[11px] text-slate-500 font-medium">
                            {notif.patient_age !== null && notif.patient_age !== undefined
                              ? `Age: ${notif.patient_age}`
                              : 'Age: Not recorded'}
                          </p>
                        </div>
                      </div>

                      <span className="text-[10px] text-slate-400 flex items-center gap-1 shrink-0">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {formatTimestamp(notif.created_at)}
                      </span>
                    </div>

                    {/* Access Request Message */}
                    <p className="text-xs text-slate-600 bg-white p-2.5 rounded-lg border border-slate-100 leading-relaxed">
                      {notif.message ||
                        'Requested access to their medical profile and reports.'}
                    </p>

                    {/* Action Controls */}
                    <div className="flex items-center justify-end gap-2 pt-1">
                      <button
                        type="button"
                        id={`reject-btn-${reqId}`}
                        disabled={isBusy}
                        onClick={() => rejectMutation.mutate(reqId)}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                      >
                        {isRejecting ? (
                          <Loader2 className="w-3 h-3 animate-spin text-rose-600" />
                        ) : (
                          <X className="w-3 h-3 text-slate-400" />
                        )}
                        <span>Reject</span>
                      </button>

                      <button
                        type="button"
                        id={`accept-btn-${reqId}`}
                        disabled={isBusy}
                        onClick={() => acceptMutation.mutate(reqId)}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
                      >
                        {isAccepting ? (
                          <Loader2 className="w-3 h-3 animate-spin text-white" />
                        ) : (
                          <Check className="w-3 h-3 text-white" />
                        )}
                        <span>Accept</span>
                      </button>
                    </div>
                  </div>
                )
              })}
          </div>

          {/* Footer */}
          <div className="px-3 py-2 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span className="flex items-center gap-1 text-slate-400">
              <ShieldCheck className="w-3 h-3 text-emerald-600" /> RBAC &amp; Privacy Protected
            </span>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="text-slate-500 hover:text-slate-800 font-semibold"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
