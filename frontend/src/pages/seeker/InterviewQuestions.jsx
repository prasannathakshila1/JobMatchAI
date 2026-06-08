import { useState, useEffect } from 'react'
import { sharedAPI } from '../../api/shared'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Badge from '../../components/ui/Badge'
import { MessageSquare, ChevronDown, ChevronUp } from 'lucide-react'

function QuestionCard({ q }) {
  const [open, setOpen] = useState(false)

  const catColor = (cat) => {
    if (cat?.toLowerCase().includes('technical')) return 'info'
    if (cat?.toLowerCase().includes('behavioural')) return 'purple'
    if (cat?.toLowerCase().includes('experience')) return 'warning'
    return 'gray'
  }

  return (
    <Card padding="16px" style={{ marginBottom: 10 }}>
      <div
        style={{ cursor: 'pointer' }}
        onClick={() => setOpen((p) => !p)}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span style={{
                width: 24, height: 24, borderRadius: '50%',
                background: 'var(--primary-light)', color: 'var(--primary)',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, fontWeight: 700, flexShrink: 0,
              }}>
                {q.number}
              </span>
              <Badge variant={catColor(q.category)}>{q.category}</Badge>
            </div>
            <p style={{ fontSize: 14, fontWeight: 500, lineHeight: 1.5 }}>{q.question}</p>
          </div>
          {open ? <ChevronUp size={18} color="var(--gray-400)" style={{ flexShrink: 0, marginTop: 4 }} />
                : <ChevronDown size={18} color="var(--gray-400)" style={{ flexShrink: 0, marginTop: 4 }} />}
        </div>
      </div>

      {open && (
        <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--gray-100)' }}>
          <div style={{ marginBottom: 12 }}>
            <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
              Answer Framework
            </p>
            <div style={{
              padding: '10px 14px',
              background: 'var(--primary-light)',
              borderRadius: 8,
              fontSize: 13, color: 'var(--gray-700)', lineHeight: 1.6,
            }}>
              {q.answer_framework}
            </div>
          </div>
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--success)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
              Sample Answer
            </p>
            <div style={{
              padding: '10px 14px',
              background: '#f0fdf4',
              borderRadius: 8,
              fontSize: 13, color: 'var(--gray-700)', lineHeight: 1.6,
            }}>
              {q.sample_answer}
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}

export default function InterviewQuestions() {
  const [resumes, setResumes]   = useState([])
  const [resumeId, setResumeId] = useState('')
  const [jdText, setJdText]     = useState('')
  const [numQ, setNumQ]         = useState(12)
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)
  const [filter, setFilter]     = useState('all')

  useEffect(() => {
    sharedAPI.getMyResumes().then((r) => {
      const list = r.data.resumes || []
      setResumes(list)
      if (list.length > 0) setResumeId(list[0].id)
    })
  }, [])

  const handleGenerate = async () => {
    if (!resumeId || !jdText.trim()) {
      toast.error('Select a resume and paste a job description')
      return
    }
    setLoading(true)
    try {
      const res = await seekerAPI.interviewQuestions({
        resume_id: resumeId, jd_text: jdText, num_questions: numQ,
      })
      setResult(res.data)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  const categories = result
    ? ['all', ...new Set(result.questions.map((q) => q.category.split('—')[0].trim()))]
    : []

  const filtered = result?.questions?.filter((q) =>
    filter === 'all' || q.category.startsWith(filter)
  ) || []

  const selectStyle = {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--gray-300)',
    borderRadius: 'var(--radius)', fontSize: 14, background: '#fff',
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Interview Question Generator</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Role-specific questions with STAR answer frameworks
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 24 }}>
        {/* Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Settings</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 4 }}>
                  Resume
                </label>
                <select value={resumeId} onChange={(e) => setResumeId(e.target.value)} style={selectStyle}>
                  {resumes.map((r) => <option key={r.id} value={r.id}>{r.original_filename}</option>)}
                </select>
              </div>

              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 4 }}>
                  Number of Questions: {numQ}
                </label>
                <input
                  type="range" min={5} max={20} value={numQ}
                  onChange={(e) => setNumQ(Number(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--primary)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--gray-400)' }}>
                  <span>5</span><span>20</span>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 10 }}>Job Description</h3>
            <Input
              name="jd" rows={10}
              placeholder="Paste the job description..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
            />
          </Card>

          <Button onClick={handleGenerate} loading={loading} fullWidth size="lg">
            <MessageSquare size={16} /> Generate Questions
          </Button>

          {/* Prep tips */}
          {result?.preparation_tips?.length > 0 && (
            <Card style={{ background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
              <h4 style={{ fontWeight: 600, marginBottom: 8, color: 'var(--success)', fontSize: 13 }}>
                Preparation Tips
              </h4>
              {result.preparation_tips.map((tip, i) => (
                <p key={i} style={{ fontSize: 12, color: 'var(--gray-600)', marginBottom: 6, lineHeight: 1.5 }}>
                  • {tip}
                </p>
              ))}
            </Card>
          )}
        </div>

        {/* Questions */}
        <div>
          {result ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                  <h3 style={{ fontWeight: 600 }}>
                    {result.total} Questions for {result.job_title}
                  </h3>
                  <p style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 2 }}>
                    Click any question to see the answer framework
                  </p>
                </div>
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  style={{ ...selectStyle, width: 180 }}
                >
                  {categories.map((c) => (
                    <option key={c} value={c}>{c === 'all' ? 'All categories' : c}</option>
                  ))}
                </select>
              </div>

              <div>
                {filtered.map((q) => <QuestionCard key={q.number} q={q} />)}
              </div>
            </>
          ) : (
            <Card style={{
              minHeight: 400, display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 12,
            }}>
              <MessageSquare size={48} color="var(--gray-300)" />
              <p style={{ color: 'var(--gray-400)', fontSize: 14 }}>
                Configure settings and click Generate
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}