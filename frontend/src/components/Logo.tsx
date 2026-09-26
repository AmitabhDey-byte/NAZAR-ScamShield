export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand" aria-label="NAZAR">
      <span className="brand-mark" aria-hidden="true"><i /><b /></span>
      {!compact && <span>NAZAR</span>}
    </div>
  )
}

