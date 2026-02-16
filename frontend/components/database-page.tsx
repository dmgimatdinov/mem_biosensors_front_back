"use client"

import { useState, useMemo, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ChevronLeft, ChevronRight, Database } from "lucide-react"
import type { StoreData, TableName } from "@/lib/biosensor-store"
import { TABLE_LABELS } from "@/lib/biosensor-store"

const PAGE_SIZE = 10

/* ── Responsive column group sizes ── */
const COLS_PER_GROUP_DESKTOP = 6
const COLS_PER_GROUP_MOBILE = 3

function useColsPerGroup() {
  // SSR-safe: default to desktop, override on mount via CSS media query
  // We use a simple approach: render both mobile and desktop UIs hidden via Tailwind
  return { mobile: COLS_PER_GROUP_MOBILE, desktop: COLS_PER_GROUP_DESKTOP }
}

/* ── Column definitions ── */

interface ColDef {
  key: string
  label: string
  pinned?: boolean // pinned columns are always visible (ID, Name)
}

const COLUMN_DEFS: Record<TableName, ColDef[]> = {
  analytes: [
    { key: "ta_id", label: "ID", pinned: true },
    { key: "ta_name", label: "Name", pinned: true },
    { key: "ph_min", label: "pH min" },
    { key: "ph_max", label: "pH max" },
    { key: "t_max", label: "T max" },
    { key: "stability", label: "Stability" },
    { key: "half_life", label: "Half-life" },
    { key: "power_consumption", label: "Power" },
  ],
  bioRecognitions: [
    { key: "bre_id", label: "ID", pinned: true },
    { key: "bre_name", label: "Name", pinned: true },
    { key: "ph_min", label: "pH min" },
    { key: "ph_max", label: "pH max" },
    { key: "sensitivity", label: "Sensitivity" },
    { key: "reproducibility", label: "Reprod." },
    { key: "t_min", label: "T min" },
    { key: "t_max", label: "T max" },
    { key: "dr_min", label: "DR min" },
    { key: "dr_max", label: "DR max" },
    { key: "response_time", label: "Resp. time" },
    { key: "stability", label: "Stability" },
    { key: "lod", label: "LOD" },
    { key: "durability", label: "Durability" },
    { key: "power_consumption", label: "Power" },
  ],
  immobilizations: [
    { key: "im_id", label: "ID", pinned: true },
    { key: "im_name", label: "Name", pinned: true },
    { key: "ph_min", label: "pH min" },
    { key: "ph_max", label: "pH max" },
    { key: "adhesion", label: "Adhesion" },
    { key: "young_modulus", label: "Young mod." },
    { key: "solubility", label: "Solubility" },
    { key: "loss_coefficient", label: "Loss coeff." },
    { key: "t_min", label: "T min" },
    { key: "t_max", label: "T max" },
    { key: "reproducibility", label: "Reprod." },
    { key: "response_time", label: "Resp. time" },
    { key: "stability", label: "Stability" },
    { key: "durability", label: "Durability" },
    { key: "power_consumption", label: "Power" },
  ],
  memristives: [
    { key: "mem_id", label: "ID", pinned: true },
    { key: "mem_name", label: "Name", pinned: true },
    { key: "ph_min", label: "pH min" },
    { key: "ph_max", label: "pH max" },
    { key: "sensitivity", label: "Sensitivity" },
    { key: "young_modulus", label: "Young mod." },
    { key: "reproducibility", label: "Reprod." },
    { key: "t_min", label: "T min" },
    { key: "t_max", label: "T max" },
    { key: "dr_min", label: "DR min" },
    { key: "dr_max", label: "DR max" },
    { key: "response_time", label: "Resp. time" },
    { key: "stability", label: "Stability" },
    { key: "lod", label: "LOD" },
    { key: "durability", label: "Durability" },
    { key: "power_consumption", label: "Power" },
  ],
  combinations: [
    { key: "id", label: "ID", pinned: true },
    { key: "ta_id", label: "Analyte" },
    { key: "bre_id", label: "BRE" },
    { key: "im_id", label: "IM" },
    { key: "mem_id", label: "MEM" },
    { key: "score", label: "Score" },
    { key: "createdAt", label: "Created" },
  ],
}

/* ── Helpers ── */

function getTableData(data: StoreData, table: TableName): Record<string, unknown>[] {
  switch (table) {
    case "analytes":
      return data.analytes
    case "bioRecognitions":
      return data.bioRecognitions
    case "immobilizations":
      return data.immobilizations
    case "memristives":
      return data.memristives
    case "combinations":
      return data.combinations
  }
}

function TableSkeleton() {
  return (
    <div className="flex flex-col gap-2 p-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full rounded" />
      ))}
    </div>
  )
}

/* ── Column group pagination logic ── */

