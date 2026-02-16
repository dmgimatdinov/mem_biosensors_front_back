"use client"

import { useEffect } from "react"
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from "lucide-react"
import { cn } from "@/lib/utils"

export interface NotificationData {
  id: number
  message: string
  type: "success" | "error" | "warning" | "info"
}

interface NotificationProps {
  notifications: NotificationData[]
  onDismiss: (id: number) => void
}

const icons = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const styles = {
  success: "border-accent/40 bg-accent/10 text-accent",
  error: "border-destructive/40 bg-destructive/10 text-destructive",
  warning: "border-[hsl(32,95%,52%)]/40 bg-[hsl(32,95%,52%)]/10 text-[hsl(32,95%,42%)]",
  info: "border-primary/40 bg-primary/10 text-primary",
}

export function NotificationStack({ notifications, onDismiss }: NotificationProps) {
  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex flex-col gap-2">
      {notifications.map((n) => (
        <NotificationItem key={n.id} notification={n} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

function NotificationItem({
  notification,
  onDismiss,
}: {
  notification: NotificationData
  onDismiss: (id: number) => void
}) {
  const Icon = icons[notification.type]

  useEffect(() => {
    const timer = setTimeout(() => onDismiss(notification.id), 4000)
    return () => clearTimeout(timer)
  }, [notification.id, onDismiss])

  return (
    <div
      className={cn(
        "pointer-events-auto flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg backdrop-blur-sm animate-in slide-in-from-right-5 fade-in duration-300",
        styles[notification.type]
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <p className="text-sm font-medium">{notification.message}</p>
      <button
        onClick={() => onDismiss(notification.id)}
        className="ml-2 shrink-0 rounded p-1 opacity-60 hover:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-label="Dismiss notification"
      >
        <X className="h-3.5 w-3.5" aria-hidden="true" />
      </button>
    </div>
  )
}
