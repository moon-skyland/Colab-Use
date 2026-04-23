import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './ProcessingStatus.css'

export default function ProcessingStatus({
  videoId,
  jobId,
  onProcessingComplete,
  apiUrl,
}) {
  const [status, setStatus] = useState('queued')
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [isProcessing, setIsProcessing] = useState(true)

  useEffect(() => {
    if (!jobId) return

    const checkStatus = async () => {
      try {
        const response = await axios.get(`${apiUrl}/api/status/${jobId}`)
        const { status: newStatus, progress: newProgress, error: newError, result: newResult } = response.data

        setStatus(newStatus)
        setProgress(newProgress)
        if (newError) setError(newError)
        if (newResult) setResult(newResult)

        if (newStatus === 'completed') {
          setIsProcessing(false)
          onProcessingComplete(newResult)
        } else if (newStatus === 'failed') {
          setIsProcessing(false)
        }
      } catch (err) {
        setError(err.message)
        setIsProcessing(false)
      }
    }

    const interval = setInterval(checkStatus, 1000)
    return () => clearInterval(interval)
  }, [jobId, apiUrl, onProcessingComplete])

  const getStatusMessage = () => {
    switch (status) {
      case 'queued':
        return 'Queued for processing...'
      case 'detecting':
        return 'Detecting shuttlecock frames...'
      case 'processing':
        return 'Processing and cutting video...'
      case 'completed':
        return 'Processing complete!'
      case 'failed':
        return 'Processing failed'
      default:
        return 'Processing...'
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'detecting':
        return '🔍'
      case 'processing':
        return '✂️'
      case 'completed':
        return '✅'
      case 'failed':
        return '❌'
      default:
        return '⏳'
    }
  }

  return (
    <div className="processing-container">
      <div className="status-card">
        <div className="status-header">
          <span className="status-icon">{getStatusIcon()}</span>
          <h3>{getStatusMessage()}</h3>
        </div>

        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="progress-text">{progress}%</p>

        {error && <div className="error-message">{error}</div>}

        {result && (
          <div className="result-info">
            <p><strong>Rally Segments Found:</strong> {result.segment_count}</p>
            <p><strong>Total Frames:</strong> {result.original_frames}</p>
            <p><strong>Status:</strong> Video successfully processed and cut</p>
          </div>
        )}
      </div>
    </div>
  )
}
