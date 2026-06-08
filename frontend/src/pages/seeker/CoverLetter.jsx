import { useState, useEffect } from 'react'
import { sharedAPI } from '../../api/shared'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import { Mail, Copy, Download } from 'lucide-react'

const TONES = ['professional', 'enthusiastic', 'concise']

export default function CoverLetter() {
  const [resumes, setResumes]       = useState([])
  const [resumeId, setResumeId]     = useState('')
  const [jdText, setJdText]         = useState('')
  const [companyName, setCompany]   = useState('')
  const [jobTitle, setJobTitle]     = useState('')
  const [applicantName, setName]    = useState('')
  const [tone, setTone]             = useState('professional')
  const [loading, setLoading]       = useState(false)
  const [result, setResult]         = useState(null)
  const [editedLetter, setEdited]   = useState('')
  const [letterId, setLetterId]     = useState(null)
  const [saving, setSaving]         = useState(false)

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
      const res = await seekerAPI.coverLetter({
        resume_id:      resumeId,
        jd_text:        jdText,
        company_name:   companyName || 'the company',
        job_title:      jobTitle    || 'this position',
        applicant_name: applicantName || 'Applicant',
        tone,
      })
      setResult(res.data)
      setEdited(res.data.cover_letter)
      setLetterId(res.data.cover_letter_id)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!letterId) return
    setSaving(true)
    try {
      await seekerAPI.updateCoverLetter(letterId, { edited_text: editedLetter })
      toast.success('Cover letter saved!')
    } catch {
      toast.error('Save failed')
    } finally {
      setSaving(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(editedLetter)
    toast.success('Copied to clipboard!')
  }

  const handleDownload = () => {
    const blob = new Blob([editedLetter], { type: 'text/plain' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `cover_letter_${companyName || 'jobmatch'}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const selectStyle = {
    padding: '9px 12px', border: '1px solid var(--gray-300)',
    borderRadius: 'var(--radius)', fontSize: 14, background: '#fff',
    width: '100%',
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Cover Letter Generator</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          AI-powered tailored cover letters — no OpenAI needed
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 24 }}>
        {/* Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Settings</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 4 }}>
                  Resume
                </label>
                <select value={resumeId} onChange={(e) => setResumeId(e.target.value)} style={selectStyle}>
                  {resumes.map((r) => (
                    <option key={r.id} value={r.id}>{r.original_filename}</option>
                  ))}
                </select>
              </div>

              <Input
                label="Your Name (optional)"
                placeholder="Auto-detected from resume"
                value={applicantName}
                onChange={(e) => setName(e.target.value)}
              />
              <Input
                label="Company Name (optional)"
                placeholder="Auto-detected from JD"
                value={companyName}
                onChange={(e) => setCompany(e.target.value)}
              />
              <Input
                label="Job Title (optional)"
                placeholder="Auto-detected from JD"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
              />

              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 4 }}>
                  Tone
                </label>
                <div style={{ display: 'flex', gap: 8 }}>
                  {TONES.map((t) => (
                    <button key={t} onClick={() => setTone(t)} style={{
                      flex: 1, padding: '7px 4px', borderRadius: 8,
                      border: `2px solid ${tone === t ? 'var(--primary)' : 'var(--gray-200)'}`,
                      background: tone === t ? 'var(--primary-light)' : '#fff',
                      color: tone === t ? 'var(--primary)' : 'var(--gray-600)',
                      fontSize: 12, fontWeight: 500, cursor: 'pointer',
                      textTransform: 'capitalize',
                    }}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 10 }}>Job Description</h3>
            <Input
              name="jd" rows={8}
              placeholder="Paste the full job description..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
            />
          </Card>

          <Button onClick={handleGenerate} loading={loading} fullWidth size="lg">
            <Mail size={16} /> Generate Cover Letter
          </Button>
        </div>

        {/* Output */}
        <div>
          {result ? (
            <Card style={{ height: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                <div>
                  <h3 style={{ fontWeight: 600 }}>Your Cover Letter</h3>
                  <p style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 2 }}>
                    {result.word_count} words · Tone: {result.tone}
                  </p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <Button variant="secondary" size="sm" onClick={handleCopy}>
                    <Copy size={13} /> Copy
                  </Button>
                  <Button variant="secondary" size="sm" onClick={handleDownload}>
                    <Download size={13} /> Download
                  </Button>
                  <Button size="sm" onClick={handleSave} loading={saving}>
                    Save
                  </Button>
                </div>
              </div>

              <textarea
                value={editedLetter}
                onChange={(e) => setEdited(e.target.value)}
                style={{
                  width: '100%', minHeight: 520,
                  padding: '16px', border: '1px solid var(--gray-200)',
                  borderRadius: 'var(--radius)', fontSize: 14,
                  lineHeight: 1.8, resize: 'vertical',
                  fontFamily: 'inherit', color: 'var(--gray-800)',
                  background: 'var(--gray-50)',
                }}
              />

              {result.matched_skills_used?.length > 0 && (
                <p style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 10 }}>
                  Skills highlighted: {result.matched_skills_used.join(', ')}
                </p>
              )}
            </Card>
          ) : (
            <Card style={{
              height: '100%', display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 12,
              minHeight: 400,
            }}>
              <Mail size={48} color="var(--gray-300)" />
              <p style={{ color: 'var(--gray-400)', fontSize: 14 }}>
                Fill in the settings and click Generate
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}