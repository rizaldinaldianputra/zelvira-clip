import React from "react"
import { Link, useNavigate } from "react-router-dom"
import { Scissors, LayoutDashboard, Settings as SettingsIcon, LogOut, Sun, Moon, ShieldAlert } from "lucide-react"
import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"

export const Navbar: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-6">
        <Link to="/" className="flex items-center space-x-2.5 font-bold text-xl tracking-tight">
          <div className="p-2 rounded-xl bg-purple-600 text-white shadow-md shadow-purple-500/20">
            <Scissors className="h-5 w-5" />
          </div>
          <span className="bg-gradient-to-r from-purple-600 via-indigo-500 to-pink-500 bg-clip-text text-transparent">
            AI Clipper
          </span>
        </Link>

        <nav className="flex items-center space-x-1 sm:space-x-3">
          {isAuthenticated ? (
            <>
              <Link
                to="/"
                className="px-3 py-2 text-sm font-medium rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                Buat Klip
              </Link>
              <Link
                to="/dashboard"
                className="flex items-center space-x-1.5 px-3 py-2 text-sm font-medium rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <LayoutDashboard className="h-4 w-4" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/settings"
                className="flex items-center space-x-1.5 px-3 py-2 text-sm font-medium rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <SettingsIcon className="h-4 w-4" />
                <span>Pengaturan AI</span>
              </Link>
            </>
          ) : null}

          <Link
            to="/terms"
            className="flex items-center space-x-1 px-3 py-2 text-sm font-medium rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <ShieldAlert className="h-4 w-4" />
            <span className="hidden sm:inline">Ketentuan</span>
          </Link>

          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="Toggle theme"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

          {isAuthenticated ? (
            <div className="flex items-center space-x-2 pl-2 border-l border-border">
              <span className="text-xs text-muted-foreground hidden md:inline">
                {user?.email}
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-1 px-2.5 py-1.5 text-xs font-medium rounded-md text-red-500 hover:bg-red-500/10 transition-colors"
                title="Keluar"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Keluar</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2 pl-2 border-l border-border">
              <Link
                to="/login"
                className="px-3 py-1.5 text-sm font-medium rounded-lg text-foreground hover:bg-muted transition-colors"
              >
                Masuk
              </Link>
              <Link
                to="/register"
                className="px-3 py-1.5 text-sm font-medium rounded-lg bg-purple-600 hover:bg-purple-700 text-white shadow-sm transition-colors"
              >
                Daftar
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  )
}