function useColumnGroups(allCols: ColDef[], groupSize: number) {
  return useMemo(() => {
    const pinned = allCols.filter((c) => c.pinned)
    const scrollable = allCols.filter((c) => !c.pinned)

    if (scrollable.length <= groupSize) {
      // All fit in one group, no pagination needed
      return { pinned, groups: [scrollable], totalGroups: 1, needsPagination: false }
    }

    const groups: ColDef[][] = []
    for (let i = 0; i < scrollable.length; i += groupSize) {
      groups.push(scrollable.slice(i, i + groupSize))
    }

    return { pinned, groups, totalGroups: groups.length, needsPagination: true }
  }, [allCols, groupSize])
}

/* ── Column group navigator bar ── */

interface ColumnNavProps {
  currentGroup: number
  totalGroups: number
  scrollableCols: ColDef[]
  groupSize: number
  onPrev: () => void
  onNext: () => void
}

function ColumnNav({ currentGroup, totalGroups, scrollableCols, groupSize, onPrev, onNext }: ColumnNavProps) {
  const startCol = currentGroup * groupSize + 1
  const endCol = Math.min((currentGroup + 1) * groupSize, scrollableCols.length)

  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-muted/50 px-3 py-2">
      <Button
        variant="ghost"
        size="sm"
        disabled={currentGroup === 0}
        onClick={onPrev}
        className="gap-1 text-xs min-h-[36px]"
        aria-label="Previous column group"
      >
        <ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" />
        <span className="hidden sm:inline">Prev</span>
      </Button>

      <div className="flex flex-col items-center gap-0.5">
        <span className="text-xs font-medium text-foreground">
          Group {currentGroup + 1}/{totalGroups}
        </span>
        <span className="text-[10px] text-muted-foreground">
          columns {startCol}-{endCol} of {scrollableCols.length}
        </span>
      </div>

      {/* Progress dots */}
      <div className="hidden sm:flex items-center gap-1 mx-3">
        {Array.from({ length: totalGroups }).map((_, i) => (
          <div
            key={i}
            className={`h-1.5 rounded-full transition-all duration-200 ${
              i === currentGroup ? "w-4 bg-primary" : "w-1.5 bg-border"
            }`}
          />
        ))}
      </div>

      <Button
        variant="ghost"
        size="sm"
        disabled={currentGroup >= totalGroups - 1}
        onClick={onNext}
        className="gap-1 text-xs min-h-[36px]"
        aria-label="Next column group"
      >
        <span className="hidden sm:inline">Next</span>
        <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
      </Button>
    </div>
  )
}

/* ── Main component ── */

interface DatabasePageProps {
  data: StoreData
}

