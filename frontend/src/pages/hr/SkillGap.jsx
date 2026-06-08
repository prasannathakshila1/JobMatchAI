import { useState, useEffect } from 'react'
import { hrAPI } from '../../api/hr'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import ScoreBar from '../../components/ui/ScoreBar'
import { TrendingUp } from 'lucide-react'

export default function SkillGap() {
  const [jobs, setJobs]         = useState([])
  const [jobId, setJobId]       = useState('')
  const [rankings, setRankings] = useState([])
  const [resumeId, setResumeId] = useState('')
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)

  useEffect(() => {
    hrAPI.getJobs({ status: 'open' }).then((r) => {
      const list = r.data.jobs || []
      setJobs(list)
      if (list.length > 0) setJobId(list[0].id)
    })
  }, [])

  useEffect(() => {
    if (!jobId) return
    hrAPI.getRankings(jobId)
      .then((r) => {
        const list = r.data?.rankings || []
        setRankings(list)
        if (list.length > 0) setResumeId(list[0].resume_id)
      })
      .catch(() => setRankings([]))
  }, [jobId])

  const handleAnalyze = async () => {
    if (!resumeId || !jobId) { toast.error('Select a job and candidate'); return }
    setLoading(true)
    try {
      const res = await hrAPI.skillGap({ resume_id: resumeId, job_id: jobId })
      setResult(res.data)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const severityColor = (s) =>
    s === 'Low' ? 'var(--success)' : s === 'Medium' ? 'var(--warning)' : 'var(--danger)'

  const selectStyle = {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--gray-300)',
    borderRadius: 10, fontSize: 14, background: '#fff',
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Skill Gap Analysis</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Compare candidate skills against job requirements
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 24 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Settings</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
                  Job Post
                </label>
                <select value={jobId} onChange={(e) => setJobId(e.target.value)} style={selectStyle}>
                  {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
                  Candidate
                </label>
                <select value={resumeId} onChange={(e) => setResumeId(e.target.value)} style={selectStyle}>
                  <option value="">-- Select candidate --</option>
                  {rankings.map((r) => (
                    <option key={r.resume_id} value={r.resume_id}>
                      {r.candidate_name || r.filename} — {Math.round(r.score)}%
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </Card>
          <Button onClick={handleAnalyze} loading={loading} fullWidth size="lg">
            <TrendingUp size={16} /> Analyze Skill Gap
          </Button>
        </div>

        <div>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <Card>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                  <div>
                    <h3 style={{ fontWeight: 600 }}>{result.candidate_name}</h3>
                    <p style={{ fontSize: 13, color: 'var(--gray-500)', marginTop: 2 }}>{result.recommendation}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 28, fontWeight: 700, color: severityColor(result.gap_severity) }}>
                      {result.match_percentage}%
                    </div>
                    <Badge variant={
                      result.gap_severity === 'Low' ? 'success' :
                      result.gap_severity === 'Medium' ? 'warning' : 'danger'
                    }>
                      {result.gap_severity} Gap
                    </Badge>
                  </div>
                </div>
                <ScoreBar score={result.match_percentage} />
                <div style={{ display: 'flex', gap: 20, marginTop: 14 }}>
                  {[
                    { label: 'Required', value: result.total_required, color: 'var(--gray-600)' },
                    { label: 'Matched',  value: result.total_matched,  color: 'var(--success)'  },
                    { label: 'Missing',  value: result.total_missing,   color: 'var(--danger)'   },
                  ].map((s) => (
                    <div key={s.label} style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
                      <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>{s.label}</div>
                    </div>
                  ))}
                </div>
              </Card>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <Card>
                  <h3 style={{ fontWeight: 600, color: 'var(--success)', marginBottom: 10, fontSize: 14 }}>
                    ✓ Matched Skills
                  </h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {result.matched_skills.map((s) => <Badge key={s} variant="success">{s}</Badge>)}
                    {result.matched_skills.length === 0 && (
                      <p style={{ fontSize: 13, color: 'var(--gray-400)' }}>No matches</p>
                    )}
                  </div>
                </Card>
                <Card>
                  <h3 style={{ fontWeight: 600, color: 'var(--danger)', marginBottom: 10, fontSize: 14 }}>
                    ✗ Missing Skills
                  </h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {result.missing_skills.map((s) => <Badge key={s} variant="danger">{s}</Badge>)}
                    {result.missing_skills.length === 0 && (
                      <p style={{ fontSize: 13, color: 'var(--success)' }}>No gaps — perfect match!</p>
                    )}
                  </div>
                </Card>
              </div>

              {result.additional_skills?.length > 0 && (
                <Card>
                  <h3 style={{ fontWeight: 600, marginBottom: 10, fontSize: 14 }}>
                    + Additional Skills (bonus)
                  </h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {result.additional_skills.map((s) => <Badge key={s} variant="purple">{s}</Badge>)}
                  </div>
                </Card>
              )}
            </div>
          ) : (
            <Card style={{ minHeight: 360, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12 }}>
              <TrendingUp size={44} color="var(--gray-300)" />
              <p style={{ color: 'var(--gray-400)', fontSize: 14 }}>Select a job and candidate to analyze</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}