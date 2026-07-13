"use client"

import React, { useState, useCallback } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Save, Trash2, FolderOpen, Target, CircleDot, Layers, Cpu } from "lucide-react"
import type {
  Analyte,
  BioRecognitionLayer,
  ImmobilizationLayer,
  MemristiveLayer,
  StoreData,
} from "@/lib/biosensor-store"
import {
  emptyAnalyte,
  emptyBioRecognition,
  emptyImmobilization,
  emptyMemristive,
} from "@/lib/biosensor-store"

interface NumberFieldProps {
  label: string
  value: number
  onChange: (v: number) => void
  min?: number
  max?: number
  step?: number
  unit?: string
}

const NumberField = React.memo(function NumberField({ label, value, onChange, min, max, step = 1, unit }: NumberFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-xs font-medium text-muted-foreground">
        {label}
        {unit && <span className="ml-1 text-muted-foreground/70">({unit})</span>}
      </Label>
      <Input
        type="number"
        value={value ?? ""}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        min={min}
        max={max}
        step={step}
        className="h-10 bg-card text-foreground"
      />
    </div>
  )
})

const TextField = React.memo(function TextField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-xs font-medium text-muted-foreground">{label}</Label>
      <Input
        type="text"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="h-10 bg-card text-foreground"
      />
    </div>
  )
})

interface DataEntryPageProps {
  data: StoreData
  showNotification: (msg: string, type: "success" | "error" | "warning" | "info") => void
  onCreateAnalyte: (analyte: Analyte) => Promise<void>
  onCreateBioRecognition: (layer: BioRecognitionLayer) => Promise<void>
  onCreateImmobilization: (layer: ImmobilizationLayer) => Promise<void>
  onCreateMemristive: (layer: MemristiveLayer) => Promise<void>
}

