import React, { useState, useRef, useEffect } from "react"
import { useParams, Link } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  ArrowLeft,
  Download,
  Copy,
  Check,
  RotateCcw,
  Sparkles,
  Flame,
  Coins,
  Cpu,
  Trash2,
  AlertCircle,
  Video,
  Clock,
  PlusCircle,
  Scissors,
  Play,
  Pause,
  Volume2,
  ChevronDown,
  ChevronUp
} from "lucide-react"
import { api } from "@/lib/api"
import { Clip } from "@/types"
import { formatDuration } from "@/lib/utils"

export const JobDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  // Manual Clip State - Default open embedded in page
  const [showManualSection, setShowManualSection] = useState<boolean>(true)
  const [showPipelineHistory, setShowPipelineHistory] = useState<boolean>(true)
  const [showClipsSection, setShowClipsSection] = useState<boolean>(true)
  const [manualStart, setManualStart] = useState<number>(0)
  const [manualEnd, setManualEnd] = useState<number>(30)
  const [currentTime, setCurrentTime] = useState<number>(0)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const videoPreviewRef = useRef<HTMLVideoElement | null>(null)
  const phoneVideoRef = useRef<HTMLVideoElement | null>(null)

  const [manualTitle, setManualTitle] = useState<string>("Highlight Kustom")
  const [manualLayout, setManualLayout] = useState<"focus" | "split" | "header_banner" | "header_white" | "footer_banner" | "top_bottom_banner" | "fit_center_black" | "fit_center_white">("focus")
  const [manualHeaderText, setManualHeaderText] = useState<string>("HIGHLIGHT PILIHAN 🔥")
  const [manualSubtitlePreset, setManualSubtitlePreset] = useState<"bold_yellow" | "classic" | "neon">("bold_yellow")
  const [manualFontSize, setManualFontSize] = useState<number>(48)
  const [manualFontFamily, setManualFontFamily] = useState<string>("Arial")
  const [manualFontColor, setManualFontColor] = useState<string>("#FFFFFF")
  const [renderProgress, setRenderProgress] = useState<number>(0)

  const { data: job, isLoading, error } = useQuery({
    queryKey: ["job", id],
    queryFn: () => api.getJob(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const current = query.state.data
      // Poll every 2 seconds if still in processing
      if (current && current.status !== "done" && current.status !== "failed") {
        return 2000
      }
      return false
    },
  })

  const retryMutation = useMutation({
    mutationFn: () => api.retryJob(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", id] })
    },
  })

  const deleteClipMutation = useMutation({
    mutationFn: (clipId: string) => api.deleteClip(clipId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", id] })
    },
  })

  const createManualClipMutation = useMutation({
    mutationFn: (data: {
      start_sec: number
      end_sec: number
      title?: string
      layout?: string
      custom_header_text?: string
      subtitle_preset?: string
      font_size?: number
      font_family?: string
      font_color?: string
    }) => api.createManualClip(id!, data),
    onSuccess: () => {
      setRenderProgress(100)
      queryClient.invalidateQueries({ queryKey: ["job", id] })
    },
  })

  // Timer for smooth progress simulation during cutting & rendering
  useEffect(() => {
    let interval: any = null
    if (createManualClipMutation.isPending) {
      setRenderProgress(10)
      interval = setInterval(() => {
        setRenderProgress((prev) => {
          if (prev >= 92) return prev
          // Smooth progressive increment
          const step = Math.max(1, Math.floor((95 - prev) / 6))
          return Math.min(94, prev + step)
        })
      }, 700)
    } else {
      if (renderProgress > 0) {
        setRenderProgress(100)
        const timeout = setTimeout(() => setRenderProgress(0), 1200)
        return () => clearTimeout(timeout)
      }
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [createManualClipMutation.isPending])

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  if (isLoading) {
    return (
      <div className="container max-w-6xl mx-auto px-4 py-12 flex justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-purple-600 border-t-transparent" />
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="container max-w-4xl mx-auto px-4 py-12 text-center space-y-4">
        <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
        <h2 className="text-xl font-bold">Job Tidak Ditemukan</h2>
        <p className="text-sm text-muted-foreground">{(error as Error)?.message || "Job tidak tersedia atau telah dihapus."}</p>
        <Link to="/dashboard" className="inline-flex items-center text-sm font-semibold text-purple-600 hover:underline">
          <ArrowLeft className="h-4 w-4 mr-1" /> Kembali ke Dashboard
        </Link>
      </div>
    )
  }

  const clips: Clip[] = job.clips || []
  const isDone = job.status === "done"
  const isFailed = job.status === "failed"

  return (
    <div className="container max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Back button & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link
            to="/dashboard"
            className="inline-flex items-center text-xs font-semibold text-muted-foreground hover:text-foreground transition mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5 mr-1" />
            Kembali ke Dashboard
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            {job.title || "Detail Video Clipper"}
          </h1>
          <p className="text-xs text-muted-foreground">
            ID: <span className="font-mono">{job.id}</span> • Status: <span className="font-semibold uppercase">{job.status}</span>
          </p>
        </div>

        {isFailed && (
          <button
            onClick={() => retryMutation.mutate()}
            disabled={retryMutation.isPending}
            className="inline-flex items-center space-x-2 rounded-xl bg-purple-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-purple-700 transition"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Lanjutkan Tahap Gagal</span>
          </button>
        )}
      </div>

      {/* Real-time Status Card if processing */}
      {!isDone && (
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between text-sm font-semibold">
            <span className="flex items-center space-x-2">
              <Sparkles className="h-4 w-4 text-purple-500 animate-spin" />
              <span>Pipeline Sedang Berjalan: {job.status}</span>
            </span>
            <div className="flex items-center space-x-3 text-xs">
              {job.estimated_remaining_sec && job.estimated_remaining_sec > 0 && (
                <span className="flex items-center space-x-1 text-muted-foreground bg-muted/60 px-2.5 py-1 rounded-lg">
                  <Clock className="h-3.5 w-3.5 text-purple-400" />
                  <span>Estimasi selesai: ~{Math.ceil(job.estimated_remaining_sec / 60)} menit ({job.estimated_remaining_sec}s)</span>
                </span>
              )}
              <span className="font-mono text-purple-400 font-bold text-sm">{job.progress}%</span>
            </div>
          </div>

          <div className="h-2.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                isFailed ? "bg-red-500" : "bg-purple-600 animate-pulse"
              }`}
              style={{ width: `${job.progress}%` }}
            />
          </div>

          {/* Live Progress Info (Bytes downloaded, Total, Speed, ETA) */}
          {job.live_status_message && (
            <div className="flex items-center space-x-2 rounded-xl bg-purple-500/10 px-3.5 py-2.5 text-xs text-purple-400 font-mono border border-purple-500/20">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
              </span>
              <span>{job.live_status_message}</span>
            </div>
          )}

          {job.error && (
            <div className="p-3 rounded-lg bg-red-500/10 text-red-500 text-xs border border-red-500/20">
              <strong>Error ({job.failed_step}):</strong> {job.error}
            </div>
          )}
        </div>
      )}

      {/* Job Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-border bg-card p-4 space-y-1">
          <span className="text-xs text-muted-foreground flex items-center space-x-1">
            <Video className="h-3.5 w-3.5" />
            <span>Durasi Video</span>
          </span>
          <p className="text-base font-bold">{job.duration_sec ? formatDuration(job.duration_sec) : "-"}</p>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 space-y-1">
          <span className="text-xs text-muted-foreground flex items-center space-x-1">
            <Sparkles className="h-3.5 w-3.5 text-purple-500" />
            <span>Klip Dihasilkan</span>
          </span>
          <p className="text-base font-bold">{clips.length} Klip 9:16</p>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 space-y-1">
          <span className="text-xs text-muted-foreground flex items-center space-x-1">
            <Cpu className="h-3.5 w-3.5 text-indigo-500" />
            <span>Total Token LLM</span>
          </span>
          <p className="text-base font-bold">{job.total_tokens?.toLocaleString() || 0} tokens</p>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 space-y-1">
          <span className="text-xs text-muted-foreground flex items-center space-x-1">
            <Coins className="h-3.5 w-3.5 text-amber-500" />
            <span>Estimasi Biaya AI</span>
          </span>
          <p className="text-base font-bold">${job.estimated_cost_usd?.toFixed(5) || "0.00000"}</p>
        </div>
      </div>

      {/* History & Transkrip Collapsible Section */}
      <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-sm">
        <button
          type="button"
          onClick={() => setShowPipelineHistory((prev) => !prev)}
          className="w-full flex items-center justify-between p-5 text-left hover:bg-muted/30 transition cursor-pointer"
        >
          <div className="flex items-center space-x-2">
            <Sparkles className="h-4 w-4 text-purple-500" />
            <h3 className="text-sm font-bold text-foreground">Riwayat Tahapan Pipeline & Transkrip Whisper</h3>
          </div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-muted-foreground">
            <span>{showPipelineHistory ? "Tutup" : "Buka"}</span>
            {showPipelineHistory ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </div>
        </button>

        {showPipelineHistory && (
          <div className="p-5 pt-0 border-t border-border/50 grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Step History */}
            <div className="space-y-3 pt-4">
              <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Tahapan Eksekusi</h4>
              <div className="space-y-2">
                {job.step_history && job.step_history.length > 0 ? (
                  job.step_history.map((s, sIdx) => (
                    <div key={sIdx} className="flex items-center justify-between text-xs p-2.5 rounded-xl bg-muted/40 border border-border/50">
                      <div className="flex items-center space-x-2">
                        <span className={`w-2 h-2 rounded-full ${
                          s.status === 'success' ? 'bg-green-500' : (s.status === 'failed' ? 'bg-red-500' : 'bg-gray-400')
                        }`} />
                        <span className="font-medium text-foreground">{s.name}</span>
                      </div>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                        s.status === 'success' ? 'text-green-500 bg-green-500/10' : (s.status === 'failed' ? 'text-red-500 bg-red-500/10' : 'text-muted-foreground')
                      }`}>
                        {s.status === 'success' ? 'Berhasil' : (s.status === 'failed' ? 'Gagal' : 'Menunggu')}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground">Menunggu proses...</p>
                )}
              </div>
            </div>

            {/* Transcript Kata-kata */}
            <div className="space-y-3 pt-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Transkrip Teks Whisper</h4>
                {job.transcript_preview && (
                  <span className="text-[10px] text-green-500 bg-green-500/10 px-2 py-0.5 rounded font-mono">
                    Teks Terdeteksi
                  </span>
                )}
              </div>
              <div className="max-h-56 overflow-y-auto rounded-xl border border-border bg-background p-3 text-xs font-mono text-muted-foreground whitespace-pre-wrap leading-relaxed">
                {job.transcript_preview || "Teks transkrip belum tersedia atau sedang diekstrak..."}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Clips Section - Collapsible (Default Open) */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-border/60 pb-3">
          <button
            type="button"
            onClick={() => setShowClipsSection((prev) => !prev)}
            className="flex items-center space-x-2.5 text-left hover:opacity-80 transition cursor-pointer"
          >
            <h2 className="text-xl font-bold tracking-tight">Klip 9:16 Siap Publikasi ({clips.length})</h2>
            <span className="p-1 rounded-md bg-muted text-muted-foreground">
              {showClipsSection ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </span>
          </button>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => retryMutation.mutate()}
              disabled={retryMutation.isPending}
              className="inline-flex items-center space-x-1.5 rounded-xl border border-border bg-card px-3.5 py-2 text-xs font-semibold text-foreground hover:bg-muted transition"
              title="Generate ulang seluruh klip secara otomatis"
            >
              <RotateCcw className="h-3.5 w-3.5 text-purple-500" />
              <span>Generate Ulang (AI)</span>
            </button>

            <button
              onClick={() => {
                setShowManualSection((prev) => !prev)
              }}
              className="inline-flex items-center space-x-1.5 rounded-xl bg-purple-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-purple-700 transition"
              title="Tampilkan / sembunyikan editor timeline manual"
            >
              <Scissors className="h-3.5 w-3.5" />
              <span>{showManualSection ? "Sembunyikan Editor Timeline" : "Buka Editor Timeline (CapCut)"}</span>
            </button>
          </div>
        </div>

        {/* Section Potong Manual - CapCut Style Visual Timeline Trimmer Embedded in Page */}
        {showManualSection && (
          <div className="rounded-2xl border-2 border-purple-500/30 bg-card p-6 shadow-xl space-y-6">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-500">
                  <Scissors className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-foreground">Timeline Video Clipper (CapCut Style)</h3>
                  <p className="text-xs text-muted-foreground">
                    Tentukan range durasi pemotong visual di timeline & pratinjau simulasi 9:16 di layar HP
                  </p>
                </div>
              </div>
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                Mode Editor Manual
              </span>
            </div>

            {/* Main Editor Grid: Left Video & Timeline, Right Phone Mockup 9:16 Preview */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column (8 cols): Video Source + Timeline Range Scrubber */}
              <div className="lg:col-span-7 space-y-4">
                {/* Video Player Source with Play/Pause & Controls */}
                <div className="relative aspect-video rounded-xl bg-black overflow-hidden flex items-center justify-center border border-border shadow-inner">
                  <video
                    ref={videoPreviewRef}
                    src={api.getJobSourceVideoUrl(job.id)}
                    className="w-full h-full object-contain"
                    onTimeUpdate={(e) => {
                      const t = e.currentTarget.currentTime
                      setCurrentTime(t)
                      if (phoneVideoRef.current && Math.abs(phoneVideoRef.current.currentTime - t) > 0.3) {
                        phoneVideoRef.current.currentTime = t
                      }
                      if (isPlaying && t >= manualEnd) {
                        e.currentTarget.currentTime = manualStart
                        if (phoneVideoRef.current) phoneVideoRef.current.currentTime = manualStart
                      }
                    }}
                    onPlay={() => {
                      setIsPlaying(true)
                      if (phoneVideoRef.current) phoneVideoRef.current.play()
                    }}
                    onPause={() => {
                      setIsPlaying(false)
                      if (phoneVideoRef.current) phoneVideoRef.current.pause()
                    }}
                  />
                  {/* Overlay Controls */}
                  <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between bg-black/70 backdrop-blur-md px-3 py-2 rounded-xl border border-white/10 text-xs text-white">
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => {
                          if (videoPreviewRef.current) {
                            if (isPlaying) {
                              videoPreviewRef.current.pause()
                            } else {
                              if (currentTime < manualStart || currentTime >= manualEnd) {
                                videoPreviewRef.current.currentTime = manualStart
                              }
                              videoPreviewRef.current.play()
                            }
                          }
                        }}
                        className="p-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white transition"
                      >
                        {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 fill-white" />}
                      </button>
                      <span className="font-mono text-xs">{formatDuration(currentTime)} / {formatDuration(job.duration_sec || 0)}</span>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] font-mono text-purple-300 bg-purple-500/10 px-2.5 py-1 rounded-lg border border-purple-500/20">
                      <span>Rentang: {formatDuration(manualStart)} - {formatDuration(manualEnd)}</span>
                    </div>
                  </div>
                </div>

                {/* CapCut-style Visual Track Range Scrubber */}
                <div className="space-y-2 rounded-xl bg-muted/30 p-3.5 border border-border">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-purple-400">
                      Range Klip: <strong className="font-mono text-foreground">{formatDuration(manualStart)} ({manualStart.toFixed(1)}s)</strong> → <strong className="font-mono text-foreground">{formatDuration(manualEnd)} ({manualEnd.toFixed(1)}s)</strong>
                    </span>
                    <span className="font-bold text-amber-400 bg-amber-400/10 px-2.5 py-1 rounded-md text-xs border border-amber-400/20">
                      Durasi Terpilih: {Math.max(0, manualEnd - manualStart).toFixed(1)}s
                    </span>
                  </div>

                  {/* Range Track Bar */}
                  <div className="relative h-16 bg-muted rounded-xl p-2 border border-border flex items-center overflow-hidden select-none">
                    {/* Simulated visual waveform / video frames bar */}
                    <div className="absolute inset-0 opacity-20 flex items-center justify-between px-1 pointer-events-none">
                      {Array.from({ length: 48 }).map((_, i) => (
                        <div
                          key={i}
                          className="w-1 bg-foreground rounded-full"
                          style={{ height: `${20 + (i % 6) * 14}%` }}
                        />
                      ))}
                    </div>

                    {/* Highlighted Selected Range Zone (CapCut Yellow/Purple Box) */}
                    {job.duration_sec && job.duration_sec > 0 && (
                      <div
                        className="absolute top-1 bottom-1 bg-purple-500/35 border-2 border-purple-500 rounded-lg pointer-events-none transition-all duration-75 shadow-[0_0_15px_rgba(168,85,247,0.35)]"
                        style={{
                          left: `${(manualStart / job.duration_sec) * 100}%`,
                          width: `${Math.max(2, ((manualEnd - manualStart) / job.duration_sec) * 100)}%`,
                        }}
                      >
                        <div className="absolute top-1 left-1.5 text-[9px] font-bold text-white bg-purple-600 px-1 rounded">
                          {Math.max(0, manualEnd - manualStart).toFixed(1)}s
                        </div>
                      </div>
                    )}

                    {/* Dual Sliders for Start & End */}
                    <input
                      type="range"
                      min={0}
                      max={job.duration_sec || 100}
                      step={0.5}
                      value={manualStart}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value)
                        if (val < manualEnd) {
                          setManualStart(val)
                          if (videoPreviewRef.current) {
                            videoPreviewRef.current.currentTime = val
                          }
                        }
                      }}
                      className="absolute inset-x-0 w-full h-10 opacity-0 cursor-ew-resize z-20 pointer-events-auto"
                      title="Geser titik awal klip"
                    />
                    <input
                      type="range"
                      min={0}
                      max={job.duration_sec || 100}
                      step={0.5}
                      value={manualEnd}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value)
                        if (val > manualStart) {
                          setManualEnd(val)
                          if (videoPreviewRef.current) {
                            videoPreviewRef.current.currentTime = val
                          }
                        }
                      }}
                      className="absolute inset-x-0 w-full h-10 opacity-0 cursor-ew-resize z-20 pointer-events-auto"
                      title="Geser titik akhir klip"
                    />

                    {/* Playhead Marker */}
                    {job.duration_sec && job.duration_sec > 0 && (
                      <div
                        className="absolute top-0 bottom-0 w-0.5 bg-red-500 pointer-events-none z-10"
                        style={{ left: `${(currentTime / job.duration_sec) * 100}%` }}
                      >
                        <div className="w-2.5 h-2.5 -ml-[4px] bg-red-500 rounded-full shadow" />
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                    <span>Geser slider kiri & kanan untuk menentukan detik potong</span>
                    <span>Total Video: {formatDuration(job.duration_sec || 0)}</span>
                  </div>
                </div>

                {/* Form Settings & Metadata */}
                <div className="space-y-4 text-xs pt-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-muted-foreground uppercase">Judul Klip</label>
                    <input
                      type="text"
                      value={manualTitle}
                      onChange={(e) => setManualTitle(e.target.value)}
                      placeholder="Contoh: Momen Kocak Streamer"
                      className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm focus:border-purple-600 focus:outline-none"
                    />
                  </div>

                  {/* Layout Buttons */}
                  <div className="space-y-1.5">
                    <label className="font-semibold text-muted-foreground uppercase">Layout & Template Frame Clipper</label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                      {[
                        { id: "focus", name: "Fokus Wajah 9:16" },
                        { id: "split", name: "Split Screen" },
                        { id: "header_banner", name: "Banner Atas (Hitam)" },
                        { id: "header_white", name: "Banner Atas (Putih)" },
                        { id: "footer_banner", name: "Banner Bawah (Kuning)" },
                        { id: "top_bottom_banner", name: "Atas & Bawah" },
                        { id: "fit_center_black", name: "Tengah + Frame Hitam" },
                        { id: "fit_center_white", name: "Tengah + Frame Putih" },
                      ].map((l) => (
                        <button
                          key={l.id}
                          type="button"
                          onClick={() => setManualLayout(l.id as any)}
                          className={`py-2 px-2 rounded-lg border text-center transition font-semibold text-[11px] ${
                            manualLayout === l.id
                              ? "border-purple-600 bg-purple-600/10 text-purple-500"
                              : "border-border text-muted-foreground hover:bg-muted"
                          }`}
                        >
                          {l.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Custom Text Banner */}
                  {(manualLayout !== "focus" && manualLayout !== "split") && (
                    <div className="space-y-3 rounded-xl border border-purple-500/20 bg-purple-500/5 p-3.5">
                      <div className="space-y-1">
                        <label className="font-semibold text-purple-400 uppercase text-[11px]">
                          Tulisan Kustom Frame ({manualLayout.includes("footer") ? "Bawah" : "Atas / Tengah"})
                        </label>
                        <input
                          type="text"
                          value={manualHeaderText}
                          onChange={(e) => setManualHeaderText(e.target.value)}
                          placeholder="Contoh: REAKSI OURAA KETEMU... / KOCAK BANGET!"
                          className="w-full rounded-xl border border-purple-500/30 bg-background px-3.5 py-2 text-sm focus:border-purple-600 focus:outline-none"
                        />
                      </div>

                      {/* Font Styling Controls: Font Size, Font Family, Font Color */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-[11px] text-muted-foreground font-semibold">
                            <span>Ukuran Font</span>
                            <span className="font-mono text-purple-400">{manualFontSize}px</span>
                          </div>
                          <input
                            type="range"
                            min="24"
                            max="84"
                            step="2"
                            value={manualFontSize}
                            onChange={(e) => setManualFontSize(Number(e.target.value))}
                            className="w-full accent-purple-600 cursor-pointer h-1.5 bg-muted rounded-lg"
                          />
                        </div>

                        <div className="space-y-1">
                          <label className="text-[11px] text-muted-foreground font-semibold block">Jenis Font</label>
                          <select
                            value={manualFontFamily}
                            onChange={(e) => setManualFontFamily(e.target.value)}
                            className="w-full rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs focus:border-purple-600 focus:outline-none"
                          >
                            <option value="Arial">Arial (Standar)</option>
                            <option value="Impact">Impact (Bold Meme)</option>
                            <option value="Trebuchet MS">Trebuchet (Modern)</option>
                            <option value="Verdana">Verdana (Clean)</option>
                            <option value="Courier New">Courier (Monospace)</option>
                          </select>
                        </div>

                        <div className="space-y-1">
                          <label className="text-[11px] text-muted-foreground font-semibold block">Warna Teks</label>
                          <div className="flex items-center space-x-1.5">
                            {["#FFFFFF", "#FACC15", "#EF4444", "#38BDF8", "#000000"].map((c) => (
                              <button
                                key={c}
                                type="button"
                                onClick={() => setManualFontColor(c)}
                                className={`w-6 h-6 rounded-full border transition ${
                                  manualFontColor === c ? "ring-2 ring-purple-600 scale-110" : "border-border"
                                }`}
                                style={{ backgroundColor: c }}
                                title={c}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Subtitle Preset */}
                  <div className="space-y-1">
                    <label className="font-semibold text-muted-foreground uppercase">Gaya Subtitle Animasi</label>
                    <select
                      value={manualSubtitlePreset}
                      onChange={(e) => setManualSubtitlePreset(e.target.value as any)}
                      className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm focus:border-purple-600 focus:outline-none"
                    >
                      <option value="bold_yellow">TikTok Bold (Kuning Highlight)</option>
                      <option value="classic">Classic Clean (Cyan Highlight)</option>
                      <option value="neon">Neon High Energy (Magenta Highlight)</option>
                    </select>
                  </div>

                  <div className="pt-2">
                    <button
                      type="button"
                      disabled={createManualClipMutation.isPending || manualEnd <= manualStart}
                      onClick={() => {
                        createManualClipMutation.mutate({
                          start_sec: manualStart,
                          end_sec: manualEnd,
                          title: manualTitle,
                          layout: manualLayout,
                          custom_header_text: manualHeaderText,
                          subtitle_preset: manualSubtitlePreset,
                          font_size: manualFontSize,
                          font_family: manualFontFamily,
                          font_color: manualFontColor,
                        })
                      }}
                      className="relative w-full overflow-hidden flex items-center justify-center space-x-2 py-3.5 rounded-xl bg-purple-600 text-sm font-bold text-white shadow-lg hover:bg-purple-700 transition disabled:opacity-75 disabled:cursor-not-allowed"
                    >
                      {/* Active Progress Bar Fill Animation inside Button */}
                      {createManualClipMutation.isPending && (
                        <div
                          className="absolute inset-0 bg-purple-800 transition-all duration-300 ease-out"
                          style={{ width: `${renderProgress}%` }}
                        />
                      )}

                      <div className="relative z-10 flex items-center space-x-2">
                        {createManualClipMutation.isPending ? (
                          <>
                            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                            <span>Sedang Memotong & Merender... {renderProgress}%</span>
                          </>
                        ) : (
                          <>
                            <Scissors className="h-4 w-4" />
                            <span>Potong & Simpan Klip Ini</span>
                          </>
                        )}
                      </div>
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Column (5 cols): Real-Time Live Phone Video Simulation (9:16 Mockup) */}
              <div className="lg:col-span-5 flex flex-col items-center justify-center p-4 bg-muted/20 rounded-2xl border border-border">
                <div className="flex items-center space-x-1.5 mb-3">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
                  </span>
                  <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    Simulasi Live Layar HP (9:16)
                  </p>
                </div>

                {/* Smartphone Device Frame Mockup */}
                <div className={`relative w-[240px] h-[480px] rounded-[36px] border-[6px] border-zinc-800 shadow-2xl overflow-hidden flex flex-col items-center ring-1 ring-white/10 ${
                  manualLayout === "header_white" || manualLayout === "fit_center_white" ? "bg-white" : "bg-black"
                }`}>
                  {/* Dynamic Island / Speaker Notch */}
                  <div className="absolute top-2 w-20 h-4 bg-zinc-900 rounded-full z-30 flex items-center justify-center">
                    <div className="w-2 h-2 rounded-full bg-zinc-950 mr-2" />
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-900/50" />
                  </div>

                  {/* Top Custom Banner if layout is header, top_bottom, or fit_center */}
                  {manualLayout === "header_banner" && (
                    <div
                      className="w-full bg-black text-center py-2 px-2 font-extrabold uppercase border-b border-white/10 tracking-tight z-20"
                      style={{
                        fontFamily: manualFontFamily,
                        color: manualFontColor,
                        fontSize: `${Math.round(manualFontSize * 0.22)}px`
                      }}
                    >
                      {manualHeaderText || "HIGHLIGHT MOMENT"}
                    </div>
                  )}

                  {manualLayout === "header_white" && (
                    <div
                      className="w-full bg-white text-center py-2 px-2 font-extrabold uppercase border-b border-zinc-300 tracking-tight z-20"
                      style={{
                        fontFamily: manualFontFamily,
                        color: manualFontColor === "#FFFFFF" ? "#000000" : manualFontColor,
                        fontSize: `${Math.round(manualFontSize * 0.22)}px`
                      }}
                    >
                      {manualHeaderText || "HIGHLIGHT MOMENT"}
                    </div>
                  )}

                  {manualLayout === "top_bottom_banner" && (
                    <div
                      className="w-full bg-black text-center py-1.5 px-2 font-extrabold uppercase border-b border-white/10 tracking-tight z-20"
                      style={{
                        fontFamily: manualFontFamily,
                        color: manualFontColor,
                        fontSize: `${Math.round(manualFontSize * 0.20)}px`
                      }}
                    >
                      {manualHeaderText || "HIGHLIGHT MOMENT"}
                    </div>
                  )}

                  {manualLayout === "fit_center_black" && (
                    <div
                      className="w-full bg-black text-center py-3 px-2 font-extrabold uppercase tracking-tight z-20"
                      style={{
                        fontFamily: manualFontFamily,
                        color: manualFontColor,
                        fontSize: `${Math.round(manualFontSize * 0.22)}px`
                      }}
                    >
                      {manualHeaderText || "HIGHLIGHT MOMENT"}
                    </div>
                  )}

                  {manualLayout === "fit_center_white" && (
                    <div
                      className="w-full bg-white text-center py-3 px-2 font-extrabold uppercase tracking-tight z-20"
                      style={{
                        fontFamily: manualFontFamily,
                        color: manualFontColor === "#FFFFFF" ? "#000000" : manualFontColor,
                        fontSize: `${Math.round(manualFontSize * 0.23)}px`
                      }}
                    >
                      {manualHeaderText || "HIGHLIGHT MOMENT"}
                    </div>
                  )}

                  {/* Main Video View inside Phone with LIVE PLAYING VIDEO */}
                  <div className={`relative flex-1 w-full flex flex-col items-center justify-center overflow-hidden ${
                    manualLayout === "fit_center_white" ? "bg-white" : "bg-black"
                  }`}>
                    {/* Live Synchronized Video inside Phone */}
                    <div className={`w-full flex items-center justify-center overflow-hidden ${
                      manualLayout.startsWith("fit_center")
                        ? "h-[50%] bg-black shadow-md border-y border-white/10"
                        : "h-full"
                    }`}>
                      <video
                        ref={phoneVideoRef}
                        src={api.getJobSourceVideoUrl(job.id)}
                        className={`w-full h-full ${
                          manualLayout.startsWith("fit_center") ? "object-contain" : "object-cover"
                        }`}
                        muted
                        playsInline
                      />
                    </div>

                    {/* TikTok Subtitle Simulation Overlay */}
                    <div className="absolute bottom-6 inset-x-2 text-center pointer-events-none z-20">
                      <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-extrabold shadow-md ${
                        manualSubtitlePreset === "bold_yellow"
                          ? "bg-black/75 text-yellow-400"
                          : (manualSubtitlePreset === "neon" ? "bg-black/75 text-pink-400" : "bg-black/75 text-cyan-300")
                      }`}>
                        Teks Subtitle TikTok
                      </span>
                    </div>

                    {/* TikTok UI Icons Simulation */}
                    <div className="absolute right-2 bottom-12 flex flex-col items-center space-y-3 pointer-events-none opacity-80 text-white z-20">
                      <div className="w-6 h-6 rounded-full bg-red-500/80 flex items-center justify-center text-[9px]">❤️</div>
                      <span className="text-[8px] font-bold">12.5K</span>
                      <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-[9px]">💬</div>
                      <span className="text-[8px] font-bold">342</span>
                      <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-[9px]">↗️</div>
                    </div>
                  </div>

                  {/* Bottom Custom Banner if layout is footer, top_bottom, or fit_center */}
                  {manualLayout === "footer_banner" && (
                    <div
                      className="w-full bg-black text-center py-2 px-2 font-extrabold uppercase border-t border-white/10 tracking-tight z-20"
                      style={{
                        fontFamily: manualFontFamily,
                        color: manualFontColor === "#FFFFFF" ? "#FACC15" : manualFontColor,
                        fontSize: `${Math.round(manualFontSize * 0.22)}px`
                      }}
                    >
                      {manualHeaderText || "HIGHLIGHT MOMENT"}
                    </div>
                  )}

                  {manualLayout === "top_bottom_banner" && (
                    <div
                      className="w-full bg-black text-center py-1.5 px-2 font-extrabold uppercase border-t border-white/10 tracking-tight z-20"
                      style={{
                        fontFamily: manualFontFamily,
                        color: "#FACC15",
                        fontSize: `${Math.round(manualFontSize * 0.19)}px`
                      }}
                    >
                      TONTON SAMPAI HABIS!
                    </div>
                  )}

                  {manualLayout === "fit_center_black" && (
                    <div
                      className="w-full bg-black text-center py-3 px-2 font-extrabold uppercase tracking-tight z-20"
                      style={{
                        fontFamily: manualFontFamily,
                        color: "#FACC15",
                        fontSize: `${Math.round(manualFontSize * 0.20)}px`
                      }}
                    >
                      TONTON SAMPAI HABIS! 🔥
                    </div>
                  )}

                  {manualLayout === "fit_center_white" && (
                    <div
                      className="w-full bg-white text-center py-3 px-2 font-extrabold uppercase tracking-tight z-20"
                      style={{
                        fontFamily: manualFontFamily,
                        color: "#EF4444",
                        fontSize: `${Math.round(manualFontSize * 0.20)}px`
                      }}
                    >
                      TONTON SAMPAI HABIS! 🔥
                    </div>
                  )}

                  {/* Bottom Home Indicator Bar */}
                  <div className="w-20 h-1 bg-zinc-600 rounded-full my-1.5 z-20" />
                </div>

                <p className="text-[10px] text-muted-foreground text-center mt-3 max-w-xs">
                  Video di HP otomatis berputar sinkron saat timeline diputar, memperlihatkan simulasi frame hitam/putih secara nyata.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Clips Grid List (Collapsible with showClipsSection) */}
        {showClipsSection && (
          <>
            {clips.length === 0 ? (
              <div className="text-center py-12 rounded-2xl border border-border bg-card/40 p-6">
                <p className="text-sm text-muted-foreground">
                  {isDone ? "Tidak ada klip yang disimpan untuk job ini." : "Klip akan muncul di sini setelah pipeline rendering selesai..."}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {clips.map((clip, idx) => (
                  <div
                    key={clip.id}
                    className="flex flex-col rounded-2xl border border-border bg-card overflow-hidden shadow-md hover:shadow-lg transition"
                  >
                    {/* 9:16 Vertical Video Player */}
                    <div className="relative aspect-[9/16] bg-black">
                      <video
                        controls
                        preload="metadata"
                        poster={clip.thumbnail_path ? api.getClipThumbnailUrl(clip.id) : undefined}
                        src={clip.file_path ? api.getClipStreamUrl(clip.id) : undefined}
                        className="w-full h-full object-cover"
                      />
                      {/* Viral score badge overlay */}
                      <div className="absolute top-3 left-3 flex items-center space-x-1 bg-black/70 backdrop-blur-md text-amber-400 px-2.5 py-1 rounded-full text-xs font-bold border border-amber-400/30">
                        <Flame className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                        <span>{clip.score.toFixed(1)} / 10</span>
                      </div>

                      {clip.category && (
                        <div className="absolute top-3 right-3 bg-purple-600/80 backdrop-blur-md text-white px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider">
                          {clip.category}
                        </div>
                      )}
                    </div>

                    {/* Clip Content Details */}
                    <div className="p-4 flex-1 flex flex-col justify-between space-y-4">
                      <div className="space-y-3">
                        {/* Title */}
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                              Judul Klip
                            </span>
                            <button
                              onClick={() => copyToClipboard(clip.title || "", `title-${clip.id}`)}
                              className="text-xs text-muted-foreground hover:text-purple-500 transition"
                              title="Salin judul"
                            >
                              {copiedKey === `title-${clip.id}` ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                            </button>
                          </div>
                          <p className="text-sm font-bold text-foreground leading-snug line-clamp-2">
                            {clip.title || `Clip #${idx + 1}`}
                          </p>
                        </div>

                        {/* Caption */}
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                              Caption
                            </span>
                            <button
                              onClick={() => copyToClipboard(clip.caption || "", `cap-${clip.id}`)}
                              className="text-xs text-muted-foreground hover:text-purple-500 transition"
                              title="Salin caption"
                            >
                              {copiedKey === `cap-${clip.id}` ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                            </button>
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-3">
                            {clip.caption || "-"}
                          </p>
                        </div>

                        {/* Hashtags */}
                        {clip.hashtags && clip.hashtags.length > 0 && (
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                                Hashtags
                              </span>
                              <button
                                onClick={() => copyToClipboard(clip.hashtags.join(" "), `tags-${clip.id}`)}
                                className="text-xs text-muted-foreground hover:text-purple-500 transition"
                                title="Salin hashtags"
                              >
                                {copiedKey === `tags-${clip.id}` ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                              </button>
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {clip.hashtags.map((tag, tIdx) => (
                                <span key={tIdx} className="text-[11px] font-medium text-purple-500 bg-purple-500/10 px-1.5 py-0.5 rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Actions: Download & Delete */}
                      <div className="flex items-center space-x-2 pt-2 border-t border-border/60">
                        <a
                          href={api.getClipDownloadUrl(clip.id)}
                          download
                          className="flex-1 flex items-center justify-center space-x-1.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold shadow-sm transition"
                        >
                          <Download className="h-3.5 w-3.5" />
                          <span>Download MP4</span>
                        </a>

                        <button
                          onClick={() => {
                            if (confirm("Hapus klip ini?")) {
                              deleteClipMutation.mutate(clip.id)
                            }
                          }}
                          className="p-2 rounded-xl text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition"
                          title="Hapus Klip"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
