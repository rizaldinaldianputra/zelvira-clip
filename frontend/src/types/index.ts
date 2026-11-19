export interface User {
  id: string
  email: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Clip {
  id: string
  job_id: string
  start_sec: number
  end_sec: number
  score: number
  category?: string
  hook?: string
  reason?: string
  title?: string
  caption?: string
  hashtags: string[]
  file_path?: string
  thumbnail_path?: string
  created_at: string
}

export interface JobSettings {
  clip_count: number
  target_duration: number
  layout: "focus" | "split" | "header_banner"
  custom_header_text?: string
  subtitle_preset: "bold_yellow" | "classic" | "neon"
  language: string
}

export interface StepHistoryItem {
  step: string
  name: string
  status: "success" | "failed" | "pending"
  message: string
}

export interface Job {
  id: string
  user_id: string
  source_type: "youtube" | "tiktok" | "upload"
  source_url?: string
  title?: string
  duration_sec?: number
  status: "queued" | "downloading" | "transcribing" | "analyzing" | "rendering" | "done" | "failed"
  progress: number
  error?: string
  failed_step?: string
  settings: JobSettings
  created_at: string
  updated_at: string
  clips?: Clip[]
  total_tokens?: number
  estimated_cost_usd?: number
  transcript_preview?: string
  step_history?: StepHistoryItem[]
}

export interface AIKey {
  id: string
  provider: "openai" | "anthropic" | "gemini" | "deepseek" | "openrouter" | "custom"
  key_hint: string
  base_url?: string
  created_at: string
}

export interface ModelSuggestion {
  id: string
  name: string
  description: string
  provider?: string
  recommended_for?: string
}

export interface AgentModelMapping {
  agent_name: string
  key_id?: string
  key_hint?: string
  provider?: string
  model: string
}

export interface TestKeyResponse {
  success: boolean
  message: string
  latency_ms?: number
  model_tested?: string
}
