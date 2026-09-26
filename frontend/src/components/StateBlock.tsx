import { AlertTriangle, LoaderCircle } from 'lucide-react'

export function LoadingBlock({ label = 'Loading intelligence…' }: { label?: string }) {
  return <div className="state-block"><LoaderCircle className="spin" size={20} /><span>{label}</span></div>
}

export function ErrorBlock({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="state-block error"><AlertTriangle size={20} /><span>{message}</span>{retry && <button onClick={retry}>Retry</button>}</div>
}

