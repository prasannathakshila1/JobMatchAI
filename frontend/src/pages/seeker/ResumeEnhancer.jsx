import { useState, useEffect } from 'react'
import { sharedAPI } from '../../api/shared'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import ScoreBar from '../../components/ui/ScoreBar'
import FileDropzone from '../../components/ui/FileDropzone'
import Badge from '../../components/ui/Badge'
import { CheckCircle, XCircle, Upload, Zap } from 'lucide-react'

export default function ResumeEnhancer() {
  const [resumes, setResumes]     = useState([])
  const [resumeId, setResumeId]   = useState('')
  const [jdText, setJdText]       = useState('')
  const [file, setFile]           = useState(null)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading]     = useState(false)
  const [result, setResult]       = useState(null)

  useEffect(() => {
    sharedAPI.getMyResumes().then((r) => {
      setResumes(r.data.resumes || [])
      if (r.data.resumes?.length > 0) setResumeId(r.data.resumes[0].id)
    })
  }, [])

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await sharedAPI.uploadResume(fd)
      toast.success('Resume uploaded!')
      const newResume = res.data.resume
      setResumes((p) => [newResume, ...p])
      setResumeId(newResume.id)
      setFile(null)
    } catch {
      toast.error('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!resumeId || !jdText.trim()) {
      toast.error('Select a resume and paste a job description')
      return
    }
    setLoading(true)
    try {
      const res = await seekerAPI.resumeEnhancer({ resume_id: resumeId, jd_text: jdText })
      setResult(res.data)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const scoreColor = (s) => s >= 70 ? 'var(--success)' : s >= 45 ? 'var(--warning)' : 'var(--danger)'

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Resume Enhancer</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Get your selection probability and interview eligibility score
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: result ? '1fr 1fr' : '1fr', gap: 24 }}>
        {/* Left — Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Upload new resume */}
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Upload Resume</h3>
            <FileDropzone
              onDrop={(f) => setFile(f[0])}
              file={file}
              hint="PDF or DOCX · max 5MB"
            />
            {file && (
              <Button onClick={handleUpload} loading={uploading} style={{ marginTop: 12 }} fullWidth>
                <Upload size={15} /> Upload
              </Button>
            )}
          </Card>

          {/* Select resume */}
          {resumes.length > 0 && (
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Select Resume</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {resumes.map((r) => (
                  <label key={r.id} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 14px', borderRadius: 8, cursor: 'pointer',
                    border: `2px solid ${resumeId === r.id ? 'var(--primary)' : 'var(--gray-200)'}`,
                    background: resumeId === r.id ? 'var(--primary-light)' : '#fff',
                    transition: 'all 0.12s',
                  }}>
                    <input
                      type="radio" name="resume" value={r.id}
                      checked={resumeId === r.id}
                      onChange={() => setResumeId(r.id)}
                      style={{ accentColor: 'var(--primary)' }}
                    />
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{r.original_filename}</div>
                      <div style={{ fontSize: 11, color: 'var(--gray-400)' }}>
                        {r.char_count?.toLocaleString()} characters extracted
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </Card>
          )}

          {/* JD input */}
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Job Description</h3>
            <Input
              label="Paste the full job description"
              name="jd"
              rows={8}
              placeholder="Copy and paste the job description here..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
            />
          </Card>

          <Button onClick={handleAnalyze} loading={loading} fullWidth size="lg">
            <Zap size={16} /> Analyze Match
          </Button>
        </div>

        {/* Right — Results */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Overall score */}
            <Card>
              <div style={{ textAlign: 'center', padding: '8px 0 16px' }}>
                <div style={{
                  fontSize: 64, fontWeight: 800,
                  color: scoreColor(result.overall_score),
                  lineHeight: 1,
                }}>
                  {Math.round(result.overall_score)}
                  <span style={{ fontSize: 28 }}>%</span>
                </div>
                <div style={{ marginTop: 8 }}>
                  <Badge variant={result.interview_eligible ? 'success' : 'danger'} style={{ fontSize: 13, padding: '4px 16px' }}>
                    {result.eligibility_label}
                  </Badge>
                </div>
                <p style={{ color: 'var(--gray-500)', fontSize: 13, marginTop: 10 }}>
                  {result.selection_probability}
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
                <ScoreBar score={result.embedding_score}    label="Semantic Match"  />
                <ScoreBar score={result.skill_overlap_score} label="Skill Overlap"  />
              </div>
            </Card>

            {/* Summary */}
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 10 }}>Summary</h3>
              <p style={{ fontSize: 13, color: 'var(--gray-600)', lineHeight: 1.7 }}>{result.summary}</p>
            </Card>

            {/* Skills */}
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Skills Analysis</h3>
              {result.matched_skills?.length > 0 && (
                <div style={{ marginBottom: 14 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--success)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <CheckCircle size={13} /> Matched Skills ({result.matched_skills.length})
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {result.matched_skills.map((s) => (
                      <Badge key={s} variant="success">{s}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {result.missing_skills?.length > 0 && (
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--danger)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <XCircle size={13} /> Missing Skills ({result.missing_skills.length})
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {result.missing_skills.map((s) => (
                      <Badge key={s} variant="danger">{s}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </Card>

            {/* Section scores */}
            {result.section_scores && (
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Section Scores</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {Object.entries(result.section_scores).map(([k, v]) => (
                    <ScoreBar key={k} score={v} max={10}
                      label={k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                    />
                  ))}
                </div>
              </Card>
            )}

            {/* Suggestions */}
            {result.improvement_suggestions?.length > 0 && (
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 12 }}>Improvement Suggestions</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {result.improvement_suggestions.map((s, i) => (
                    <div key={i} style={{
                      padding: '10px 14px',
                      background: 'var(--gray-50)',
                      borderLeft: '3px solid var(--primary)',
                      borderRadius: '0 8px 8px 0',
                      fontSize: 13, color: 'var(--gray-700)',
                      lineHeight: 1.6,
                    }}>
                      {s}
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}