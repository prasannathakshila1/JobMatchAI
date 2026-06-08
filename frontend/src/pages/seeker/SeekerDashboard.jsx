import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { seekerAPI } from '../../api/seeker'
import { sharedAPI } from '../../api/shared'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import { statusBadge, fmtDate } from '../../utils/helpers'
import {
  TrendingUp, CheckSquare, AlertCircle, Mail,
  MessageSquare, Briefcase, Upload, ArrowRight,
} from 'lucide-react'

const features = [
  { label: 'Resume Enhancer',      icon: TrendingUp,    to: '/seeker/enhancer',     desc: 'Get your match score & eligibility'    },
  { label: 'ATS Checker',          icon: CheckSquare,   to: '/seeker/ats',           desc: 'Check ATS compatibility'                },
  { label: 'Rejection Diagnostic', icon: AlertCircle,   to: '/seeker/diagnostic',    desc: 'Find out why you were rejected'         },
  { label: 'Cover Letter',         icon: Mail,          to: '/seeker/cover-letter',  desc: 'Generate a tailored cover letter'       },
  { label: 'Interview Q&A',        icon: MessageSquare, to: '/seeker/interview-q',   desc: 'Role-specific questions with answers'   },
  { label: 'Job Tracker',          icon: Briefcase,     to: '/seeker/tracker',       desc: 'Track all your applications'            },
]

export default function SeekerDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats]     = useState(null)
  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      seekerAPI.getStats(),
      sharedAPI.getMyResumes(),
    ]).then(([s, r]) => {
      setStats(s.data)
      setResumes(r.data.resumes || [])
    }).finally(() => setLoading(false))
  }, [])

  const statCards = [
    { label: 'Applied',   value: stats?.applied   || 0, color: 'var(--info)'    },
    { label: 'Interview', value: stats?.interview  || 0, color: 'var(--warning)' },
    { label: 'Offers',    value: stats?.offer      || 0, color: 'var(--success)' },
    { label: 'Rejected',  value: stats?.rejected   || 0, color: 'var(--danger)'  },
  ]

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>
          Welcome back, {user?.name?.split(' ')[0]} 👋
        </h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Here's your job search overview
        </p>
      </div>

      {/* Upload resume CTA */}
      {resumes.length === 0 && (
        <Card style={{ marginBottom: 24, background: 'var(--primary-light)', border: '1px solid var(--primary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontWeight: 600, color: 'var(--primary-dark)' }}>Upload your resume to get started</p>
              <p style={{ fontSize: 13, color: 'var(--gray-600)', marginTop: 2 }}>
                Upload once — use across all 6 features
              </p>
            </div>
            <Button onClick={() => navigate('/seeker/enhancer')}>
              <Upload size={15} /> Upload Resume
            </Button>
          </div>
        </Card>
      )}

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        {statCards.map((s) => (
          <Card key={s.label} padding="20px">
            <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 13, color: 'var(--gray-500)', marginTop: 4 }}>{s.label}</div>
          </Card>
        ))}
      </div>

      {/* Feature grid */}
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 14 }}>AI Tools</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 28 }}>
        {features.map(({ label, icon: Icon, to, desc }) => (
          <Card
            key={to}
            padding="20px"
            style={{ cursor: 'pointer', transition: 'all 0.15s' }}
            onClick={() => navigate(to)}
          >
            <div style={{
              width: 40, height: 40, borderRadius: 10,
              background: 'var(--primary-light)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 12,
            }}>
              <Icon size={20} color="var(--primary)" />
            </div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{label}</div>
            <div style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 4 }}>{desc}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 12, color: 'var(--primary)', fontSize: 12 }}>
              Open <ArrowRight size={12} />
            </div>
          </Card>
        ))}
      </div>

      {/* Recent resumes */}
      {resumes.length > 0 && (
        <>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 14 }}>Your Resumes</h2>
          <Card padding="0">
            {resumes.slice(0, 5).map((r, i) => (
              <div key={r.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '14px 20px',
                borderBottom: i < resumes.length - 1 ? '1px solid var(--gray-100)' : 'none',
              }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 500 }}>{r.original_filename}</div>
                  <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 2 }}>
                    {fmtDate(r.uploaded_at)} · {r.char_count?.toLocaleString()} chars
                  </div>
                </div>
                <Badge variant={r.validation_status === 'auto_approved' ? 'success' : 'gray'}>
                  {r.validation_status}
                </Badge>
              </div>
            ))}
          </Card>
        </>
      )}
    </div>
  )
}