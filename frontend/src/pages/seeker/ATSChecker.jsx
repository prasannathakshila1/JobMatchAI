import { useState, useEffect } from 'react'
import { sharedAPI } from '../../api/shared'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import ScoreBar from '../../components/ui/ScoreBar'
import Badge from '../../components/ui/Badge'
import { CheckCircle, AlertTriangle, XCircle, Shield } from 'lucide-react'

export default function ATSChecker() {
  const [resumes, setResumes]   = useState([])
  const [resumeId, setResumeId] = useState('')
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)

  useEffect(() => {
    sharedAPI.getMyResumes().then((r) => {
      const list = r.data.resumes || []
      setResumes(list)
      if (list.length > 0) setResumeId(list[0].id)
    })
  }, [])

  const handleCheck = async () => {
    if (!resumeId) { toast.error('Select a resume first'); return }
    setLoading(true)
    try {
      const res = await seekerAPI.atsChecker({ resume_id: resumeId })
      setResult(res.data)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Check failed')
    } finally {
      setLoading(false)
    }
  }

  const gradeColor = (score) =>
    score >= 85 ? 'var(--success)' :
    score >= 70 ? 'var(--info)'    :
    score >= 55 ? 'var(--warning)' : 'var(--danger)'

  const checkIcon = (score, max) => {
    const pct = (score / max) * 100
    if (pct >= 80) return <CheckCircle size={16} color="var(--success)" />
    if (pct >= 50) return <AlertTriangle size={16} color="var(--warning)" />
    return <XCircle size={16} color="var(--danger)" />
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>ATS Checker</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Check how well your resume passes Applicant Tracking Systems
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: result ? '380px 1fr' : '480px', gap: 24 }}>
        {/* Select resume */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Shield size={18} color="var(--primary)" /> Select Resume
            </h3>
            {resumes.length === 0 ? (
              <p style={{ color: 'var(--gray-400)', fontSize: 13 }}>
                No resumes uploaded yet. Upload one via Resume Enhancer.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {resumes.map((r) => (
                  <label key={r.id} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 14px', borderRadius: 8, cursor: 'pointer',
                    border: `2px solid ${resumeId === r.id ? 'var(--primary)' : 'var(--gray-200)'}`,
                    background: resumeId === r.id ? 'var(--primary-light)' : '#fff',
                  }}>
                    <input
                      type="radio" name="resume" value={r.id}
                      checked={resumeId === r.id}
                      onChange={() => setResumeId(r.id)}
                      style={{ accentColor: 'var(--primary)' }}
                    />
                    <div style={{ fontSize: 13 }}>{r.original_filename}</div>
                  </label>
                ))}
              </div>
            )}
          </Card>

          <Button onClick={handleCheck} loading={loading} fullWidth size="lg" disabled={!resumeId}>
            Run ATS Check
          </Button>

          {/* Info card */}
          <Card style={{ background: '#fffbeb', border: '1px solid #fde68a' }}>
            <p style={{ fontSize: 12, color: '#92400e', lineHeight: 1.6 }}>
              <strong>75% of resumes</strong> are rejected by ATS before a human reads them.
              This tool checks format, keywords, structure, and compatibility.
            </p>
          </Card>
        </div>

        {/* Results */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Score */}
            <Card>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 48, fontWeight: 800, color: gradeColor(result.ats_score), lineHeight: 1 }}>
                    {result.ats_score}
                    <span style={{ fontSize: 22 }}>/100</span>
                  </div>
                  <p style={{ fontSize: 14, fontWeight: 500, color: 'var(--gray-600)', marginTop: 4 }}>
                    {result.grade}
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: 13, color: 'var(--gray-500)', maxWidth: 220, lineHeight: 1.5 }}>
                    {result.summary}
                  </p>
                </div>
              </div>
              <ScoreBar score={result.ats_score} />
            </Card>

            {/* Detailed checks */}
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Detailed Checks</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {Object.entries(result.checks || {}).map(([key, val]) => (
                  <div key={key} style={{
                    padding: '12px 16px',
                    borderRadius: 8,
                    border: '1px solid var(--gray-200)',
                    background: 'var(--gray-50)',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {checkIcon(val.score, val.max)}
                        <span style={{ fontWeight: 500, fontSize: 13, textTransform: 'capitalize' }}>
                          {key.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <span style={{ fontSize: 12, color: 'var(--gray-500)' }}>
                        {val.score}/{val.max}
                      </span>
                    </div>
                    <ScoreBar score={val.score} max={val.max} showValue={false} />
                    {val.issues?.map((issue, i) => (
                      <p key={i} style={{
                        marginTop: 8, fontSize: 12,
                        color: 'var(--danger)', lineHeight: 1.5,
                      }}>
                        ⚠ {issue}
                      </p>
                    ))}
                    {val.details?.action_verbs_found?.length > 0 && (
                      <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {val.details.action_verbs_found.map((v) => (
                          <Badge key={v} variant="success" style={{ fontSize: 10 }}>{v}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Card>

            {/* All suggestions */}
            {result.suggestions?.length > 0 && (
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 12 }}>Fix These Issues</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {result.suggestions.map((s, i) => (
                    <div key={i} style={{
                      padding: '10px 14px',
                      background: '#fff7ed',
                      borderLeft: '3px solid var(--warning)',
                      borderRadius: '0 8px 8px 0',
                      fontSize: 13, lineHeight: 1.6,
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