"use client"

import { useState, useCallback, useEffect } from "react"
import { AppSidebar, type Section } from "@/components/app-sidebar"
import { DataEntryPage } from "@/components/data-entry-page"
import { DatabasePage } from "@/components/database-page"
import { AnalysisPage } from "@/components/analysis-page"
import { ExportPage } from "@/components/export-page"
import { NotificationStack, type NotificationData } from "@/components/notification"
import { ScrollArea } from "@/components/ui/scroll-area"
import { loadStore, saveStore, type StoreData } from "@/lib/biosensor-store"

export default function Page() {
  const [activeSection, setActiveSection] = useState<Section>("data_entry")
  const [data, setData] = useState<StoreData | null>(null)
  const [notifications, setNotifications] = useState<NotificationData[]>([])
  const [notifId, setNotifId] = useState(0)

  useEffect(() => {
    setData(loadStore())
  }, [])

  const updateData = useCallback((newData: StoreData) => {
    setData(newData)
    saveStore(newData)
  }, [])

  const showNotification = useCallback(
    (message: string, type: "success" | "error" | "warning" | "info") => {
      const id = notifId + 1
      setNotifId(id)
      setNotifications((prev) => [...prev, { id, message, type }])
    },
    [notifId]
  )

  const dismissNotification = useCallback((id: number) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  const handleSidebarSave = useCallback(() => {
    if (data) {
      saveStore(data)
      showNotification("Data saved to local storage", "success")
    }
  }, [data, showNotification])

  const handleSidebarLoad = useCallback(() => {
    const loaded = loadStore()
    setData(loaded)
    showNotification("Data loaded from local storage", "info")
  }, [showNotification])

  const handleSidebarClear = useCallback(() => {
    showNotification("Navigate to Data Entry to clear the form", "info")
    setActiveSection("data_entry")
  }, [showNotification])

  const handleSidebarExport = useCallback(() => {
    setActiveSection("export")
  }, [])

  if (!data) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading biosensor data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <AppSidebar
        activeSection={activeSection}
        onNavigate={setActiveSection}
        onSave={handleSidebarSave}
        onLoad={handleSidebarLoad}
        onClear={handleSidebarClear}
        onExport={handleSidebarExport}
      />
      <main className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4 pt-16 sm:p-6 md:pt-6 lg:p-8">
            {activeSection === "data_entry" && (
              <DataEntryPage data={data} onSave={updateData} showNotification={showNotification} />
            )}
            {activeSection === "database" && <DatabasePage data={data} />}
            {activeSection === "analysis" && (
              <AnalysisPage data={data} onSave={updateData} showNotification={showNotification} />
            )}
            {activeSection === "export" && (
              <ExportPage data={data} showNotification={showNotification} />
            )}
          </div>
        </ScrollArea>
      </main>
      <NotificationStack notifications={notifications} onDismiss={dismissNotification} />
    </div>
  )
}
