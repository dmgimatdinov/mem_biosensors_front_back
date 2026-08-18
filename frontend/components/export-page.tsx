"use client"

import { useState, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Download, FileText, FileJson, Archive } from "lucide-react"
import type { StoreData, TableName } from "@/lib/biosensor-store"
import { TABLE_LABELS } from "@/lib/biosensor-store"

interface ExportPageProps {
  data: StoreData
  showNotification: (msg: string, type: "success" | "error" | "warning" | "info") => void
}

function getTableDataArray(data: StoreData, table: TableName): Record<string, unknown>[] {
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

function toCSV(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return ""
  const headers = Object.keys(rows[0])
  const csvRows = [
    headers.join(","),
    ...rows.map((row) =>
      headers.map((h) => {
        const val = String(row[h] ?? "")
        return val.includes(",") ? `"${val}"` : val
      }).join(",")
    ),
  ]
  return csvRows.join("\n")
}

function downloadFile(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function ExportPage({ data, showNotification }: ExportPageProps) {
  const [exportScope, setExportScope] = useState<"single" | "all">("single")
  const [format, setFormat] = useState<"csv" | "json">("csv")
  const [selectedTable, setSelectedTable] = useState<TableName>("analytes")

  const handleExportSingle = useCallback(() => {
    const tableData = getTableDataArray(data, selectedTable)
    if (tableData.length === 0) {
      showNotification("В этой таблице нет данных для экспорта", "warning")
      return
    }

    if (format === "csv") {
      const csv = toCSV(tableData)
      downloadFile(`${selectedTable}.csv`, csv, "text/csv")
    } else {
      const json = JSON.stringify(tableData, null, 2)
      downloadFile(`${selectedTable}.json`, json, "application/json")
    }
    showNotification(`Экспортировано: ${selectedTable} в формате ${format.toUpperCase()}`, "success")
  }, [data, selectedTable, format, showNotification])

  const handleExportAll = useCallback(() => {
    const allData: Record<string, Record<string, unknown>[]> = {}
    for (const table of Object.keys(TABLE_LABELS) as TableName[]) {
      allData[table] = getTableDataArray(data, table)
    }

    if (format === "csv") {
      // Export as combined CSV
      let combined = ""
      for (const [tableName, tableData] of Object.entries(allData)) {
        combined += `=== ${tableName} ===\n`
        combined += toCSV(tableData as Record<string, unknown>[])
        combined += "\n\n"
      }
      downloadFile("biosensor_all_data.csv", combined, "text/csv")
    } else {
      const json = JSON.stringify(allData, null, 2)
      downloadFile("biosensor_all_data.json", json, "application/json")
    }
    showNotification(`Все таблицы экспортированы в формате ${format.toUpperCase()}`, "success")
  }, [data, format, showNotification])

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">Экспорт данных</h2>
        <p className="text-sm text-muted-foreground">
          Экспорт данных биосенсоров в формат CSV или JSON
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Scope */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
              <Archive className="h-4 w-4 text-primary" aria-hidden="true" />
              Что экспортировать
            </CardTitle>
          </CardHeader>
          <CardContent>
            <RadioGroup value={exportScope} onValueChange={(v) => setExportScope(v as "single" | "all")} className="flex flex-col gap-3">
              <div className="flex items-center gap-3 rounded-lg border border-border p-3 transition-colors hover:bg-muted/50">
                <RadioGroupItem value="single" id="single" />
                <Label htmlFor="single" className="cursor-pointer text-foreground">
                  <span className="font-medium">Одна таблица</span>
                  <span className="block text-xs text-muted-foreground">Экспорт одной конкретной таблицы</span>
                </Label>
              </div>
              <div className="flex items-center gap-3 rounded-lg border border-border p-3 transition-colors hover:bg-muted/50">
                <RadioGroupItem value="all" id="all" />
                <Label htmlFor="all" className="cursor-pointer text-foreground">
                  <span className="font-medium">Все таблицы</span>
                  <span className="block text-xs text-muted-foreground">Экспорт всего сразу</span>
                </Label>
              </div>
            </RadioGroup>
          </CardContent>
        </Card>

        {/* Format */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
              <FileText className="h-4 w-4 text-primary" aria-hidden="true" />
              Формат
            </CardTitle>
          </CardHeader>
          <CardContent>
            <RadioGroup value={format} onValueChange={(v) => setFormat(v as "csv" | "json")} className="flex flex-col gap-3">
              <div className="flex items-center gap-3 rounded-lg border border-border p-3 transition-colors hover:bg-muted/50">
                <RadioGroupItem value="csv" id="csv" />
                <Label htmlFor="csv" className="flex cursor-pointer items-center gap-2 text-foreground">
                  <FileText className="h-4 w-4 text-accent" aria-hidden="true" />
                  <span>
                    <span className="font-medium">CSV</span>
                    <span className="block text-xs text-muted-foreground">Значения через запятую, совместимо с Excel</span>
                  </span>
                </Label>
              </div>
              <div className="flex items-center gap-3 rounded-lg border border-border p-3 transition-colors hover:bg-muted/50">
                <RadioGroupItem value="json" id="json" />
                <Label htmlFor="json" className="flex cursor-pointer items-center gap-2 text-foreground">
                  <FileJson className="h-4 w-4 text-primary" aria-hidden="true" />
                  <span>
                    <span className="font-medium">JSON</span>
                    <span className="block text-xs text-muted-foreground">Структурированный формат, идеален для API</span>
                  </span>
                </Label>
              </div>
            </RadioGroup>
          </CardContent>
        </Card>
      </div>

      {/* Conditional export panel */}
      <Card className="border-border bg-card">
        <CardContent className="p-6">
          {exportScope === "single" ? (
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <Label className="text-xs font-medium text-muted-foreground">Выберите таблицу</Label>
                <Select value={selectedTable} onValueChange={(v) => setSelectedTable(v as TableName)}>
                  <SelectTrigger className="bg-card text-foreground">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(Object.keys(TABLE_LABELS) as TableName[]).map((key) => (
                      <SelectItem key={key} value={key}>
                        {TABLE_LABELS[key]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-border bg-muted/50 p-4">
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {TABLE_LABELS[selectedTable]}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {getTableDataArray(data, selectedTable).length} доступно записей
                  </p>
                </div>
                <Button onClick={handleExportSingle} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
                  <Download className="h-4 w-4" aria-hidden="true" />
                  Экспорт {format.toUpperCase()}
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between rounded-lg border border-border bg-muted/50 p-4">
              <div>
                <p className="text-sm font-medium text-foreground">Все таблицы</p>
                <p className="text-xs text-muted-foreground">
                  {Object.keys(TABLE_LABELS).length} таблиц, всего записей: {" "}
                  {(Object.keys(TABLE_LABELS) as TableName[]).reduce(
                    (sum, key) => sum + getTableDataArray(data, key).length,
                    0
                  )}
                </p>
              </div>
              <Button onClick={handleExportAll} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
                <Download className="h-4 w-4" aria-hidden="true" />
                Экспорт всех в {format.toUpperCase()}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
