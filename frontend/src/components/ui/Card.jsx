export default function Card({ children, style = {}, padding = '24px', shadow = true }) {
  return (
    <div style={{
      background:   '#fff',
      borderRadius: 'var(--radius)',
      padding,
      boxShadow:    shadow ? 'var(--shadow)' : 'none',
      border:       '1px solid var(--gray-200)',
      ...style,
    }}>
      {children}
    </div>
  )
}