import React, { useState } from "react"
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
  Video
} from "lucide-react"
import { api } from "@/lib/api"
import { Clip } from "@/types"
import { formatDuration } from "@/lib/utils"

export const JobDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

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
            <span>{job.progress}%</span>
          </div>
          <div className="h-2.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                isFailed ? "bg-red-500" : "bg-purple-600 animate-pulse"
              }`}
              style={{ width: `${job.progress}%` }}
            />
          </div>
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

      {/* History & Transkrip Accordion Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Step History */}
        <div className="rounded-2xl border border-border bg-card p-5 space-y-3">
          <h3 className="text-sm font-bold flex items-center space-x-2">
            <span>Riwayat Tahapan Pipeline</span>
          </h3>
          <div className="space-y-2">
            {job.step_history && job.step_history.length > 0 ? (
              job.step_history.map((s, sIdx) => (
                <div key={sIdx} className="flex items-center justify-between text-xs p-2 rounded-lg bg-muted/40 border border-border/50">
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
        <div className="rounded-2xl border border-border bg-card p-5 space-y-3">
          <h3 className="text-sm font-bold flex items-center justify-between">
            <span>Transkrip Teks Whisper</span>
            {job.transcript_preview && (
              <span className="text-[10px] text-green-500 bg-green-500/10 px-2 py-0.5 rounded font-mono">
                Teks Terdeteksi
              </span>
            )}
          </h3>
          <div className="max-h-48 overflow-y-auto rounded-xl border border-border bg-background p-3 text-xs font-mono text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {job.transcript_preview || "Teks transkrip belum tersedia atau sedang diekstrak..."}
          </div>
        </div>
      </div>

      {/* Clips Section */}
      <div className="space-y-6">
        <h2 className="text-xl font-bold tracking-tight">Klip 9:16 Siap Publikasi</h2>

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
      </div>
    </div>
  )
}
