import Spinner from './Spinner'
import clsx from 'clsx'

const styles = {
  base: {
    display:        'inline-flex',
    alignItems:     'center',
    justifyContent: 'center',
    gap:            '6px',
    padding:        '8px 16px',
    borderRadius:   'var(--radius)',
    fontWeight:     500,
    fontSize:       '14px',
    border:         'none',
    transition:     'all 0.15s',
    cursor:         'pointer',
  },
  primary: {
    background: 'var(--primary)',
    color:      '#fff',
  },
  secondary: {
    background: 'var(--gray-100)',
    color:      'var(--gray-700)',
    border:     '1px solid var(--gray-200)',
  },
  danger: {
    background: 'var(--danger)',
    color:      '#fff',
  },
  ghost: {
    background: 'transparent',
    color:      'var(--primary)',
  },
  sm: { padding: '5px 10px', fontSize: '12px' },
  lg: { padding: '11px 22px', fontSize: '15px' },
}

export default function Button({
  children,
  variant = 'primary',
  size,
  loading = false,
  disabled = false,
  onClick,
  type = 'button',
  style = {},
  fullWidth = false,
}) {
  const combined = {
    ...styles.base,
    ...styles[variant],
    ...(size ? styles[size] : {}),
    ...(fullWidth ? { width: '100%' } : {}),
    ...(disabled || loading ? { opacity: 0.6, cursor: 'not-allowed' } : {}),
    ...style,
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      style={combined}
    >
      {loading && <Spinner size={14} color={variant === 'primary' ? '#fff' : 'var(--primary)'} />}
      {children}
    </button>
  )
}