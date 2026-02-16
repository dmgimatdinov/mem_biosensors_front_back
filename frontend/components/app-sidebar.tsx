"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import {
  FlaskConical,
  Database,
  BarChart3,
  Download,
  Save,
  FolderOpen,
  Trash2,
  FileSpreadsheet,
  Cpu,
  Menu,
} from "lucide-react"

export type Section = "data_entry" | "database" | "analysis" | "export"

interface AppSidebarProps {
  activeSection: Section
  onNavigate: (section: Section) => void
  onSave?: () => void
  onLoad?: () => void
  onClear?: () => void
  onExport?: () => void
}

const navItems: { id: Section; label: string; icon: React.ElementType }[] = [
  { id: "data_entry", label: "Data Entry", icon: FlaskConical },
  { id: "database", label: "Database", icon: Database },
  { id: "analysis", label: "Analysis", icon: BarChart3 },
  { id: "export", label: "Export", icon: Download },
]

function SidebarContent({
  activeSection,
  onNavigate,
  onSave,
  onLoad,
  onClear,
  onExport,
  onItemClick,
}: AppSidebarProps & { onItemClick?: () => void }) {
  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sidebar-primary">
          <Cpu className="h-5 w-5 text-sidebar-primary-foreground" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-sidebar-accent-foreground">
            BioSensor
          </h1>
          <p className="text-xs text-sidebar-foreground/60">Passport Manager</p>
        </div>
      </div>

      <Separator className="bg-sidebar-border" />

      <ScrollArea className="flex-1 px-3 py-4">
        {/* File Section */}
        <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-sidebar-foreground/50">
          File
        </p>
        <div className="mb-4 flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="flex-1 justify-start gap-2 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            onClick={() => { onSave?.(); onItemClick?.() }}
          >
            <Save className="h-4 w-4" aria-hidden="true" />
            Save
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="flex-1 justify-start gap-2 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            onClick={() => { onLoad?.(); onItemClick?.() }}
          >
            <FolderOpen className="h-4 w-4" aria-hidden="true" />
            Load
          </Button>
        </div>

        <Separator className="mb-4 bg-sidebar-border" />

        {/* Navigation */}
        <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-sidebar-foreground/50">
          Navigation
        </p>
        <nav className="mb-4 flex flex-col gap-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = activeSection === item.id
            return (
              <button
                key={item.id}
                onClick={() => { onNavigate(item.id); onItemClick?.() }}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar-background",
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
              </button>
            )
          })}
        </nav>

        <Separator className="mb-4 bg-sidebar-border" />

        {/* Tools */}
        <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-sidebar-foreground/50">
          Tools
        </p>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="flex-1 justify-start gap-2 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            onClick={() => { onClear?.(); onItemClick?.() }}
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Clear
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="flex-1 justify-start gap-2 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            onClick={() => { onExport?.(); onItemClick?.() }}
          >
            <FileSpreadsheet className="h-4 w-4" aria-hidden="true" />
            Export
          </Button>
        </div>
      </ScrollArea>

      <Separator className="bg-sidebar-border" />
      <div className="px-5 py-3">
        <p className="text-xs text-sidebar-foreground/40">
          v1.0.0 &middot; Memristive Biosensor
        </p>
      </div>
    </div>
  )
}

export function AppSidebar(props: AppSidebarProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden h-screen w-64 shrink-0 border-r border-sidebar-border md:flex">
        <SidebarContent {...props} />
      </aside>

      {/* Mobile hamburger + sheet */}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="fixed left-3 top-3 z-50 h-10 w-10 min-h-[44px] min-w-[44px] rounded-lg bg-card shadow-md md:hidden"
            aria-label="Open navigation menu"
          >
            <Menu className="h-5 w-5 text-foreground" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <SidebarContent {...props} onItemClick={() => setOpen(false)} />
        </SheetContent>
      </Sheet>
    </>
  )
}
