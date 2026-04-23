import React, { useState } from 'react'
import axios from 'axios'
import './UploadForm.css'

export default function UploadForm({ onUploadSuccess, apiUrl }) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState(null)

  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      uploadFile(files[0])
    }
  }

  const handleFileSelect = (e) => {
    const files = e.target.files
    if (files.length > 0) {
      uploadFile(files[0])
    }
  }

  const uploadFile = async (file) => {
    // Validate file type
    const validTypes = ['video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska']
    if (!validTypes.includes(file.type)) {
      setError('Invalid file type. Please upload a video file (mp4, avi, mov, mkv)')
      return
    }

    setIsUploading(true)
    setError(null)
    setUploadProgress(0)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${apiUrl}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          setUploadProgress(percent)
        },
      })

      setUploadProgress(100)
      onUploadSuccess(response.data)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          'Upload failed. Please try again.'
      )
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="upload-container">
      <h2>Upload Your Badminton Video</h2>

      <div
        className={`upload-area ${isDragging ? 'dragging' : ''}`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isUploading ? (
          <div>
            <p>Uploading...</p>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="progress-text">{uploadProgress}%</p>
          </div>
        ) : (
          <div>
            <p className="upload-icon">📹</p>
            <p className="upload-text">
              Drag and drop your video here, or click to select
            </p>
            <p className="upload-hint">Supported: MP4, AVI, MOV, MKV</p>
            <label className="file-input-label">
              Select Video
              <input
                type="file"
                accept="video/*"
                onChange={handleFileSelect}
                disabled={isUploading}
              />
            </label>
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
    </div>
  )
}
