import React from "react"
import { Link } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  LayoutDashboard,
  Clock,
  Sparkles,
  RotateCcw,
  Trash2,
  ExternalLink,
  AlertCircle,
  CheckCircle2,
  Video,
  Scissors,
  HardDrive,
  FileVideo,
} from "lucide-react"
import { api } from "@/lib/api"
import { Job } from "@/types"
import { formatDuration } from "@/lib/utils"

const statusLabels: Record<string, { label: string; color: string }> = {
  queued: { label: "Dalam Antrean", color: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" },
  downloading: { label: "Mengunduh Video", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
  transcribing: { label: "Transkripsi Audio", color: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20" },
  analyzing: { label: "Mencari Momen AI", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
  rendering: { label: "Merender 9:16 & Subtitle", color: "bg-pink-500/10 text-pink-500 border-pink-500/20" },
  done: { label: "Selesai", color: "bg-green-500/10 text-green-500 border-green-500/20" },
  failed: { label: "Gagal", color: "bg-red-500/10 text-red-500 border-red-500/20" },
}

export const Dashboard: React.FC = () => {
  const queryClient = useQueryClient()

  // Polling every 3 seconds as requested in specifications
  const { data: jobs = [], isLoading, isError, error } = useQuery({
    queryKey: ["jobs"],
    queryFn: api.getJobs,
    refetchInterval: 3000,
  })

  // Storage Quota (10 GB)
  const { data: storageQuota } = useQuery({
    queryKey: ["storageQuota"],
    queryFn: api.getStorageQuota,
  })

  const deleteMutation = useMutation({
    mutationFn: (jobId: string) => api.deleteJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] })
      queryClient.invalidateQueries({ queryKey: ["storageQuota"] })
    },
  })

  const retryMutation = useMutation({
    mutationFn: (jobId: string) => api.retryJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] })
    },
  })

  return (
    <div className="container max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight flex items-center space-x-2">
            <FileVideo className="h-7 w-7 text-purple-600" />
            <span>Pustaka Video & Riwayat Project</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Riwayat seluruh project video clipper Anda dan pantau sisa kuota penyimpanan 10 GB.
          </p>
        </div>

        <Link
          to="/"
          className="inline-flex items-center space-x-2 rounded-xl bg-purple-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-purple-700 transition self-start sm:self-auto"
        >
          <Scissors className="h-4 w-4" />
          <span>Buat Klip Baru</span>
        </Link>
      </div>

      {/* 10 GB Storage Quota Card */}
      {storageQuota && (
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <HardDrive className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-foreground">Kapasitas Penyimpanan Pengguna</h3>
                <p className="text-xs text-muted-foreground">
                  Setiap akun diberikan alokasi penyimpanan <strong>10 GB</strong> untuk menyimpan raw video & klip hasil render.
                </p>
              </div>
            </div>

            <div className="text-right">
              <p className="text-sm font-bold font-mono text-purple-400">
                {storageQuota.used_gb.toFixed(2)} GB <span className="text-muted-foreground font-normal">/ {storageQuota.quota_gb} GB</span>
              </p>
              <p className="text-[11px] text-muted-foreground">
                {storageQuota.total_videos} video tersimpan ({storageQuota.percentage}%)
              </p>
            </div>
          </div>

          <div className="w-full bg-muted rounded-full h-2.5 overflow-hidden border border-border">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                storageQuota.percentage > 90
                  ? "bg-red-500"
                  : storageQuota.percentage > 70
                  ? "bg-amber-500"
                  : "bg-purple-600"
              }`}
              style={{ width: `${storageQuota.percentage}%` }}
            />
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-2xl border border-border bg-card animate-pulse" />
          ))}
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="flex items-center space-x-2 rounded-xl bg-red-500/10 p-4 text-sm text-red-500 border border-red-500/20">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>Gagal memuat daftar job: {(error as Error).message}</span>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && jobs.length === 0 && (
        <div className="text-center py-16 border-2 border-dashed border-border rounded-2xl p-8 bg-card/50">
          <Video className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-bold mb-1">Belum Ada Video yang Diproses</h3>
          <p className="text-sm text-muted-foreground max-w-sm mx-auto mb-6">
            Mulai potong video pertama Anda dengan memasukkan link streamer atau mengunggah video.
          </p>
          <Link
            to="/"
            className="inline-flex items-center space-x-2 rounded-xl bg-purple-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-purple-700 transition"
          >
            <Scissors className="h-4 w-4" />
            <span>Mulai Sekarang</span>
          </Link>
        </div>
      )}

      {/* Jobs List */}
      <div className="space-y-4">
        {jobs.map((job) => {
          const statusInfo = statusLabels[job.status] || { label: job.status, color: "bg-gray-500/10 text-gray-400" }
          const isDone = job.status === "done"
          const isFailed = job.status === "failed"
          const isProcessing = !isDone && !isFailed

          return (
            <div
              key={job.id}
              className="rounded-2xl border border-border bg-card p-5 sm:p-6 shadow-sm hover:shadow-md transition space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${statusInfo.color}`}
                    >
                      {statusInfo.label}
                    </span>
                    <span className="text-xs text-muted-foreground uppercase font-mono">
                      {job.source_type}
                    </span>
                  </div>
                  <h3 className="text-base sm:text-lg font-bold text-foreground">
                    {job.title || "Memproses video..."}
                  </h3>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  {isFailed && (
                    <button
                      onClick={() => retryMutation.mutate(job.id)}
                      disabled={retryMutation.isPending}
                      className="flex items-center space-x-1 rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted text-foreground transition"
                      title="Lanjutkan dari tahap yang gagal"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                      <span>Ulangi Tahap</span>
                    </button>
                  )}

                  <Link
                    to={`/jobs/${job.id}`}
                    className="flex items-center space-x-1 rounded-lg bg-purple-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-purple-700 transition"
                  >
                    <span>Detail & Klip</span>
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Link>

                  <button
                    onClick={() => {
                      if (confirm("Hapus job ini beserta seluruh klipnya?")) {
                        deleteMutation.mutate(job.id)
                      }
                    }}
                    disabled={deleteMutation.isPending}
                    className="p-1.5 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition"
                    title="Hapus Job"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Progress bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Progres Pipeline</span>
                  <span>{job.progress}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      isFailed
                        ? "bg-red-500"
                        : isDone
                        ? "bg-green-500"
                        : "bg-purple-600 animate-pulse"
                    }`}
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              </div>

              {/* Error message if failed */}
              {job.error && (
                <div className="text-xs text-red-500 bg-red-500/10 p-2.5 rounded-lg border border-red-500/20">
                  <strong>Error ({job.failed_step || "pipeline"}):</strong> {job.error}
                </div>
              )}

              {/* Metadata footer */}
              <div className="flex items-center justify-between text-xs text-muted-foreground pt-1 border-t border-border/50">
                <span className="flex items-center space-x-1">
                  <Clock className="h-3.5 w-3.5" />
                  <span>Dibuat: {new Date(job.created_at).toLocaleString("id-ID")}</span>
                </span>
                {job.duration_sec ? (
                  <span>Durasi Asli: {formatDuration(job.duration_sec)}</span>
                ) : null}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
