import React, { useMemo, useState } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'

function App() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [jobId, setJobId] = useState('')
  const [uploadPath, setUploadPath] = useState('')
  const [statusText, setStatusText] = useState('Select a video file to begin.')
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [editedVideoUrl, setEditedVideoUrl] = useState('')
  const [editInstructionUrl, setEditInstructionUrl] = useState('')
  const [timelineUrl, setTimelineUrl] = useState('')
  const [error, setError] = useState('')

  const originalVideoUrl = useMemo(() => {
    if (!uploadPath) return ''
    const filename = uploadPath.split('/').pop()
    return filename ? `${API_BASE}/uploads/${filename}` : ''
  }, [uploadPath])

  const handleFileChange = (event) => {
    const file = event.target.files?.[0] ?? null
    setSelectedFile(file)
    setError('')
    if (file) {
      setStatusText(`Selected: ${file.name}`)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a video file first.')
      return
    }
    setIsUploading(true)
    setError('')
    setStatusText('Uploading video...')
    setEditedVideoUrl('')
    setEditInstructionUrl('')
    setTimelineUrl('')

    const formData = new FormData()
    formData.append('video', selectedFile)

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || 'Upload failed.')
      }
      setJobId(payload.job_id)
      setUploadPath(payload.video_path)
      setStatusText('Upload successful. Click Process to continue.')
    } catch (err) {
      setError(err.message || 'Upload failed.')
      setStatusText('Upload failed.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleProcess = async () => {
    if (!jobId) {
      setError('Upload a video first.')
      return
    }
    setIsProcessing(true)
    setError('')
    setStatusText('Processing video...')

    try {
      const response = await fetch(`${API_BASE}/process/${jobId}`, {
        method: 'POST',
      })
      const payload = await response.json()
      if (!response.ok || payload.status !== 'success') {
        throw new Error(payload.error || payload.detail || 'Processing failed.')
      }
      setEditedVideoUrl(`${API_BASE}${payload.edited_video_url}`)
      setEditInstructionUrl(`${API_BASE}${payload.edit_instruction_url}`)
      setTimelineUrl(`${API_BASE}${payload.state_timeline_url}`)
      setStatusText('Processing complete.')
    } catch (err) {
      setError(err.message || 'Processing failed.')
      setStatusText('Processing failed.')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="app-container">
      <div className="card">
        <h1>Badminton AI Editor</h1>
        <p className="subtitle">Upload, process, preview, and download</p>

        <div className="controls">
          <input type="file" accept="video/*" onChange={handleFileChange} />
          <div className="button-row">
            <button onClick={handleUpload} disabled={isUploading}>
              {isUploading ? 'Uploading...' : 'Upload'}
            </button>
            <button onClick={handleProcess} disabled={isProcessing || !jobId}>
              {isProcessing ? 'Processing...' : 'Process'}
            </button>
          </div>
        </div>

        <p className="status">{statusText}</p>
        {error && <p className="error">{error}</p>}

        <div className="media-grid">
          <div>
            <h3>Original Video</h3>
            {originalVideoUrl ? (
              <video controls src={originalVideoUrl} className="video" />
            ) : (
              <p className="muted">No uploaded video preview yet.</p>
            )}
          </div>

          <div>
            <h3>Edited Video</h3>
            {editedVideoUrl ? (
              <>
                <video controls src={editedVideoUrl} className="video" />
                <a href={editedVideoUrl} download className="download-link">
                  Download edited video
                </a>
              </>
            ) : (
              <p className="muted">No edited video yet.</p>
            )}
          </div>
        </div>

        <div className="links">
          <h3>Artifacts</h3>
          <p>
            Edit instruction:{' '}
            {editInstructionUrl ? (
              <a href={editInstructionUrl} target="_blank" rel="noreferrer">
                {editInstructionUrl}
              </a>
            ) : (
              <span className="muted">Not available yet</span>
            )}
          </p>
          <p>
            State timeline:{' '}
            {timelineUrl ? (
              <a href={timelineUrl} target="_blank" rel="noreferrer">
                {timelineUrl}
              </a>
            ) : (
              <span className="muted">Not available yet</span>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
