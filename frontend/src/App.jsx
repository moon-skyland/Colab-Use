import React, { useState } from 'react'
import UploadForm from './components/UploadForm'
import ProcessingStatus from './components/ProcessingStatus'
import ResultsView from './components/ResultsView'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [stage, setStage] = useState('upload') // 'upload', 'processing', 'results'
  const [videoData, setVideoData] = useState(null)
  const [jobData, setJobData] = useState(null)
  const [resultsData, setResultsData] = useState(null)

  const handleUploadSuccess = (data) => {
    setVideoData(data)
    setStage('processing')

    // Automatically start processing
    processVideo(data.video_id)
  }

  const processVideo = async (videoId) => {
    try {
      const response = await fetch(`${API_URL}/api/process?video_id=${videoId}`, {
        method: 'POST',
      })
      const data = await response.json()
      setJobData(data)
    } catch (err) {
      console.error('Error starting processing:', err)
      alert('Failed to start processing. Please try again.')
    }
  }

  const handleProcessingComplete = (result) => {
    setResultsData(result)
    setStage('results')
  }

  const handleReset = () => {
    setStage('upload')
    setVideoData(null)
    setJobData(null)
    setResultsData(null)
  }

  return (
    <div className="app-container">
      <div className="app-header">
        <h1>🏸 Badminton Video Editor</h1>
        <p>AI-powered automatic rally detection and editing</p>
      </div>

      <div className="app-main">
        {stage === 'upload' && (
          <UploadForm onUploadSuccess={handleUploadSuccess} apiUrl={API_URL} />
        )}

        {stage === 'processing' && jobData && (
          <ProcessingStatus
            videoId={videoData.video_id}
            jobId={jobData.job_id}
            onProcessingComplete={handleProcessingComplete}
            apiUrl={API_URL}
          />
        )}

        {stage === 'results' && resultsData && (
          <ResultsView
            videoId={videoData.video_id}
            result={resultsData}
            apiUrl={API_URL}
            onReset={handleReset}
          />
        )}
      </div>

      <div className="app-footer">
        <p>Made with ❤️ for badminton enthusiasts</p>
        <p className="tech-stack">Backend: FastAPI | Frontend: React | ML: YOLOv8</p>
      </div>
    </div>
  )
}

export default App