export function DataEntryPage({
  data,
  showNotification,
  onCreateAnalyte,
  onCreateBioRecognition,
  onCreateImmobilization,
  onCreateMemristive,
}: DataEntryPageProps) {
  const [analyte, setAnalyte] = useState<Analyte>(emptyAnalyte())
  const [bre, setBre] = useState<BioRecognitionLayer>(emptyBioRecognition())
  const [im, setIm] = useState<ImmobilizationLayer>(emptyImmobilization())
  const [mem, setMem] = useState<MemristiveLayer>(emptyMemristive())
  const [saving, setSaving] = useState(false)
  const [duplicateDialog, setDuplicateDialog] = useState<{ open: boolean; duplicates: string[] }>({
    open: false,
    duplicates: [],
  })
  const [loadDialog, setLoadDialog] = useState(false)
  const [loadType, setLoadType] = useState<string>("analyte")
  const [loadId, setLoadId] = useState("")

  const updateAnalyte = useCallback(
    (field: keyof Analyte, value: string | number) =>
      setAnalyte((prev) => ({ ...prev, [field]: value })),
    []
  )
  const updateBre = useCallback(
    (field: keyof BioRecognitionLayer, value: string | number) =>
      setBre((prev) => ({ ...prev, [field]: value })),
    []
  )
  const updateIm = useCallback(
    (field: keyof ImmobilizationLayer, value: string | number) =>
      setIm((prev) => ({ ...prev, [field]: value })),
    []
  )
  const updateMem = useCallback(
    (field: keyof MemristiveLayer, value: string | number) =>
      setMem((prev) => ({ ...prev, [field]: value })),
    []
  )

  const handleSave = async () => {
    if (!analyte.ta_id || !analyte.ta_name) {
      showNotification("ID и название аналита обязательны", "error")
      return
    }
    if (!bre.bre_id || !bre.bre_name) {
      showNotification("ID и название BRE обязательны", "error")
      return
    }
    if (!im.im_id || !im.im_name) {
      showNotification("ID и название IM обязательны", "error")
      return
    }
    if (!mem.mem_id || !mem.mem_name) {
      showNotification("ID и название MEM обязательны", "error")
      return
    }

    const duplicates: string[] = []
    if (data.analytes.some((a) => a.ta_id === analyte.ta_id)) duplicates.push(`Analyte: ${analyte.ta_id}`)
    if (data.bioRecognitions.some((b) => b.bre_id === bre.bre_id)) duplicates.push(`BRE: ${bre.bre_id}`)
    if (data.immobilizations.some((i) => i.im_id === im.im_id)) duplicates.push(`IM: ${im.im_id}`)
    if (data.memristives.some((m) => m.mem_id === mem.mem_id)) duplicates.push(`MEM: ${mem.mem_id}`)

    if (duplicates.length > 0) {
      setDuplicateDialog({ open: true, duplicates })
      return
    }

    await savePassport()
  }

  const savePassport = async () => {
    setSaving(true)
    try {
      // Save all layers to backend via API
      await Promise.all([
        onCreateAnalyte(analyte),
        onCreateBioRecognition(bre),
        onCreateImmobilization(im),
        onCreateMemristive(mem),
      ])
      
      setDuplicateDialog({ open: false, duplicates: [] })
      showNotification("Все слои успешно сохранены в базу данных", "success")
      
      // Clear form after successful save
      handleClear()
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to save data"
      showNotification(errorMessage, "error")
    } finally {
      setSaving(false)
    }
  }

  const handleClear = () => {
    setAnalyte(emptyAnalyte())
    setBre(emptyBioRecognition())
    setIm(emptyImmobilization())
    setMem(emptyMemristive())
    showNotification("Форма очищена", "info")
  }

  const handleLoad = () => {
    const id = loadId.trim()
    if (!id) {
      showNotification("Введите ID для загрузки", "warning")
      return
    }

    if (loadType === "analyte") {
      const found = data.analytes.find((a) => a.ta_id === id)
      if (found) {
        setAnalyte(found)
        showNotification(`Аналит ${id} загружен`, "success")
      } else {
        showNotification(`Аналит ${id} не найден`, "error")
      }
    } else if (loadType === "bre") {
      const found = data.bioRecognitions.find((b) => b.bre_id === id)
      if (found) {
        setBre(found)
        showNotification(`BRE ${id} загружен`, "success")
      } else {
        showNotification(`BRE ${id} не найден`, "error")
      }
    } else if (loadType === "im") {
      const found = data.immobilizations.find((i) => i.im_id === id)
      if (found) {
        setIm(found)
        showNotification(`IM ${id} загружен`, "success")
      } else {
        showNotification(`IM ${id} не найден`, "error")
      }
    } else if (loadType === "mem") {
      const found = data.memristives.find((m) => m.mem_id === id)
      if (found) {
        setMem(found)
        showNotification(`MEM ${id} загружен`, "success")
      } else {
        showNotification(`MEM ${id} не найден`, "error")
      }
    }

    setLoadDialog(false)
    setLoadId("")
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground">Ввод данных</h2>
          <p className="text-sm text-muted-foreground">
            Создание и редактирование паспортов биосенсоров
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left Column */}
        <div className="flex flex-col gap-6">
          {/* Analyte Section */}
          <Card className="border-border bg-card">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10">
                  <Target className="h-4 w-4 text-primary" aria-hidden="true" />
                </div>
                Целевой аналит (TA)
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <TextField label="ID аналита" value={analyte.ta_id} onChange={(v) => updateAnalyte("ta_id", v)} placeholder="TA001" />
                <TextField label="Название" value={analyte.ta_name} onChange={(v) => updateAnalyte("ta_name", v)} placeholder="Глюкоза" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="pH мин" value={analyte.ph_min} onChange={(v) => updateAnalyte("ph_min", v)} min={2} max={10} step={0.1} />
                <NumberField label="pH макс" value={analyte.ph_max} onChange={(v) => updateAnalyte("ph_max", v)} min={2} max={10} step={0.1} />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <NumberField label="Макс. температура" value={analyte.t_max} onChange={(v) => updateAnalyte("t_max", v)} min={0} max={180} unit="C" />
                <NumberField label="Стабильность" value={analyte.stability} onChange={(v) => updateAnalyte("stability", v)} min={0} max={365} unit="days" />
                <NumberField label="Период полураспада" value={analyte.half_life} onChange={(v) => updateAnalyte("half_life", v)} min={0} max={8760} unit="h" />
              </div>
              <NumberField label="Энергопотребление" value={analyte.power_consumption} onChange={(v) => updateAnalyte("power_consumption", v)} min={0} max={1000} unit="mW" />
            </CardContent>
          </Card>

          <Separator />

          {/* BRE Section */}
          <Card className="border-border bg-card">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-destructive/10">
                  <CircleDot className="h-4 w-4 text-destructive" aria-hidden="true" />
                </div>
                Биораспознающий слой (BRE)
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <TextField label="ID BRE" value={bre.bre_id} onChange={(v) => updateBre("bre_id", v)} placeholder="BRE001" />
                <TextField label="Название" value={bre.bre_name} onChange={(v) => updateBre("bre_name", v)} placeholder="Фермент GOx" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="pH мин" value={bre.ph_min} onChange={(v) => updateBre("ph_min", v)} min={2} max={10} step={0.1} />
                <NumberField label="pH макс" value={bre.ph_max} onChange={(v) => updateBre("ph_max", v)} min={2} max={10} step={0.1} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="T мин" value={bre.t_min} onChange={(v) => updateBre("t_min", v)} min={4} max={120} unit="C" />
                <NumberField label="T макс" value={bre.t_max} onChange={(v) => updateBre("t_max", v)} min={4} max={120} unit="C" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="DR мин" value={bre.dr_min} onChange={(v) => updateBre("dr_min", v)} min={0.1} max={1e12} step={0.1} unit="pM" />
                <NumberField label="DR макс" value={bre.dr_max} onChange={(v) => updateBre("dr_max", v)} min={0.1} max={1e12} step={0.1} unit="pM" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <NumberField label="Чувствительность" value={bre.sensitivity} onChange={(v) => updateBre("sensitivity", v)} min={0} max={20000} unit="uA/(uM*cm2)" />
                <NumberField label="Воспроизводимость" value={bre.reproducibility} onChange={(v) => updateBre("reproducibility", v)} min={0} max={100} unit="%" />
                <NumberField label="Время отклика" value={bre.response_time} onChange={(v) => updateBre("response_time", v)} min={0} max={3600} unit="s" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <NumberField label="Стабильность" value={bre.stability} onChange={(v) => updateBre("stability", v)} min={0} max={365} unit="days" />
                <NumberField label="LOD" value={bre.lod} onChange={(v) => updateBre("lod", v)} min={0} max={100000} unit="nM" />
                <NumberField label="Долговечность" value={bre.durability} onChange={(v) => updateBre("durability", v)} min={0} max={100000} unit="h" />
              </div>
              <NumberField label="Энергопотребление" value={bre.power_consumption} onChange={(v) => updateBre("power_consumption", v)} min={0} max={1000} unit="mW" />
            </CardContent>
          </Card>
        </div>

        {/* Right Column */}
        <div className="flex flex-col gap-6">
          {/* IM Section */}
          <Card className="border-border bg-card">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
                <div className="flex h-7 w-7 items-center justify-center rounded-md" style={{ backgroundColor: "hsl(32 85% 48% / 0.1)" }}>
                  <Layers className="h-4 w-4" style={{ color: "hsl(32 85% 48%)" }} aria-hidden="true" />
                </div>
                Иммобилизационный слой (IM)
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <TextField label="ID IM" value={im.im_id} onChange={(v) => updateIm("im_id", v)} placeholder="IM001" />
                <TextField label="Название" value={im.im_name} onChange={(v) => updateIm("im_name", v)} placeholder="SAM-Au" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="pH мин" value={im.ph_min} onChange={(v) => updateIm("ph_min", v)} min={2} max={10} step={0.1} />
                <NumberField label="pH макс" value={im.ph_max} onChange={(v) => updateIm("ph_max", v)} min={2} max={10} step={0.1} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="T мин" value={im.t_min} onChange={(v) => updateIm("t_min", v)} min={4} max={120} unit="C" />
                <NumberField label="T макс" value={im.t_max} onChange={(v) => updateIm("t_max", v)} min={4} max={120} unit="C" />
              </div>
              <NumberField label="Модуль Юнга" value={im.young_modulus} onChange={(v) => updateIm("young_modulus", v)} min={0} max={1000} unit="GPa" />
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <Label className="text-xs font-medium text-muted-foreground">Адгезия</Label>
                  <Select value={im.adhesion} onValueChange={(v) => updateIm("adhesion", v)}>
                    <SelectTrigger className="h-10 bg-card text-foreground">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="слабая">Слабая</SelectItem>
                      <SelectItem value="хорошая">Хорошая</SelectItem>
                      <SelectItem value="отличная">Отличная</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label className="text-xs font-medium text-muted-foreground">Растворимость</Label>
                  <Select value={im.solubility} onValueChange={(v) => updateIm("solubility", v)}>
                    <SelectTrigger className="h-10 bg-card text-foreground">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="водорастворимый">Низкая</SelectItem>
                      <SelectItem value="органический">Средняя</SelectItem>
                      <SelectItem value="нерастворимый">Высокая</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <NumberField label="Коэффициент потерь" value={im.loss_coefficient} onChange={(v) => updateIm("loss_coefficient", v)} min={0} max={1} step={0.01} />
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="Воспроизводимость" value={im.reproducibility} onChange={(v) => updateIm("reproducibility", v)} min={0} max={100} unit="%" />
                <NumberField label="Время отклика" value={im.response_time} onChange={(v) => updateIm("response_time", v)} min={0} max={3600} unit="s" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="Stability" value={im.stability} onChange={(v) => updateIm("stability", v)} min={0} max={365} unit="days" />
                <NumberField label="Durability" value={im.durability} onChange={(v) => updateIm("durability", v)} min={0} max={100000} unit="h" />
              </div>
              <NumberField label="Энергопотребление" value={im.power_consumption} onChange={(v) => updateIm("power_consumption", v)} min={0} max={1000} unit="mW" />
            </CardContent>
          </Card>

          <Separator />

          {/* MEM Section */}
          <Card className="border-border bg-card">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
                <div className="flex h-7 w-7 items-center justify-center rounded-md" style={{ backgroundColor: "hsl(280 60% 55% / 0.1)" }}>
                  <Cpu className="h-4 w-4" style={{ color: "hsl(280 60% 55%)" }} aria-hidden="true" />
                </div>
                Мемристивный слой (MEM)
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <TextField label="ID MEM" value={mem.mem_id} onChange={(v) => updateMem("mem_id", v)} placeholder="MEM001" />
                <TextField label="Название" value={mem.mem_name} onChange={(v) => updateMem("mem_name", v)} placeholder="Мемристор TiO2" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="pH мин" value={mem.ph_min} onChange={(v) => updateMem("ph_min", v)} min={2} max={10} step={0.1} />
                <NumberField label="pH макс" value={mem.ph_max} onChange={(v) => updateMem("ph_max", v)} min={2} max={10} step={0.1} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="T мин" value={mem.t_min} onChange={(v) => updateMem("t_min", v)} min={5} max={120} unit="C" />
                <NumberField label="T макс" value={mem.t_max} onChange={(v) => updateMem("t_max", v)} min={5} max={120} unit="C" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <NumberField label="DR мин" value={mem.dr_min} onChange={(v) => updateMem("dr_min", v)} min={1e-7} max={1e11} step={0.0001} unit="pM" />
                <NumberField label="DR макс" value={mem.dr_max} onChange={(v) => updateMem("dr_max", v)} min={1e-7} max={1e11} step={0.0001} unit="pM" />
              </div>
              <NumberField label="Модуль Юнга" value={mem.young_modulus} onChange={(v) => updateMem("young_modulus", v)} min={0} max={1000} unit="GPa" />
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <NumberField label="Чувствительность" value={mem.sensitivity} onChange={(v) => updateMem("sensitivity", v)} min={0} max={1000} unit="mV/dec" />
                <NumberField label="Воспроизводимость" value={mem.reproducibility} onChange={(v) => updateMem("reproducibility", v)} min={0} max={100} unit="%" />
                <NumberField label="Время отклика" value={mem.response_time} onChange={(v) => updateMem("response_time", v)} min={0} max={3600} unit="s" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <NumberField label="Стабильность" value={mem.stability} onChange={(v) => updateMem("stability", v)} min={0} max={365} unit="days" />
                <NumberField label="LOD" value={mem.lod} onChange={(v) => updateMem("lod", v)} min={0} max={100000} unit="nM" />
                <NumberField label="Долговечность" value={mem.durability} onChange={(v) => updateMem("durability", v)} min={0} max={100000} unit="h" />
              </div>
              <NumberField label="Энергопотребление" value={mem.power_consumption} onChange={(v) => updateMem("power_consumption", v)} min={0} max={1000} unit="mW" />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Button onClick={handleSave} disabled={saving} className="h-11 gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
          <Save className="h-4 w-4" aria-hidden="true" />
          {saving ? "Сохранение..." : "Сохранить паспорт"}
        </Button>
        <Button onClick={handleClear} variant="secondary" disabled={saving} className="h-11 gap-2">
          <Trash2 className="h-4 w-4" aria-hidden="true" />
          Очистить форму
        </Button>
        <Button onClick={() => setLoadDialog(true)} disabled={saving} className="h-11 gap-2 bg-accent text-accent-foreground hover:bg-accent/90">
          <FolderOpen className="h-4 w-4" aria-hidden="true" />
          Загрузить паспорт
        </Button>
      </div>

      {/* Duplicate Dialog */}
      <Dialog open={duplicateDialog.open} onOpenChange={(open) => setDuplicateDialog({ ...duplicateDialog, open })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-foreground">Обнаружены дубликаты</DialogTitle>
            <DialogDescription>
              Следующие записи уже существуют в базе данных. Создание дубликатов запрещено.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-2 rounded-lg border border-border bg-muted p-3">
            {duplicateDialog.duplicates.map((d, i) => (
              <p key={i} className="text-sm font-medium text-foreground">
                {d}
              </p>
            ))}
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setDuplicateDialog({ open: false, duplicates: [] })}>
              Закрыть
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Load Dialog */}
      <Dialog open={loadDialog} onOpenChange={setLoadDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-foreground">Загрузка данных паспорта</DialogTitle>
            <DialogDescription>
              Выберите тип слоя и введите его ID для загрузки из базы данных.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label className="text-xs font-medium text-muted-foreground">Тип слоя</Label>
              <Select value={loadType} onValueChange={setLoadType}>
                <SelectTrigger className="bg-card text-foreground">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="analyte">Аналит (TA)</SelectItem>
                  <SelectItem value="bre">Биораспознающий (BRE)</SelectItem>
                  <SelectItem value="im">Иммобилизационный (IM)</SelectItem>
                  <SelectItem value="mem">Мемристивный (MEM)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label className="text-xs font-medium text-muted-foreground">ID слоя</Label>
              <Input
                placeholder="напр. TA001, BRE001"
                value={loadId}
                onChange={(e) => setLoadId(e.target.value)}
                className="bg-card text-foreground"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setLoadDialog(false)}>
              Отмена
            </Button>
            <Button onClick={handleLoad} className="bg-primary text-primary-foreground hover:bg-primary/90">
              Загрузить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
