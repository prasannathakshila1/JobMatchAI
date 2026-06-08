import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { hrAPI } from '../../api/hr'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import { fmtDate, statusBadge } from '../../utils/helpers'
import {
  Briefcase, Upload, List, Star,
  Calendar, BarChart2, Users, ArrowRight,
  TrendingUp, FileText,
} from 'lucide-react'

const features = [
  { label: 'Job Posts',     icon: Briefcase,  to: '/hr/jobs',       desc: 'Create and manage job posts'      },
  { label: 'Bulk Upload',   icon: Upload,      to: '/hr/upload',     desc: 'Upload multiple CVs at once'      },
  { label: 'Job Ranking',   icon: List,        to: '/hr/ranking',    desc: 'Rank CVs against a job'           },
  { label: 'Shortlist',     icon: Star,        to: '/hr/shortlist',  desc: 'Manage candidate shortlists'      },
  { label: 'Skill Gap',     icon: TrendingUp,  to: '/hr/skill-gap',  desc: 'Analyze candidate skill gaps'     },
  { label: 'Interviews',    icon: Calendar,    to: '/hr/interviews', desc: 'Schedule and track interviews'    },
  { label: 'Analytics',     icon: BarChart2,   to: '/hr/analytics',  desc: 'Hiring metrics and charts'        },
  { label: 'Team & Collab', icon: Users,       to: '/hr/collab',     desc: 'Team reviews and voting'          },
]

export default function HRDashboard() {
  const { user } = useAuth()
  const navigate  = useNavigate()
  const [overview, setOverview] = useState(null)
  const [jobs, setJobs]         = useState([])
  const [upcoming, setUpcoming] = useState([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    Promise.all([
      hrAPI.getAnalytics(),
      hrAPI.getJobs({ limit: 5 }),
      hrAPI.getUpcoming(),
    ]).then(([a, j, u]) => {
      setOverview(a.data.overview)
      setJobs(j.data.jobs || [])
      setUpcoming(u.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const overviewCards = [
    { label: 'Open Jobs',         value: overview?.open_jobs        || 0, color: 'var(--success)' },
    { label: 'CVs Processed',     value: overview?.total_cv_processed || 0, color: 'var(--primary)' },
    { label: 'Shortlisted',       value: overview?.total_shortlisted  || 0, color: 'var(--warning)' },
    { label: 'Avg Match Score',   value: overview?.average_match_score ? `${overview.average_match_score}%` : '—', color: 'var(--info)' },
  ]

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>
          Welcome, {user?.name?.split(' ')[0]} 👋
        </h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          {user?.company_name ? `${user.company_name} · ` : ''}HR Dashboard
        </p>
      </div>

      {/* Overview stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        {overviewCards.map((s) => (
          <Card key={s.label} padding="20px">
            <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 13, color: 'var(--gray-500)', marginTop: 4 }}>{s.label}</div>
          </Card>
        ))}
      </div>

      {/* Feature grid */}
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 14 }}>HR Tools</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
        {features.map(({ label, icon: Icon, to, desc }) => (
          <Card
            key={to} padding="18px"
            style={{ cursor: 'pointer', transition: 'box-shadow 0.15s' }}
            onClick={() => navigate(to)}
          >
            <div style={{
              width: 38, height: 38, borderRadius: 10,
              background: 'var(--primary-light)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 10,
            }}>
              <Icon size={18} color="var(--primary)" />
            </div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>{label}</div>
            <div style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 3, lineHeight: 1.4 }}>{desc}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 3, marginTop: 10, color: 'var(--primary)', fontSize: 11 }}>
              Open <ArrowRight size={11} />
            </div>
          </Card>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Recent jobs */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h2 style={{ fontSize: 15, fontWeight: 600 }}>Recent Job Posts</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/hr/jobs')}>
              View all <ArrowRight size={12} />
            </Button>
          </div>
          <Card padding="0">
            {jobs.length === 0 ? (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--gray-400)', fontSize: 13 }}>
                No job posts yet. <span style={{ color: 'var(--primary)', cursor: 'pointer' }} onClick={() => navigate('/hr/jobs')}>Create one</span>
              </div>
            ) : jobs.map((j, i) => (
              <div key={j.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '12px 18px',
                borderBottom: i < jobs.length - 1 ? '1px solid var(--gray-100)' : 'none',
              }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{j.title}</div>
                  <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 2 }}>
                    {j.location || 'Remote'} · {fmtDate(j.created_at)}
                  </div>
                </div>
                <Badge variant={statusBadge(j.status)}>{j.status}</Badge>
              </div>
            ))}
          </Card>
        </div>

        {/* Upcoming interviews */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h2 style={{ fontSize: 15, fontWeight: 600 }}>Upcoming Interviews</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/hr/interviews')}>
              View all <ArrowRight size={12} />
            </Button>
          </div>
          <Card padding="0">
            {upcoming.length === 0 ? (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--gray-400)', fontSize: 13 }}>
                No upcoming interviews in next 7 days
              </div>
            ) : upcoming.map((iv, i) => (
              <div key={iv.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '12px 18px',
                borderBottom: i < upcoming.length - 1 ? '1px solid var(--gray-100)' : 'none',
              }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>
                    Interview · {fmtDate(iv.scheduled_date)}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 2 }}>
                    {iv.duration_minutes} min · {iv.meeting_link ? 'Online' : 'On-site'}
                  </div>
                </div>
                <Badge variant={statusBadge(iv.status)}>{iv.status}</Badge>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  )
}