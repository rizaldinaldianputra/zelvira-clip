import React, { useState } from "react"
import { ShieldAlert, CheckCircle2, Flag, AlertTriangle } from "lucide-react"

export const Terms: React.FC = () => {
  const [reportOpen, setReportOpen] = useState(false)
  const [reportUrl, setReportUrl] = useState("")
  const [reportReason, setReportReason] = useState("")
  const [reportSent, setReportSent] = useState(false)

  const handleReport = (e: React.FormEvent) => {
    e.preventDefault()
    setReportSent(true)
    setTimeout(() => {
      setReportSent(false)
      setReportOpen(false)
      setReportUrl("")
      setReportReason("")
    }, 2500)
  }

  return (
    <div className="container max-w-4xl mx-auto px-4 py-8 sm:py-12 space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight flex items-center space-x-2">
          <ShieldAlert className="h-7 w-7 text-purple-600" />
          <span>Syarat & Ketentuan Penggunaan</span>
        </h1>
        <p className="text-sm text-muted-foreground">
          Ketentuan hak cipta, kepemilikan konten, dan kepatuhan hukum penggunaan AI Clipper.
        </p>
      </div>

      <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 space-y-6 shadow-sm text-sm text-muted-foreground leading-relaxed">
        <div className="space-y-3">
          <h2 className="text-base font-bold text-foreground">1. Tanggung Jawab Hak Cipta & Kepemilikan Konten</h2>
          <p>
            Pengguna ("User") bertanggung jawab penuh atas segala video, siaran langsung, atau materi audio-visual yang dimasukkan ke dalam layanan AI Clipper (baik melalui tautan YouTube, TikTok, maupun berkas yang diunggah).
          </p>
          <p>
            AI Clipper semata-mata bertindak sebagai alat pemroses teknis otomatis atas instruksi pengguna. Pengguna wajib memastikan bahwa mereka memiliki izin, hak cipta, atau memenuhi doktrin penggunaan wajar (fair use) sebelum memproses, memotong, dan menyebarluaskan kembali hasil klip video.
          </p>
        </div>

        <div className="space-y-3">
          <h2 className="text-base font-bold text-foreground">2. Kebijakan BYOK (Bring Your Own Key) & Privasi Data</h2>
          <p>
            Setiap panggilan analisis LLM menggunakan kredensial API key milik pengguna secara independen. AI Clipper tidak menyimpan atau menjual data transkrip rekaman pengguna kepada pihak ketiga. Kunci API disimpan dalam bentuk terenkripsi Fernet dan hanya didekripsi saat job pipeline dieksekusi di background worker.
          </p>
        </div>

        <div className="space-y-3">
          <h2 className="text-base font-bold text-foreground">3. Larangan Penggunaan</h2>
          <p>
            Dilarang menggunakan platform ini untuk memproses konten yang melanggar hukum, mengandung ujaran kebencian, pornografi, doxxing, atau melanggar hak privasi individu tanpa persetujuan.
          </p>
        </div>

        <div className="pt-4 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="font-bold text-foreground">Menemukan Konten yang Melanggar Hak Cipta Anda?</h3>
            <p className="text-xs">Kami menanggapi setiap laporan pelanggaran DMCA / Hak Cipta secara serius.</p>
          </div>

          <button
            onClick={() => setReportOpen(true)}
            className="flex items-center space-x-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 px-4 py-2.5 text-xs font-semibold transition"
          >
            <Flag className="h-4 w-4" />
            <span>Laporkan Konten</span>
          </button>
        </div>
      </div>

      {/* Modal Laporkan Konten */}
      {reportOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl space-y-4">
            <div className="flex items-center space-x-2 text-red-500">
              <AlertTriangle className="h-5 w-5" />
              <h3 className="font-bold text-lg text-foreground">Formulir Laporan Konten</h3>
            </div>

            {reportSent ? (
              <div className="py-8 text-center space-y-2 text-green-500">
                <CheckCircle2 className="h-10 w-10 mx-auto" />
                <p className="font-semibold text-sm">Laporan Berhasil Terkirim</p>
                <p className="text-xs text-muted-foreground">Tim kami akan menindaklanjuti dalam waktu 1x24 jam.</p>
              </div>
            ) : (
              <form onSubmit={handleReport} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Tautan / ID Video</label>
                  <input
                    type="text"
                    required
                    value={reportUrl}
                    onChange={(e) => setReportUrl(e.target.value)}
                    placeholder="URL konten atau Job ID"
                    className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Alasan Laporan</label>
                  <textarea
                    required
                    rows={3}
                    value={reportReason}
                    onChange={(e) => setReportReason(e.target.value)}
                    placeholder="Jelaskan pelanggaran hak cipta atau konten terlarang..."
                    className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                  />
                </div>

                <div className="flex items-center space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setReportOpen(false)}
                    className="flex-1 py-2 rounded-xl border border-border text-xs font-semibold hover:bg-muted transition"
                  >
                    Batal
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-sm"
                  >
                    Kirim Laporan
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
