import React from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthProvider } from "@/context/AuthContext"
import { ThemeProvider } from "@/context/ThemeContext"
import { Navbar } from "@/components/Navbar"
import { ProtectedRoute } from "@/components/ProtectedRoute"

import { Home } from "@/pages/Home"
import { Dashboard } from "@/pages/Dashboard"
import { JobDetail } from "@/pages/JobDetail"
import { Settings } from "@/pages/Settings"
import { Login } from "@/pages/Login"
import { Register } from "@/pages/Register"
import { Terms } from "@/pages/Terms"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <div className="min-h-screen flex flex-col bg-background text-foreground transition-colors">
              <Navbar />
              <main className="flex-1">
                <Routes>
                  {/* Public routes */}
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  <Route path="/terms" element={<Terms />} />

                  {/* Protected routes */}
                  <Route element={<ProtectedRoute />}>
                    <Route path="/" element={<Home />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/jobs/:id" element={<JobDetail />} />
                    <Route path="/settings" element={<Settings />} />
                  </Route>

                  {/* Fallback */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </main>
            </div>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
