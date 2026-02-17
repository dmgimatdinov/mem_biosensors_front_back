"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { FlaskConical, Trophy, BarChart3, Loader2 } from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts"
import type { StoreData, SensorCombination } from "@/lib/biosensor-store"

interface AnalysisPageProps {
  data: StoreData
  showNotification: (msg: string, type: "success" | "error" | "warning" | "info") => void
  onSynthesizeCombinations: (max: number) => Promise<{ checked: number; created: number }>
}

export function AnalysisPage({ data, showNotification, onSynthesizeCombinations }: AnalysisPageProps) {
  const [synthesizing, setSynthesizing] = useState(false)
  const [topN, setTopN] = useState([10])
  const [selectedCombo, setSelectedCombo] = useState<string>("")

  const sortedCombinations = useMemo(
    () => [...data.combinations].sort((a, b) => b.score - a.score),
    [data.combinations]
  )

  const topCombinations = sortedCombinations.slice(0, topN[0])

  const stats = useMemo(() => {
    const scores = data.combinations.map((c) => c.score)
    return {
      total: data.combinations.length,
      avgScore: scores.length ? Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10 : 0,
      maxScore: scores.length ? Math.max(...scores) : 0,
    }
  }, [data.combinations])

  // Distribution chart data
  const distributionData = useMemo(() => {
    const buckets = Array.from({ length: 10 }, (_, i) => ({
      range: `${i * 10}-${(i + 1) * 10}`,
      count: 0,
    }))
    data.combinations.forEach((c) => {
      const idx = Math.min(Math.floor(c.score / 10), 9)
      buckets[idx].count++
    })
    return buckets
  }, [data.combinations])

  const handleSynthesize = async () => {
    setSynthesizing(true)
    try {
      const result = await onSynthesizeCombinations(10000)
      showNotification(
        `Synthesis complete: ${result.checked} checked, ${result.created} new combinations created`,
        "success"
      )
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to synthesize combinations"
      showNotification(errorMessage, "error")
    } finally {
      setSynthesizing(false)
    }
  }

  const selectedComboData = useMemo((): SensorCombination | undefined => {
    return data.combinations.find((c) => c.id === selectedCombo)
  }, [data.combinations, selectedCombo])

  const CHART_COLORS = [
    "hsl(220 14% 88%)",
    "hsl(220 14% 82%)",
    "hsl(220 14% 76%)",
    "hsl(220 14% 70%)",
    "hsl(210 60% 65%)",
    "hsl(210 80% 55%)",
    "hsl(210 100% 48%)",
    "hsl(160 50% 50%)",
    "hsl(160 60% 42%)",
    "hsl(160 70% 35%)",
  ]

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          Analysis & Synthesis
        </h2>
        <p className="text-sm text-muted-foreground">
          Synthesize combinations and analyze sensor performance
        </p>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card className="border-border bg-card">
          <CardContent className="flex flex-col items-center gap-3 p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
              <FlaskConical className="h-6 w-6 text-primary" aria-hidden="true" />
            </div>
            <h3 className="font-semibold text-foreground">Synthesize</h3>
            <p className="text-center text-xs text-muted-foreground">
              Generate all possible sensor combinations (max 5000)
            </p>
            <Button
              onClick={handleSynthesize}
              disabled={synthesizing}
              className="mt-2 w-full gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {synthesizing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Synthesizing...
                </>
              ) : (
                <>
                  <FlaskConical className="h-4 w-4" />
                  Run Synthesis
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardContent className="flex flex-col items-center gap-3 p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl" style={{ backgroundColor: "hsl(32 85% 48% / 0.1)" }}>
              <Trophy className="h-6 w-6" style={{ color: "hsl(32 85% 48%)" }} aria-hidden="true" />
            </div>
            <h3 className="font-semibold text-foreground">Top Combinations</h3>
            <p className="text-center text-xs text-muted-foreground">
              {stats.total} total combinations available
            </p>
            <div className="mt-2 w-full">
              <p className="mb-1 text-xs text-muted-foreground">
                Show top {topN[0]} results
              </p>
              <Slider value={topN} onValueChange={setTopN} min={1} max={50} step={1} />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardContent className="flex flex-col items-center gap-3 p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10">
              <BarChart3 className="h-6 w-6 text-accent" aria-hidden="true" />
            </div>
            <h3 className="font-semibold text-foreground">Statistics</h3>
            <div className="mt-2 grid w-full grid-cols-3 gap-2 text-center">
              <div>
                <p className="text-lg font-bold text-primary">{stats.total}</p>
                <p className="text-[10px] text-muted-foreground">Total</p>
              </div>
              <div>
                <p className="text-lg font-bold text-foreground">{stats.avgScore}</p>
                <p className="text-[10px] text-muted-foreground">Avg Score</p>
              </div>
              <div>
                <p className="text-lg font-bold text-accent">{stats.maxScore}</p>
                <p className="text-[10px] text-muted-foreground">Max Score</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Combinations Table */}
      {topCombinations.length > 0 && (
        <Card className="border-border bg-card">
          <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <Trophy className="h-4 w-4" style={{ color: "hsl(32 85% 48%)" }} aria-hidden="true" />
              Top {topN[0]} Combinations by Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto rounded-lg border border-border">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50 hover:bg-muted/50">
                    <TableHead className="text-xs font-semibold uppercase">#</TableHead>
                    <TableHead className="text-xs font-semibold uppercase">ID</TableHead>
                    <TableHead className="text-xs font-semibold uppercase">Analyte</TableHead>
                    <TableHead className="text-xs font-semibold uppercase">BRE</TableHead>
                    <TableHead className="text-xs font-semibold uppercase">IM</TableHead>
                    <TableHead className="text-xs font-semibold uppercase">MEM</TableHead>
                    <TableHead className="text-xs font-semibold uppercase text-right">Score</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topCombinations.map((combo, idx) => (
                    <TableRow key={combo.id} className="hover:bg-muted/30">
                      <TableCell className="text-sm font-medium text-muted-foreground">{idx + 1}</TableCell>
                      <TableCell className="text-sm font-mono">{combo.id}</TableCell>
                      <TableCell className="text-sm">{combo.ta_id}</TableCell>
                      <TableCell className="text-sm">{combo.bre_id}</TableCell>
                      <TableCell className="text-sm">{combo.im_id}</TableCell>
                      <TableCell className="text-sm">{combo.mem_id}</TableCell>
                      <TableCell className="text-right">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                            combo.score >= 90
                              ? "bg-accent/10 text-accent"
                              : combo.score >= 70
                              ? "bg-primary/10 text-primary"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {combo.score}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Detail Viewer */}
            <div className="mt-4 flex flex-col gap-2">
              <p className="text-xs font-medium text-muted-foreground">View combination details (JSON)</p>
              <Select value={selectedCombo} onValueChange={setSelectedCombo}>
                <SelectTrigger className="bg-card text-foreground">
                  <SelectValue placeholder="Select a combination..." />
                </SelectTrigger>
                <SelectContent>
                  {topCombinations.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.id} &mdash; Score: {c.score}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedComboData && (
                <pre className="mt-2 overflow-auto rounded-lg border border-border bg-muted p-4 text-xs text-foreground">
                  {JSON.stringify(selectedComboData, null, 2)}
                </pre>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Score Distribution Chart */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <BarChart3 className="h-4 w-4 text-primary" aria-hidden="true" />
            Score Distribution
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data.combinations.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <p className="text-sm">No combinations to visualize. Run synthesis first.</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={distributionData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 14% 88%)" />
                <XAxis dataKey="range" tick={{ fill: "hsl(220 10% 45%)", fontSize: 12 }} />
                <YAxis tick={{ fill: "hsl(220 10% 45%)", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(0 0% 100%)",
                    border: "1px solid hsl(220 14% 88%)",
                    borderRadius: "8px",
                    color: "hsl(220 20% 10%)",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
                  }}
                  labelStyle={{ color: "hsl(220 20% 10%)", fontWeight: 600 }}
                  cursor={{ fill: "hsl(210 100% 45% / 0.08)" }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {distributionData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