export function DatabasePage({ data }: DatabasePageProps) {
  const [activeTable, setActiveTable] = useState<TableName>("analytes")
  const [currentPage, setCurrentPage] = useState(0)
  const [colGroupDesktop, setColGroupDesktop] = useState(0)
  const [colGroupMobile, setColGroupMobile] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)

  const { mobile: mobileSize, desktop: desktopSize } = useColsPerGroup()

  const tableData = useMemo(() => getTableData(data, activeTable), [data, activeTable])
  const allColDefs = useMemo(() => COLUMN_DEFS[activeTable], [activeTable])

  const desktopGroups = useColumnGroups(allColDefs, desktopSize)
  const mobileGroups = useColumnGroups(allColDefs, mobileSize)

  const totalPages = Math.max(1, Math.ceil(tableData.length / PAGE_SIZE))
  const pageData = tableData.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE)

  const handleTableChange = useCallback((table: string) => {
    setIsTransitioning(true)
    setActiveTable(table as TableName)
    setCurrentPage(0)
    setColGroupDesktop(0)
    setColGroupMobile(0)
    setTimeout(() => setIsTransitioning(false), 120)
  }, [])

  // Build visible columns for each breakpoint
  const desktopVisibleCols = useMemo(() => {
    const groupCols = desktopGroups.groups[colGroupDesktop] ?? []
    return [...desktopGroups.pinned, ...groupCols]
  }, [desktopGroups, colGroupDesktop])

  const mobileVisibleCols = useMemo(() => {
    const groupCols = mobileGroups.groups[colGroupMobile] ?? []
    return [...mobileGroups.pinned, ...groupCols]
  }, [mobileGroups, colGroupMobile])

  const scrollableCols = useMemo(() => allColDefs.filter((c) => !c.pinned), [allColDefs])

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">Database</h2>
        <p className="text-sm text-muted-foreground">
          Browse and manage biosensor data tables
        </p>
      </div>

      {/* Table selector tabs */}
      <Tabs value={activeTable} onValueChange={handleTableChange}>
        <TabsList className="grid w-full grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-1">
          {(Object.keys(TABLE_LABELS) as TableName[]).map((key) => (
            <TabsTrigger key={key} value={key} className="text-[10px] sm:text-xs">
              {TABLE_LABELS[key]}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Table card */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-4">
            <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
              <Database className="h-4 w-4 text-primary" aria-hidden="true" />
              {TABLE_LABELS[activeTable]}
              <Badge variant="secondary" className="ml-1 text-xs font-normal">
                {tableData.length} rows
              </Badge>
            </CardTitle>
            <Badge variant="outline" className="text-[10px] font-normal text-muted-foreground">
              {allColDefs.length} columns
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="flex flex-col gap-3 px-4 pb-4">
          {isTransitioning ? (
            <TableSkeleton />
          ) : tableData.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Database className="mb-3 h-10 w-10 opacity-40" aria-hidden="true" />
              <p className="text-sm">No data in this table yet</p>
            </div>
          ) : (
            <>
              {/* Column group navigator -- DESKTOP */}
              {desktopGroups.needsPagination && (
                <div className="hidden md:block">
                  <ColumnNav
                    currentGroup={colGroupDesktop}
                    totalGroups={desktopGroups.totalGroups}
                    scrollableCols={scrollableCols}
                    groupSize={desktopSize}
                    onPrev={() => setColGroupDesktop((g) => Math.max(0, g - 1))}
                    onNext={() => setColGroupDesktop((g) => Math.min(desktopGroups.totalGroups - 1, g + 1))}
                  />
                </div>
              )}

              {/* Column group navigator -- MOBILE */}
              {mobileGroups.needsPagination && (
                <div className="md:hidden">
                  <ColumnNav
                    currentGroup={colGroupMobile}
                    totalGroups={mobileGroups.totalGroups}
                    scrollableCols={scrollableCols}
                    groupSize={mobileSize}
                    onPrev={() => setColGroupMobile((g) => Math.max(0, g - 1))}
                    onNext={() => setColGroupMobile((g) => Math.min(mobileGroups.totalGroups - 1, g + 1))}
                  />
                </div>
              )}

              {/* DESKTOP table */}
              <div className="hidden md:block">
                <div className="max-h-[28rem] overflow-y-auto rounded-lg border border-border">
                  <Table>
                    <TableHeader className="sticky top-0 z-10 bg-muted/95 backdrop-blur-sm">
                      <TableRow className="hover:bg-transparent">
                        {desktopVisibleCols.map((col) => (
                          <TableHead
                            key={col.key}
                            className={`whitespace-nowrap px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider ${
                              col.pinned ? "bg-muted text-foreground" : ""
                            }`}
                          >
                            {col.label}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pageData.map((row, i) => (
                        <TableRow key={i} className="hover:bg-muted/30">
                          {desktopVisibleCols.map((col) => {
                            const value = (row as Record<string, unknown>)[col.key]
                            return (
                              <TableCell
                                key={col.key}
                                className={`whitespace-nowrap px-3 py-2 text-sm tabular-nums ${
                                  col.pinned ? "font-medium text-foreground" : ""
                                }`}
                              >
                                {value !== undefined && value !== null && value !== ""
                                  ? String(value)
                                  : "\u2014"}
                              </TableCell>
                            )
                          })}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {/* MOBILE table */}
              <div className="md:hidden">
                <div className="max-h-[24rem] overflow-y-auto rounded-lg border border-border">
                  <Table>
                    <TableHeader className="sticky top-0 z-10 bg-muted/95 backdrop-blur-sm">
                      <TableRow className="hover:bg-transparent">
                        {mobileVisibleCols.map((col) => (
                          <TableHead
                            key={col.key}
                            className={`whitespace-nowrap px-2 py-2 text-[10px] font-semibold uppercase tracking-wider ${
                              col.pinned ? "bg-muted text-foreground" : ""
                            }`}
                          >
                            {col.label}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pageData.map((row, i) => (
                        <TableRow key={i} className="hover:bg-muted/30">
                          {mobileVisibleCols.map((col) => {
                            const value = (row as Record<string, unknown>)[col.key]
                            return (
                              <TableCell
                                key={col.key}
                                className={`whitespace-nowrap px-2 py-1.5 text-xs tabular-nums ${
                                  col.pinned ? "font-medium text-foreground" : ""
                                }`}
                              >
                                {value !== undefined && value !== null && value !== ""
                                  ? String(value)
                                  : "\u2014"}
                              </TableCell>
                            )
                          })}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {/* Row pagination */}
              <div className="flex items-center justify-between pt-1">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === 0}
                  onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                  className="gap-1 min-h-[44px] min-w-[44px]"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                  <span className="hidden sm:inline">Previous</span>
                </Button>
                <span className="text-sm font-medium text-muted-foreground">
                  Page {currentPage + 1} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= totalPages - 1}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
                  className="gap-1 min-h-[44px] min-w-[44px]"
                  aria-label="Next page"
                >
                  <span className="hidden sm:inline">Next</span>
                  <ChevronRight className="h-4 w-4" aria-hidden="true" />
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
