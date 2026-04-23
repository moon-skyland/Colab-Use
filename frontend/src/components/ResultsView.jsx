import React from 'react'
import axios from 'axios'
import './ResultsView.css'

export default function ResultsView({ videoId, result, apiUrl, onReset }) {
  const [isDownloading, setIsDownloading] = React.useState(false)
  const [downloadError, setDownloadError] = React.useState(null)

  const handleDownload = async () => {
    setIsDownloading(true)
    setDownloadError(null)

    try {
      const response = await axios.get(`${apiUrl}/api/download/${videoId}`, {
        responseType: 'blob',
      })

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `badminton_edited_${videoId}.mp4`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setDownloadError(
        err.response?.data?.detail || err.message || 'Download failed'
      )
    } finally {
      setIsDownloading(false)
    }
  }

  const handleCleanup = async () => {
    try {
      await axios.delete(`${apiUrl}/api/cleanup/${videoId}`)
      onReset()
    } catch (err) {
      console.error('Cleanup failed:', err)
    }
  }

  return (
    <div className="results-container">
      <div className="results-card">
        <div className="results-header">
          <h2>✅ Processing Complete</h2>
        </div>

        <div className="results-summary">
          <div className="summary-item">
            <span className="summary-label">Rally Segments:</span>
            <span className="summary-value">{result.segment_count}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Original Frames:</span>
            <span className="summary-value">{result.original_frames}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Status:</span>
            <span className="summary-value">Success</span>
          </div>
        </div>

        <div className="intervals-section">
          <h3>Detected Rally Intervals</h3>
          <div className="intervals-list">
            {result.intervals.map((interval, idx) => (
              <div key={idx} className="interval-item">
                <span className="interval-index">{idx + 1}</span>
                <span className="interval-text">
                  Frames {interval[0]} - {interval[1]}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="actions">
          <button
            className="btn btn-primary"
            onClick={handleDownload}
            disabled={isDownloading}
          >
            {isDownloading ? 'Downloading...' : '⬇️ Download Edited Video'}
          </button>
          <button className="btn btn-secondary" onClick={onReset}>
            Process Another Video
          </button>
        </div>

        {downloadError && (
          <div className="error-message">{downloadError}</div>
        )}

        <button className="btn-cleanup" onClick={handleCleanup}>
          Clean Up Files
        </button>
      </div>
    </div>
  )
}
