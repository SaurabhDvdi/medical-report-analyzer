import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import { Link, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import { getReports } from '../services/reportService'
import { useAuth } from '../contexts/AuthContext'
import {
  Upload,
  FileText,
  Trash2,
  Download,
  Loader,
  FileDown,
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  X,
  Filter,
  ArrowUpRight
} from 'lucide-react'
import { TableSkeleton } from '../components/Skeletons'

export async function downloadLabValuesCsv() {
  const response = await api.get('/api/export/csv', { responseType: 'blob' })
  const blob =
    response.data instanceof Blob ? response.data : new Blob([response.data], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'lab_values.csv'
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export default function Reports() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [categoryFilter, setCategoryFilter] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadError, setUploadError] = useState(null)
  const [exporting, setExporting] = useState(false)

  // Redirect doctors away from reports page
  if (user?.role === 'doctor') {
    navigate('/dashboard')
  }

  // Reports Query with conditional refetchInterval OCR polling
  const { data: reports = [], isLoading: loading, error: reportsError } = useQuery({
    queryKey: ['reports'],
    queryFn: getReports,
    staleTime: 2 * 60 * 1000,
    refetchInterval: (query) => {
      const data = query.state.data
      if (Array.isArray(data) && data.some((r) => r.ocr_status === 'pending' || r.ocr_status === 'processing' || r.ocr_status === 'validating')) {
        return 3000
      }
      return false
    },
  })

  // Report Categories Query
  const { data: categories = [], isLoading: categoriesLoading } = useQuery({
    queryKey: ['report-categories'],
    queryFn: () => api.get('/api/report-categories').then((res) => res.data),
    staleTime: 30 * 60 * 1000,
  })

  const listError = reportsError ? (reportsError.response?.data?.detail || 'Failed to load reports.') : ''

  // Delete Report Mutation
  const deleteMutation = useMutation({
    mutationFn: (reportId) => api.delete(`/api/reports/${reportId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['reports-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: (err) => {
      alert(err.response?.data?.detail || 'Error deleting report. Please try again.')
    }
  })

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0 || uploading) return

    const file = acceptedFiles[0]
    setUploading(true)
    setUploadProgress(0)
    setUploadError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      await api.post('/api/reports/upload', formData, {
        onUploadProgress: (progressEvent) => {
          const total = progressEvent.total || 1
          const percentCompleted = Math.round((progressEvent.loaded * 100) / total)
          setUploadProgress(percentCompleted)
        },
      })

      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['reports-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    } catch (error) {
      console.error('Error uploading file:', error)
      const errorDetail = error.response?.data?.detail
      const errorCode = error.response?.data?.code

      if (error.response?.status === 422 || errorCode === 'NON_MEDICAL_DOCUMENT') {
        setUploadError({
          title: 'Document Rejected',
          message: errorDetail || 'This file does not appear to be a medical report. Please upload a valid laboratory, diagnostic, prescription, or clinical report.'
        })
      } else {
        setUploadError({
          title: 'Upload Failed',
          message: errorDetail || 'Error uploading file. Please try again.'
        })
      }
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }, [queryClient, uploading])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: uploading,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
  })

  const handleDelete = (reportId) => {
    if (!window.confirm('Are you sure you want to delete this report?')) {
      return
    }
    deleteMutation.mutate(reportId)
  }

  const handleDownload = async (reportId, fileName) => {
    try {
      const response = await api.get(`/api/reports/${reportId}/download`, {
        responseType: 'blob',
      })
      const blob =
        response.data instanceof Blob
          ? response.data
          : new Blob([response.data])
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading report:', error)
      alert(
        error.response?.data?.detail || 'Error downloading report. Please try again.'
      )
    }
  }

  const handleExportCsv = async () => {
    setExporting(true)
    try {
      await downloadLabValuesCsv()
    } catch (error) {
      console.error('CSV export failed:', error)
      alert(
        error.response?.data?.detail || 'Could not export CSV. Please try again.'
      )
    } finally {
      setExporting(false)
    }
  }

  const filteredReports = categoryFilter
    ? reports.filter((r) => (r.category || '') === categoryFilter)
    : reports

  if (loading) {
    return <TableSkeleton rows={6} />
  }

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Medical Reports</h1>
          <p className="text-xs text-slate-500 mt-1">
            Upload PDF or image lab reports to run automated OCR, parameter extraction, and AI clinical summaries.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Category Filter */}
          <div className="flex items-center gap-2 bg-white px-3 py-1.5 border border-slate-300 rounded-lg text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              className="bg-transparent text-slate-700 font-medium focus:outline-none"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              disabled={categoriesLoading}
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Export CSV */}
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={exporting}
            className="clinical-button-secondary text-xs"
          >
            {exporting ? (
              <Loader className="w-3.5 h-3.5 mr-2 animate-spin" />
            ) : (
              <FileDown className="w-3.5 h-3.5 mr-2 text-slate-500" />
            )}
            Export Lab Data CSV
          </button>
        </div>
      </div>

      {listError && (
        <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 text-xs text-rose-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{listError}</span>
        </div>
      )}

      {uploadError && (
        <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 text-xs text-rose-800 flex items-start justify-between gap-3 shadow-sm">
          <div className="flex items-start gap-2.5">
            <XCircle className="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
            <div>
              <p className="font-bold text-rose-900 text-sm">{uploadError.title}</p>
              <p className="text-rose-700 mt-0.5 leading-relaxed">{uploadError.message}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setUploadError(null)}
            className="text-rose-500 hover:text-rose-800 p-1 rounded-lg hover:bg-rose-100 transition-colors shrink-0"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Upload Dropzone */}
      <div
        {...getRootProps()}
        className={`clinical-card p-8 sm:p-10 text-center border-2 border-dashed transition-all cursor-pointer ${
          isDragActive
            ? 'border-teal-500 bg-teal-50/60 scale-[1.005]'
            : 'border-slate-300 hover:border-teal-500 hover:bg-slate-50/50'
        } ${uploading ? 'opacity-60 pointer-events-none' : ''}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="space-y-3">
            <Loader className="w-10 h-10 mx-auto text-teal-600 animate-spin" />
            <p className="text-xs font-bold text-slate-700">Uploading & Analyzing Document... {uploadProgress}%</p>
            <div className="w-48 mx-auto bg-slate-200 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-teal-600 h-full transition-all duration-200"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-100 text-teal-600 flex items-center justify-center mx-auto">
              <Upload className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">
                {isDragActive ? 'Drop your report file here' : 'Click or Drag & Drop Medical Report'}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Supports PDF, PNG, JPG, or JPEG formats up to 20MB
              </p>
            </div>
            <div className="pt-2 flex items-center justify-center gap-4 text-[11px] text-slate-400">
              <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-emerald-500" /> Fast Document Inspection</span>
              <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-emerald-500" /> Auto Extraction</span>
              <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-emerald-500" /> Clinical AI Summary</span>
            </div>
          </div>
        )}
      </div>

      {/* Reports Table List */}
      <div className="clinical-card overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <h3 className="font-bold text-slate-900 text-sm">
            All Uploaded Documents ({filteredReports.length})
          </h3>
          {categoryFilter && (
            <button
              onClick={() => setCategoryFilter('')}
              className="text-xs text-teal-700 font-semibold hover:underline"
            >
              Clear Filter
            </button>
          )}
        </div>

        <div className="divide-y divide-slate-100">
          {filteredReports.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <FileText className="w-10 h-10 text-slate-300 mx-auto" />
              <p className="text-sm font-medium text-slate-600">
                {reports.length === 0 ? 'No medical reports uploaded yet.' : 'No reports found for selected category.'}
              </p>
              <p className="text-xs text-slate-400">
                {reports.length === 0 ? 'Upload your first PDF or image report above.' : 'Try selecting a different filter.'}
              </p>
            </div>
          ) : (
            filteredReports.map((report) => (
              <div
                key={report.id}
                className="p-4 sm:p-5 flex items-center justify-between gap-4 hover:bg-slate-50/80 transition-colors group"
              >
                <Link
                  to={`/reports/${report.id}`}
                  className="flex-1 flex items-start gap-3.5 min-w-0"
                >
                  <div className="p-2.5 bg-slate-100 text-slate-700 rounded-xl group-hover:bg-teal-50 group-hover:text-teal-700 transition-colors shrink-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="space-y-1 min-w-0">
                    <p className="text-sm font-bold text-slate-900 group-hover:text-teal-700 transition-colors truncate flex items-center gap-1.5">
                      <span>{report.file_name}</span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-600" />
                    </p>
                    <p className="text-xs text-slate-500 flex flex-wrap items-center gap-2">
                      <span>{new Date(report.upload_date).toLocaleDateString()}</span>
                      <span>·</span>
                      <span className="font-medium text-slate-700">{report.category || 'Uncategorized'}</span>
                    </p>
                    {report.ai_summary && (
                      <p className="text-xs text-slate-600 line-clamp-1 italic">
                        &quot;{report.ai_summary}&quot;
                      </p>
                    )}
                  </div>
                </Link>

                <div className="flex items-center gap-3 shrink-0">
                  <span
                    className={
                      report.ocr_status === 'completed'
                        ? 'clinical-badge-normal'
                        : report.ocr_status === 'failed' || report.ocr_status === 'rejected_non_medical'
                        ? 'clinical-badge-high'
                        : 'clinical-badge-low'
                    }
                  >
                    {report.ocr_status === 'completed' && <CheckCircle2 className="w-3 h-3 mr-1" />}
                    {report.ocr_status === 'rejected_non_medical' && <XCircle className="w-3 h-3 mr-1" />}
                    {report.ocr_status === 'failed' && <XCircle className="w-3 h-3 mr-1" />}
                    {(report.ocr_status === 'processing' || report.ocr_status === 'pending' || report.ocr_status === 'validating') && (
                      <Clock className="w-3 h-3 mr-1 animate-spin" />
                    )}
                    {report.ocr_status === 'rejected_non_medical'
                      ? 'Rejected (Non-Medical)'
                      : report.ocr_status === 'validating'
                      ? 'Validating...'
                      : report.ocr_status === 'processing'
                      ? 'Processing...'
                      : report.ocr_status}
                  </span>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault()
                      handleDownload(report.id, report.file_name)
                    }}
                    className="p-2 text-slate-400 hover:text-teal-600 hover:bg-slate-100 rounded-lg transition-colors"
                    title="Download Report"
                  >
                    <Download className="w-4 h-4" />
                  </button>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault()
                      handleDelete(report.id)
                    }}
                    className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                    title="Delete Report"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
