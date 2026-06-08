import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

export default function AppLayout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{
        marginLeft: 'var(--sidebar-w)',
        flex:       1,
        padding:    '28px 32px',
        minHeight:  '100vh',
        background: 'var(--gray-50)',
      }}>
        <Outlet />
      </main>
      <ToastContainer
        position="top-right"
        autoClose={3500}
        hideProgressBar={false}
        newestOnTop
        pauseOnHover
      />
    </div>
  )
}