import React, { createContext, useContext, useState, useEffect } from "react"
import { User } from "@/types"
import { getToken, clearToken, setToken } from "@/lib/api"

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string, user: User) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setTokenState] = useState<string | null>(getToken())
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem("user")
    return saved ? JSON.parse(saved) : null
  })
  const [isLoading, setIsLoading] = useState<boolean>(true)

  useEffect(() => {
    const currentToken = getToken()
    setTokenState(currentToken)
    setIsLoading(false)
  }, [])

  const login = (newToken: string, newUser: User) => {
    setToken(newToken)
    setTokenState(newToken)
    setUser(newUser)
    localStorage.setItem("user", JSON.stringify(newUser))
  }

  const logout = () => {
    clearToken()
    setTokenState(null)
    setUser(null)
    localStorage.removeItem("user")
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
