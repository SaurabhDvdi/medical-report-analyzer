import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Link } from 'react-router-dom'
import api from '../utils/api'
import { Upload, FileText, Trash2, Download, Loader } from 'lucide-react'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  useEffect(() => {
    fetchReports()
  }, [])

  const fetchReports = async () => {
    try {
      const response = await api.get('/api/reports')
      setReports(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching reports:', error)
      setLoading(false)
    }
  }

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    setUploading(true)
    setUploadProgress(0)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/api/reports/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          setUploadProgress(percentCompleted)
        },
      })

      // Refresh reports list
      await fetchReports()
      setUploading(false)
      setUploadProgress(0)
    } catch (error) {
      console.error('Error uploading file:', error)
      setUploading(false)
      setUploadProgress(0)
      alert('Error uploading file. Please try again.')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf']
    },
    maxFiles: 1
  })

  const handleDelete = async (reportId) => {
    if (!window.confirm('Are you sure you want to delete this report?')) {
      return
    }

    try {
      await api.delete(`/api/reports/${reportId}`)
      setReports(reports.filter(r => r.id !== reportId))
    } catch (error) {
      console.error('Error deleting report:', error)
      alert('Error deleting report. Please try again.')
    }
  }

  const handleDownload = async (reportId, fileName) => {
    try {
      const response = await api.get(`/api/reports/${reportId}/download`, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Error downloading report:', error)
      alert('Error downloading report. Please try again.')
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading reports...</div>
  }

  return (
    <div className="px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Reports</h1>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div>
            <Loader className="w-12 h-12 mx-auto mb-4 text-blue-500 animate-spin" />
            <p className="text-gray-600">Uploading... {uploadProgress}%</p>
          </div>
        ) : (
          <div>
            <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium text-gray-700 mb-2">
              {isDragActive ? 'Drop the file here' : 'Drag & drop a report file here'}
            </p>
            <p className="text-sm text-gray-500">
              or click to select (PDF, PNG, JPG)
            </p>
          </div>
        )}
      </div>

      {/* Reports List */}
      <div className="mt-8 bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">All Reports</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {reports.length === 0 ? (
            <div className="px-6 py-12 text-center text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>No reports uploaded yet.</p>
              <p className="text-sm mt-2">Upload your first medical report above.</p>
            </div>
          ) : (
            reports.map((report) => (
              <div
                key={report.id}
                className="px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <Link
                    to={`/reports/${report.id}`}
                    className="flex-1 flex items-center space-x-4"
                  >
                    <FileText className="w-8 h-8 text-blue-500" />
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{report.file_name}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(report.upload_date).toLocaleDateString()} • {report.category || 'Uncategorized'}
                      </p>
                      {report.ai_summary && (
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {report.ai_summary}
                        </p>
                      )}
                    </div>
                  </Link>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded ${
                      report.ocr_status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : report.ocr_status === 'processing'
                        ? 'bg-yellow-100 text-yellow-800'
                        : report.ocr_status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {report.ocr_status}
                    </span>
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        handleDownload(report.id, report.file_name)
                      }}
                      className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                      title="Download"
                    >
                      <Download className="w-5 h-5" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        handleDelete(report.id)
                      }}
                      className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

