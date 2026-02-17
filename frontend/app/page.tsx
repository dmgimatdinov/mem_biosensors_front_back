"use client"

import { useState, useCallback } from "react"
import { AppSidebar, type Section } from "@/components/app-sidebar"
import { DataEntryPage } from "@/components/data-entry-page"
import { DatabasePage } from "@/components/database-page"
import { AnalysisPage } from "@/components/analysis-page"
import { ExportPage } from "@/components/export-page"
import { NotificationStack, type NotificationData } from "@/components/notification"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useBiosensorData } from "@/hooks/use-biosensor-data"

export default function Page() {
  const [activeSection, setActiveSection] = useState<Section>("data_entry")
  const [notifications, setNotifications] = useState<NotificationData[]>([])
  const [notifId, setNotifId] = useState(0)

  // Fetch data from backend API instead of localStorage
  const {
    data,
    loading,
    error,
    refetch,
    createNewAnalyte,
    createNewBioRecognition,
    createNewImmobilization,
    createNewMemristive,
    synthesizeNewCombinations,
  } = useBiosensorData()

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
    // Refresh data from server (backend auto-saves)
    refetch()
    showNotification("Data refreshed from server", "success")
  }, [refetch, showNotification])

  const handleSidebarLoad = useCallback(() => {
    // Refresh data from server
    refetch()
    showNotification("Data reloaded from server", "info")
  }, [refetch, showNotification])

  const handleSidebarClear = useCallback(() => {
    showNotification("Navigate to Data Entry to clear the form", "info")
    setActiveSection("data_entry")
  }, [showNotification])

  const handleSidebarExport = useCallback(() => {
    setActiveSection("export")
  }, [])

  // Show error state if API fetch failed
  if (error && !loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3 max-w-md text-center">
          <div className="text-destructive text-4xl">⚠️</div>
          <h2 className="text-xl font-semibold text-foreground">Connection Error</h2>
          <p className="text-sm text-muted-foreground">{error}</p>
          <p className="text-xs text-muted-foreground mt-2">
            Make sure the backend server is running at http://localhost:8000
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  // Show loading state
  if (loading || !data) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading biosensor data from server...</p>
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
              <DataEntryPage
                data={data}
                showNotification={showNotification}
                onCreateAnalyte={createNewAnalyte}
                onCreateBioRecognition={createNewBioRecognition}
                onCreateImmobilization={createNewImmobilization}
                onCreateMemristive={createNewMemristive}
              />
            )}
            {activeSection === "database" && <DatabasePage data={data} />}
            {activeSection === "analysis" && (
              <AnalysisPage
                data={data}
                showNotification={showNotification}
                onSynthesizeCombinations={synthesizeNewCombinations}
              />
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
