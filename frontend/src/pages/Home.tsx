import React, { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import {
  Scissors,
  Youtube,
  Upload,
  Sliders,
  Sparkles,
  AlertCircle,
  FileVideo,
  CheckCircle2,
  KeyRound,
} from "lucide-react"
import { api } from "@/lib/api"

export const Home: React.FC = () => {
  const navigate = useNavigate()

  // Form State
  const [sourceType, setSourceType] = useState<"link" | "file">("link")
  const [url, setUrl] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [clipCount, setClipCount] = useState<number>(5)
  const [targetDuration, setTargetDuration] = useState<number>(60)
  const [layout, setLayout] = useState<"focus" | "split" | "header_banner">("focus")
  const [customHeader, setCustomHeader] = useState<string>("REAKSI STREAMER TERBAIK 🔥")
  const [subtitlePreset, setSubtitlePreset] = useState<"bold_yellow" | "classic" | "neon">("bold_yellow")
  const [language, setLanguage] = useState<string>("auto")

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Check if user has added an API key
  const { data: keys = [] } = useQuery({
    queryKey: ["aiKeys"],
    queryFn: api.getKeys,
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0]
      const ext = selected.name.split(".").pop()?.toLowerCase()
      if (!["mp4", "mov", "mkv", "webm"].includes(ext || "")) {
        setError("Format file tidak didukung. Harap unggah MP4, MOV, MKV, atau WebM.")
        return
      }
      setFile(selected)
      setError(null)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (keys.length === 0) {
      setError("Anda belum menambahkan Kunci API AI. Harap atur API key Anda di halaman Pengaturan AI terlebih dahulu.")
      return
    }

    if (sourceType === "link") {
      if (!url.trim()) {
        setError("Masukkan URL YouTube atau TikTok yang valid.")
        return
      }
      if (!url.includes("youtube.com") && !url.includes("youtu.be") && !url.includes("tiktok.com")) {
        setError("Hanya link YouTube dan TikTok yang didukung.")
        return
      }
    } else {
      if (!file) {
        setError("Pilih file video untuk diunggah.")
        return
      }
    }

    setLoading(true)

    try {
      const formData = new FormData()
      if (sourceType === "link") {
        formData.append("source_url", url.trim())
      } else if (file) {
        formData.append("file", file)
      }

      formData.append("clip_count", clipCount.toString())
      formData.append("target_duration", targetDuration.toString())
      formData.append("layout", layout)
      if (layout === "header_banner" && customHeader.trim()) {
        formData.append("custom_header_text", customHeader.trim())
      }
      formData.append("subtitle_preset", subtitlePreset)
      formData.append("language", language)

      const job = await api.createJob(formData)
      navigate(`/jobs/${job.id}`)
    } catch (err: any) {
      setError(err.message || "Gagal membuat job pemotongan klip.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container max-w-4xl mx-auto px-4 py-8 sm:py-12">
      {/* Header */}
      <div className="text-center space-y-3 mb-10">
        <div className="inline-flex items-center space-x-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-4 py-1.5 text-xs font-semibold text-purple-400">
          <Sparkles className="h-3.5 w-3.5" />
          <span>AI Viral Clipper 9:16</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight">
          Potong Stream Jadi Klip Viral{" "}
          <span className="bg-gradient-to-r from-purple-500 via-pink-500 to-indigo-500 bg-clip-text text-transparent">
            Otomatis
          </span>
        </h1>
        <p className="text-sm sm:text-base text-muted-foreground max-w-xl mx-auto">
          AI mendeteksi momen terbaik, memotong dan reframing ke format 9:16 vertikal, melacak wajah streamer, dan membakar subtitle TikTok.
        </p>
      </div>

      {/* Warning if no keys configured */}
      {keys.length === 0 && (
        <div className="mb-8 flex items-center justify-between rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-500">
          <div className="flex items-center space-x-3">
            <KeyRound className="h-5 w-5 shrink-0" />
            <span>Kunci API AI belum diatur. Anda membutuhkan minimal satu API key (BYOK) untuk menjalankan pipeline.</span>
          </div>
          <Link
            to="/settings"
            className="shrink-0 ml-4 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-black hover:bg-amber-400 transition"
          >
            Atur Kunci
          </Link>
        </div>
      )}

      {/* Error alert */}
      {error && (
        <div className="mb-6 flex items-center space-x-2 rounded-xl bg-red-500/10 p-4 text-sm text-red-500 border border-red-500/20">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Input Form */}
      <form onSubmit={handleSubmit} className="space-y-8 rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-xl">
        {/* Source Type Selector */}
        <div className="flex rounded-xl bg-muted p-1">
          <button
            type="button"
            onClick={() => setSourceType("link")}
            className={`flex-1 flex items-center justify-center space-x-2 py-2.5 rounded-lg text-sm font-semibold transition ${
              sourceType === "link"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Youtube className="h-4 w-4" />
            <span>Link YouTube / TikTok</span>
          </button>
          <button
            type="button"
            onClick={() => setSourceType("file")}
            className={`flex-1 flex items-center justify-center space-x-2 py-2.5 rounded-lg text-sm font-semibold transition ${
              sourceType === "file"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Upload className="h-4 w-4" />
            <span>Upload File Video</span>
          </button>
        </div>

        {/* Source Input */}
        {sourceType === "link" ? (
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              URL Streamer
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=... atau https://www.tiktok.com/@.../video/..."
              className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm focus:border-purple-600 focus:outline-none focus:ring-1 focus:ring-purple-600"
            />
            <p className="text-xs text-muted-foreground">
              Maksimal durasi video: 60 menit. Hanya video publik yang dapat diproses.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              File Video Lokal
            </label>
            <div className="flex flex-col items-center justify-center border-2 border-dashed border-border rounded-xl p-6 sm:p-8 hover:border-purple-500/50 transition cursor-pointer relative bg-muted/20">
              <input
                type="file"
                accept=".mp4,.mov,.mkv,.webm"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              {file ? (
                <div className="flex items-center space-x-3 text-purple-600">
                  <FileVideo className="h-8 w-8" />
                  <div className="text-left">
                    <p className="text-sm font-semibold text-foreground">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{(file.size / (1024 * 1024)).toFixed(1)} MB</p>
                  </div>
                </div>
              ) : (
                <div className="text-center space-y-2">
                  <Upload className="h-8 w-8 text-muted-foreground mx-auto" />
                  <p className="text-sm font-medium">Klik atau seret file video ke sini</p>
                  <p className="text-xs text-muted-foreground">Format: MP4, MOV, MKV, WebM (Maks. 500MB)</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Options Grid */}
        <div className="pt-4 border-t border-border space-y-6">
          <div className="flex items-center space-x-2 text-sm font-bold text-foreground">
            <Sliders className="h-4 w-4 text-purple-500" />
            <span>Opsi & Pengaturan Klip</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Target Duration */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Target Durasi</label>
              <div className="grid grid-cols-3 gap-2">
                {[30, 60, 90].map((dur) => (
                  <button
                    key={dur}
                    type="button"
                    onClick={() => setTargetDuration(dur)}
                    className={`py-2 text-xs font-semibold rounded-lg border transition ${
                      targetDuration === dur
                        ? "border-purple-600 bg-purple-600/10 text-purple-500"
                        : "border-border hover:bg-muted text-muted-foreground"
                    }`}
                  >
                    {dur} detik
                  </button>
                ))}
              </div>
            </div>

            {/* Clip Count */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Jumlah Klip Terbaik</label>
              <select
                value={clipCount}
                onChange={(e) => setClipCount(Number(e.target.value))}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm focus:border-purple-600 focus:outline-none"
              >
                {[1, 2, 3, 5, 7, 10].map((cnt) => (
                  <option key={cnt} value={cnt}>
                    Top {cnt} Klip
                  </option>
                ))}
              </select>
            </div>

            {/* Layout */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Layout & Template</label>
              <div className="grid grid-cols-3 gap-1.5">
                <button
                  type="button"
                  onClick={() => setLayout("focus")}
                  className={`py-2 text-[11px] font-semibold rounded-lg border transition ${
                    layout === "focus"
                      ? "border-purple-600 bg-purple-600/10 text-purple-500"
                      : "border-border hover:bg-muted text-muted-foreground"
                  }`}
                  title="Crop penuh vertikal mengikuti wajah streamer"
                >
                  Fokus Wajah
                </button>
                <button
                  type="button"
                  onClick={() => setLayout("split")}
                  className={`py-2 text-[11px] font-semibold rounded-lg border transition ${
                    layout === "split"
                      ? "border-purple-600 bg-purple-600/10 text-purple-500"
                      : "border-border hover:bg-muted text-muted-foreground"
                  }`}
                  title="Wajah streamer di atas, gameplay di bawah"
                >
                  Split Screen
                </button>
                <button
                  type="button"
                  onClick={() => setLayout("header_banner")}
                  className={`py-2 text-[11px] font-semibold rounded-lg border transition ${
                    layout === "header_banner"
                      ? "border-purple-600 bg-purple-600/10 text-purple-500"
                      : "border-border hover:bg-muted text-muted-foreground"
                  }`}
                  title="Template dengan banner teks kustom di bagian atas video"
                >
                  Banner Teks
                </button>
              </div>

              {layout === "header_banner" && (
                <div className="pt-2 space-y-1">
                  <label className="text-[10px] uppercase font-bold text-purple-500">
                    Teks Banner Kustom (Frame Atas)
                  </label>
                  <input
                    type="text"
                    value={customHeader}
                    onChange={(e) => setCustomHeader(e.target.value)}
                    placeholder="Contoh: REAKSI OURAA KETEMU..."
                    className="w-full rounded-lg border border-purple-500/30 bg-background px-3 py-1.5 text-xs focus:outline-none focus:border-purple-600"
                  />
                </div>
              )}
            </div>

            {/* Subtitle Preset */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Gaya Subtitle</label>
              <select
                value={subtitlePreset}
                onChange={(e) => setSubtitlePreset(e.target.value as any)}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm focus:border-purple-600 focus:outline-none"
              >
                <option value="bold_yellow">TikTok Bold (Kuning Highlight)</option>
                <option value="classic">Classic Clean (Cyan Highlight)</option>
                <option value="neon">Neon High Energy (Magenta Highlight)</option>
              </select>
            </div>

            {/* Language */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Bahasa Transkrip</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm focus:border-purple-600 focus:outline-none"
              >
                <option value="auto">Deteksi Otomatis</option>
                <option value="id">Bahasa Indonesia</option>
                <option value="en">English</option>
              </select>
            </div>
          </div>
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center space-x-2 rounded-xl bg-purple-600 py-4 text-base font-bold text-white shadow-lg hover:bg-purple-700 transition disabled:opacity-50 cursor-pointer"
        >
          <Scissors className="h-5 w-5" />
          <span>{loading ? "Sedang Mengirim Pipeline..." : "Buat Klip Sekarang"}</span>
        </button>
      </form>
    </div>
  )
}
