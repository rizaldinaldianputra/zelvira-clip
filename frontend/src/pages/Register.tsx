import React, { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Scissors, AlertCircle, ArrowRight } from "lucide-react"
import { api } from "@/lib/api"
import { useAuth } from "@/context/AuthContext"

export const Register: React.FC = () => {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError("Kata sandi dan konfirmasi kata sandi tidak cocok.")
      return
    }

    if (password.length < 6) {
      setError("Kata sandi minimal harus 6 karakter.")
      return
    }

    setLoading(true)
    try {
      const res = await api.register({ email, password })
      login(res.access_token, res.user)
      navigate("/")
    } catch (err: any) {
      setError(err.message || "Pendaftaran gagal. Silakan coba lagi.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6 rounded-2xl border border-border bg-card p-8 shadow-xl">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-purple-600/10 text-purple-600 mb-2">
            <Scissors className="h-8 w-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Buat Akun AI Clipper</h1>
          <p className="text-sm text-muted-foreground">
            Daftar untuk memotong video otomatis dengan BYOK API keys
          </p>
        </div>

        {error && (
          <div className="flex items-center space-x-2 rounded-lg bg-red-500/10 p-3 text-sm text-red-500 border border-red-500/20">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nama@email.com"
              className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none focus:ring-1 focus:ring-purple-600"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Kata Sandi
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimal 6 karakter"
              className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none focus:ring-1 focus:ring-purple-600"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Konfirmasi Kata Sandi
            </label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Ulangi kata sandi"
              className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none focus:ring-1 focus:ring-purple-600"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center space-x-2 rounded-xl bg-purple-600 py-3 text-sm font-semibold text-white shadow-md hover:bg-purple-700 transition disabled:opacity-50"
          >
            <span>{loading ? "Memproses..." : "Daftar Akun"}</span>
            {!loading && <ArrowRight className="h-4 w-4" />}
          </button>
        </form>

        <div className="text-center text-xs text-muted-foreground">
          Sudah punya akun?{" "}
          <Link to="/login" className="font-semibold text-purple-600 hover:underline">
            Masuk sekarang
          </Link>
        </div>
      </div>
    </div>
  )
}
