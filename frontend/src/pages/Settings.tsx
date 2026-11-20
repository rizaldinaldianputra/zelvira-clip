import React, { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  KeyRound,
  ShieldCheck,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Layers,
  Sparkles,
  Activity,
  History,
  Check,
  X,
  ExternalLink,
  ChevronRight,
  Server,
  Code2
} from "lucide-react"
import { api } from "@/lib/api"
import { AIKey, AgentModelMapping, ProviderStatus, GatewayModel, UsageHistoryResponse } from "@/types"

export const Settings: React.FC = () => {
  const queryClient = useQueryClient()

  // Active Tab
  const [activeTab, setActiveTab] = useState<"providers" | "models" | "mappings" | "history">("providers")

  // New Key Form State
  const [provider, setProvider] = useState<string>("openai")
  const [apiKey, setApiKey] = useState<string>("")
  const [baseUrl, setBaseUrl] = useState<string>("")
  const [testModel, setTestModel] = useState<string>("gpt-4o-mini")

  // Testing status
  const [testing, setTesting] = useState<boolean>(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; latency_ms?: number } | null>(null)
  const [keyError, setKeyError] = useState<string | null>(null)

  // Agent Model Mappings State
  const [agentMappings, setAgentMappings] = useState<Record<string, { key_id: string; model: string }>>({
    moment_finder: { key_id: "", model: "gpt-4o-mini" },
    ranker: { key_id: "", model: "gpt-4o" },
    metadata: { key_id: "", model: "gpt-4o-mini" },
  })
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false)

  // 1. Queries - Providers Connection Status
  const { data: providers = [], isLoading: loadingProviders } = useQuery<ProviderStatus[]>({
    queryKey: ["aiProviders"],
    queryFn: api.getProvidersStatus,
  })

  // 2. Queries - AI Keys
  const { data: keys = [], isLoading: loadingKeys } = useQuery<AIKey[]>({
    queryKey: ["aiKeys"],
    queryFn: api.getKeys,
  })

  // 3. Queries - Gateway Models
  const { data: gatewayModels = [], isLoading: loadingModels } = useQuery<GatewayModel[]>({
    queryKey: ["gatewayModels"],
    queryFn: () => api.getGatewayModels(),
  })

  // 4. Queries - Usage History
  const { data: usageHistory, isLoading: loadingUsage } = useQuery<UsageHistoryResponse>({
    queryKey: ["usageHistory"],
    queryFn: () => api.getUsageHistory(50),
    enabled: activeTab === "history",
  })

  const { data: allModels = [] } = useQuery({
    queryKey: ["allModels"],
    queryFn: () => api.getModels(),
  })

  const { data: providerModels = [] } = useQuery({
    queryKey: ["providerModels", provider],
    queryFn: () => api.getModels(provider),
    enabled: !!provider,
  })

  const { data: currentAgentModels = [] } = useQuery({
    queryKey: ["agentModels"],
    queryFn: async () => {
      const res = await api.getAgentModels()
      const map: Record<string, { key_id: string; model: string }> = {}
      res.forEach((item) => {
        map[item.agent_name] = { key_id: item.key_id || "", model: item.model }
      })
      setAgentMappings((prev) => ({ ...prev, ...map }))
      return res
    },
  })

  // Helper: Dapatkan model yang tersedia khusus untuk Kunci API yang dipilih
  const getModelsForKey = (keyId: string) => {
    // 1. Cari kunci API di daftar kunci tersimpan
    const selectedKey = keys.find((k) => k.id === keyId)
    if (!selectedKey) {
      // Jika belum memilih key atau pilih otomatis, ambil model dari provider-provider yang tersimpan kuncinya
      const savedProviders = new Set(keys.map((k) => k.provider.toLowerCase()))
      if (savedProviders.size > 0) {
        const filtered = gatewayModels.filter((m) => savedProviders.has(m.provider.toLowerCase()))
        if (filtered.length > 0) return filtered
      }
      return gatewayModels.length > 0 ? gatewayModels : allModels
    }

    const prov = selectedKey.provider.toLowerCase()

    // 2. Filter model dari Gateway Models sesuai provider kunci tersimpan
    const matchedGatewayModels = gatewayModels.filter((m) => m.provider.toLowerCase() === prov)
    if (matchedGatewayModels.length > 0) {
      return matchedGatewayModels
    }

    // 3. Fallback filter dari allModels
    const filtered = allModels.filter(
      (m) => (m.provider && m.provider.toLowerCase() === prov) || m.id.toLowerCase().startsWith(prov)
    )
    return filtered.length > 0 ? filtered : allModels
  }

  // Mutations
  const addKeyMutation = useMutation({
    mutationFn: (data: { provider: string; api_key: string; base_url?: string }) => api.addKey(data),
    onSuccess: () => {
      setApiKey("")
      setBaseUrl("")
      setTestResult(null)
      setKeyError(null)
      queryClient.invalidateQueries({ queryKey: ["aiKeys"] })
      queryClient.invalidateQueries({ queryKey: ["aiProviders"] })
      queryClient.invalidateQueries({ queryKey: ["agentModels"] })
    },
    onError: (err: any) => {
      setKeyError(err.message || "Gagal menyimpan kunci API.")
    },
  })

  const deleteKeyMutation = useMutation({
    mutationFn: (keyId: string) => api.deleteKey(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["aiKeys"] })
      queryClient.invalidateQueries({ queryKey: ["aiProviders"] })
      queryClient.invalidateQueries({ queryKey: ["agentModels"] })
    },
  })

  const updateAgentModelsMutation = useMutation({
    mutationFn: (data: any) => api.updateAgentModels(data),
    onSuccess: () => {
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
      queryClient.invalidateQueries({ queryKey: ["agentModels"] })
    },
  })

  const handleTestKey = async () => {
    if (!apiKey) {
      setKeyError("Masukkan API Key terlebih dahulu untuk pengujian.")
      return
    }
    setTesting(true)
    setTestResult(null)
    setKeyError(null)

    try {
      const res = await api.testKey({
        provider,
        model: testModel,
        api_key: apiKey,
        base_url: baseUrl || undefined,
      })
      setTestResult(res)
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.message || "Pengujian gagal. Periksa kembali API Key Anda.",
      })
    } finally {
      setTesting(false)
    }
  }

  const handleSaveKey = (e: React.FormEvent) => {
    e.preventDefault()
    if (!apiKey) {
      setKeyError("API Key tidak boleh kosong.")
      return
    }
    addKeyMutation.mutate({
      provider,
      api_key: apiKey,
      base_url: baseUrl || undefined,
    })
  }

  const handleSaveAgentModels = (e: React.FormEvent) => {
    e.preventDefault()
    const mappings = Object.entries(agentMappings).map(([agent_name, conf]) => ({
      agent_name,
      key_id: conf.key_id || undefined,
      model: conf.model,
    }))
    updateAgentModelsMutation.mutate(mappings)
  }

  return (
    <div className="container max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2 text-purple-600 mb-1">
          <Server className="h-5 w-5" />
          <span className="text-xs font-bold uppercase tracking-wider">LiteLLM Unified AI Gateway</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
          AI Provider & Gateway Management
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Kelola seluruh provider LLM (OpenAI, Anthropic Claude, Gemini, NVIDIA, DeepSeek, Mistral) dalam satu standar API terpadu (BYOK). Kunci dienkripsi menggunakan standar Fernet AES-128-CBC.
        </p>
      </div>

      {/* Security notice */}
      <div className="flex items-start space-x-3 rounded-2xl border border-purple-500/20 bg-purple-500/5 p-4 text-xs text-muted-foreground">
        <ShieldCheck className="h-5 w-5 text-purple-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="text-foreground">Jaminan Keamanan & Isolasi BYOK:</strong>
          <p>
            API Key Anda hanya digunakan secara eksklusif untuk request akun Anda. Kredensial tidak pernah dicatat di log, dienkripsi saat disimpan, dan endpoint custom dilindungi dengan SSRF protection.
          </p>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center space-x-2 border-b border-border pb-1 overflow-x-auto text-sm font-semibold">
        <button
          onClick={() => setActiveTab("providers")}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl transition ${
            activeTab === "providers"
              ? "bg-purple-600 text-white shadow-md shadow-purple-500/20"
              : "text-muted-foreground hover:bg-muted"
          }`}
        >
          <Layers className="h-4 w-4" />
          <span>Dashboard AI Provider</span>
        </button>

        <button
          onClick={() => setActiveTab("models")}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl transition ${
            activeTab === "models"
              ? "bg-purple-600 text-white shadow-md shadow-purple-500/20"
              : "text-muted-foreground hover:bg-muted"
          }`}
        >
          <Cpu className="h-4 w-4" />
          <span>Model Registry ({gatewayModels.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("mappings")}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl transition ${
            activeTab === "mappings"
              ? "bg-purple-600 text-white shadow-md shadow-purple-500/20"
              : "text-muted-foreground hover:bg-muted"
          }`}
        >
          <Sparkles className="h-4 w-4" />
          <span>Penugasan Agent Clipper</span>
        </button>

        <button
          onClick={() => setActiveTab("history")}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl transition ${
            activeTab === "history"
              ? "bg-purple-600 text-white shadow-md shadow-purple-500/20"
              : "text-muted-foreground hover:bg-muted"
          }`}
        >
          <History className="h-4 w-4" />
          <span>Usage History & Audit Log</span>
        </button>
      </div>

      {/* TAB 1: PROVIDERS STATUS & KEY MANAGEMENT */}
      {activeTab === "providers" && (
        <div className="space-y-8">
          {/* Provider Status Grid (Expected Layout) */}
          <div className="space-y-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
              Status Koneksi Provider AI
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {providers.map((p) => (
                <div
                  key={p.id}
                  className={`rounded-2xl border p-5 transition flex flex-col justify-between space-y-4 shadow-sm ${
                    p.connected
                      ? "border-emerald-500/30 bg-emerald-500/5 hover:border-emerald-500/50"
                      : "border-border bg-card hover:border-muted-foreground/30"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <h3 className="font-bold text-base text-foreground">{p.name}</h3>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold ${
                          p.connected
                            ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                            : "bg-zinc-500/10 text-muted-foreground border border-zinc-500/20"
                        }`}
                      >
                        {p.connected ? (
                          <>
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
                            Connected
                          </>
                        ) : (
                          "Not connected"
                        )}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{p.category}</p>
                  </div>

                  <div className="pt-2 border-t border-border/50 text-xs flex items-center justify-between text-muted-foreground">
                    <span>
                      {p.key_hint ? (
                        <span className="font-mono text-purple-400 font-semibold">{p.key_hint}</span>
                      ) : (
                        "Belum ada key"
                      )}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setProvider(p.id)
                        const el = document.getElementById("add-key-card")
                        if (el) el.scrollIntoView({ behavior: "smooth" })
                      }}
                      className="text-purple-500 hover:text-purple-400 font-semibold flex items-center space-x-1"
                    >
                      <span>{p.connected ? "Ganti" : "Set Key"}</span>
                      <ChevronRight className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SECTION 1: Tambah / Perbarui Kunci API */}
          <div id="add-key-card" className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-sm space-y-6">
            <div className="flex items-center space-x-2 border-b border-border pb-4">
              <Plus className="h-5 w-5 text-purple-600" />
              <h2 className="text-lg font-bold">Tambah / Perbarui Kunci API (BYOK)</h2>
            </div>

            {keyError && (
              <div className="flex items-center space-x-2 rounded-xl bg-red-500/10 p-3 text-sm text-red-500 border border-red-500/20">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{keyError}</span>
              </div>
            )}

            <form onSubmit={handleSaveKey} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Provider</label>
                  <select
                    value={provider}
                    onChange={(e) => {
                      const val = e.target.value
                      setProvider(val)
                      if (val === "openai") setTestModel("gpt-4o-mini")
                      else if (val === "anthropic") setTestModel("claude-3-5-haiku-latest")
                      else if (val === "gemini") setTestModel("gemini-1.5-flash")
                      else if (val === "deepseek") setTestModel("deepseek-chat")
                      else if (val === "mistral") setTestModel("mistral-small-latest")
                      else if (val === "nvidia") {
                        setTestModel("meta/llama-3.1-70b-instruct")
                        setBaseUrl("https://integrate.api.nvidia.com/v1")
                      } else if (val === "openrouter") setTestModel("meta-llama/llama-3.1-8b-instruct")
                    }}
                    className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none"
                  >
                    <option value="openai">OpenAI (GPT Models)</option>
                    <option value="anthropic">Anthropic (Claude Models)</option>
                    <option value="gemini">Google Gemini (Gemini Models)</option>
                    <option value="nvidia">NVIDIA NIM (build.nvidia.com)</option>
                    <option value="deepseek">DeepSeek (DeepSeek Models)</option>
                    <option value="mistral">Mistral AI (Mistral Models)</option>
                    <option value="custom">Custom (OpenAI-Compatible Base URL)</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Model Pengujian</label>
                  <select
                    value={testModel}
                    onChange={(e) => setTestModel(e.target.value)}
                    className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none"
                  >
                    {(providerModels.length > 0 ? providerModels : allModels).map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({m.id})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {(provider === "custom" || provider === "nvidia") && (
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Base URL API (Endpoint)</label>
                  <input
                    type="url"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    placeholder={
                      provider === "nvidia"
                        ? "https://integrate.api.nvidia.com/v1"
                        : "https://your-custom-endpoint.com/v1"
                    }
                    className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none font-mono"
                  />
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase">API Key Milik Anda</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Tempel API Key di sini (contoh: sk-...)"
                  className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none font-mono"
                />
              </div>

              {testResult && (
                <div
                  className={`flex items-center space-x-2 rounded-xl p-3 text-xs border ${
                    testResult.success
                      ? "bg-green-500/10 text-green-500 border-green-500/20"
                      : "bg-red-500/10 text-red-500 border-red-500/20"
                  }`}
                >
                  {testResult.success ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : <AlertCircle className="h-4 w-4 shrink-0" />}
                  <span>
                    {testResult.message} {testResult.latency_ms && `(${testResult.latency_ms}ms)`}
                  </span>
                </div>
              )}

              <div className="flex flex-col sm:flex-row items-center space-y-2 sm:space-y-0 sm:space-x-3 pt-2">
                <button
                  type="button"
                  onClick={handleTestKey}
                  disabled={testing || !apiKey}
                  className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-border hover:bg-muted text-xs font-bold transition disabled:opacity-50"
                >
                  {testing ? "Menguji Koneksi..." : "Uji Koneksi (Test Key)"}
                </button>

                <button
                  type="submit"
                  disabled={addKeyMutation.isPending || !apiKey}
                  className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-md transition disabled:opacity-50"
                >
                  {addKeyMutation.isPending ? "Menyimpan Terenkripsi..." : "Simpan Kunci API"}
                </button>
              </div>
            </form>
          </div>

          {/* SECTION 2: Daftar Kunci Tersimpan */}
          <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-sm space-y-4">
            <div className="flex items-center space-x-2 border-b border-border pb-4">
              <KeyRound className="h-5 w-5 text-purple-600" />
              <h2 className="text-lg font-bold">Daftar Kunci Tersimpan</h2>
            </div>

            {loadingKeys ? (
              <div className="py-4 text-center text-xs text-muted-foreground">Memuat daftar kunci...</div>
            ) : keys.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground border border-dashed rounded-xl border-border">
                Belum ada kunci API yang tersimpan. Tambahkan kunci pertama Anda di atas.
              </div>
            ) : (
              <div className="divide-y divide-border">
                {keys.map((k) => (
                  <div key={k.id} className="flex items-center justify-between py-3.5">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-xs uppercase px-2 py-0.5 rounded bg-purple-600/10 text-purple-600 border border-purple-600/20">
                          {k.provider}
                        </span>
                        <span className="font-mono text-xs text-muted-foreground">{k.key_hint}</span>
                      </div>
                      {k.base_url && <p className="font-mono text-[11px] text-muted-foreground">Base URL: {k.base_url}</p>}
                    </div>

                    <button
                      onClick={() => {
                        if (confirm(`Yakin ingin menghapus kunci untuk provider ${k.provider}?`)) {
                          deleteKeyMutation.mutate(k.id)
                        }
                      }}
                      disabled={deleteKeyMutation.isPending}
                      className="p-2 text-muted-foreground hover:text-red-500 rounded-lg hover:bg-muted transition"
                      title="Hapus Kunci"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: MODEL REGISTRY */}
      {activeTab === "models" && (
        <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-border pb-4">
            <div>
              <h2 className="text-lg font-bold">Dynamic Model Registry</h2>
              <p className="text-xs text-muted-foreground">
                Katalog model yang dapat dipanggil langsung melalui gateway <code>POST /api/v1/ai/chat/completions</code>.
              </p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
              {gatewayModels.length} Model Terdaftar
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {gatewayModels.map((m) => (
              <div key={m.id} className="p-4 rounded-xl border border-border bg-background space-y-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-foreground">{m.name}</span>
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-muted text-muted-foreground">
                      {m.provider}
                    </span>
                  </div>
                  <p className="font-mono text-xs text-purple-400 mt-1">{m.id}</p>
                  {m.description && <p className="text-xs text-muted-foreground mt-2">{m.description}</p>}
                </div>

                <div className="pt-3 border-t border-border flex flex-wrap items-center gap-1.5 text-[10px]">
                  {m.context_window && (
                    <span className="bg-muted px-2 py-0.5 rounded text-muted-foreground font-mono">
                      {(m.context_window / 1000).toFixed(0)}k Context
                    </span>
                  )}
                  {m.supports_vision && (
                    <span className="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded font-semibold">
                      Vision
                    </span>
                  )}
                  {m.supports_tools && (
                    <span className="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded font-semibold">
                      Function Calling
                    </span>
                  )}
                  {m.recommended_for && (
                    <span className="bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded font-semibold">
                      {m.recommended_for}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: AGENT CLIPPER MAPPINGS */}
      {activeTab === "mappings" && (
        <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-sm space-y-6">
          <div className="border-b border-border pb-4">
            <h2 className="text-lg font-bold">2. Penugasan Model AI per Agent</h2>
            <p className="text-xs text-muted-foreground mt-1">
              Atur model mana yang bertugas untuk tiap tahapan pipeline AI Clipper (Moment Finder, Ranker, Metadata) berdasarkan daftar Kunci API yang tersimpan.
            </p>
          </div>

          {keys.length === 0 ? (
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-5 text-center space-y-3">
              <AlertCircle className="h-6 w-6 text-amber-500 mx-auto" />
              <div>
                <p className="font-bold text-sm text-foreground">Belum ada Kunci API yang Tersimpan</p>
                <p className="text-xs text-muted-foreground mt-1 max-w-md mx-auto">
                  Silakan tambahkan Kunci API Anda terlebih dahulu di tab <strong>Dashboard AI Provider</strong> agar dapat memilih model yang sesuai dengan kunci Anda.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setActiveTab("providers")}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold transition inline-flex items-center space-x-1.5"
              >
                <span>Buka Dashboard AI Provider</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <>
              {saveSuccess && (
                <div className="flex items-center space-x-2 rounded-xl bg-green-500/10 p-3 text-xs text-green-500 border border-green-500/20">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>Pengaturan model berhasil disimpan!</span>
                </div>
              )}

              <form onSubmit={handleSaveAgentModels} className="space-y-6">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-border text-xs uppercase text-muted-foreground">
                        <th className="py-2.5 pr-4 font-semibold">Tugas Agent</th>
                        <th className="py-2.5 px-4 font-semibold">Kunci API Terpilih (Kunci Tersimpan)</th>
                        <th className="py-2.5 pl-4 font-semibold">Nama Model (Sesuai Kunci Terpilih)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {/* 1. Moment Finder */}
                      <tr>
                        <td className="py-4 pr-4">
                          <p className="font-bold text-foreground">Moment Finder</p>
                          <p className="text-xs text-muted-foreground">Mendeteksi momen viral di tiap chunk video</p>
                        </td>
                        <td className="py-4 px-4">
                          <select
                            value={agentMappings["moment_finder"]?.key_id || ""}
                            onChange={(e) => {
                              const newKeyId = e.target.value
                              const available = getModelsForKey(newKeyId)
                              setAgentMappings((prev) => ({
                                ...prev,
                                moment_finder: {
                                  ...prev.moment_finder,
                                  key_id: newKeyId,
                                  model: available[0]?.id || "gpt-4o-mini",
                                },
                              }))
                            }}
                            className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                          >
                            <option value="">-- Pilih dari Kunci Tersimpan ({keys.length} Kunci) --</option>
                            {keys.map((k) => (
                              <option key={k.id} value={k.id}>
                                {k.provider.toUpperCase()} ({k.key_hint})
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="py-4 pl-4">
                          <select
                            value={agentMappings["moment_finder"]?.model || ""}
                            onChange={(e) =>
                              setAgentMappings((prev) => ({
                                ...prev,
                                moment_finder: { ...prev.moment_finder, model: e.target.value },
                              }))
                            }
                            className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                          >
                            {getModelsForKey(agentMappings["moment_finder"]?.key_id).map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.name} ({m.id})
                              </option>
                            ))}
                          </select>
                        </td>
                      </tr>

                      {/* 2. Ranker */}
                      <tr>
                        <td className="py-4 pr-4">
                          <p className="font-bold text-foreground">Ranker</p>
                          <p className="text-xs text-muted-foreground">Menilai dan memilih 5 klip terbaik</p>
                        </td>
                        <td className="py-4 px-4">
                          <select
                            value={agentMappings["ranker"]?.key_id || ""}
                            onChange={(e) => {
                              const newKeyId = e.target.value
                              const available = getModelsForKey(newKeyId)
                              setAgentMappings((prev) => ({
                                ...prev,
                                ranker: {
                                  ...prev.ranker,
                                  key_id: newKeyId,
                                  model: available[0]?.id || "gpt-4o",
                                },
                              }))
                            }}
                            className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                          >
                            <option value="">-- Pilih dari Kunci Tersimpan ({keys.length} Kunci) --</option>
                            {keys.map((k) => (
                              <option key={k.id} value={k.id}>
                                {k.provider.toUpperCase()} ({k.key_hint})
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="py-4 pl-4">
                          <select
                            value={agentMappings["ranker"]?.model || ""}
                            onChange={(e) =>
                              setAgentMappings((prev) => ({
                                ...prev,
                                ranker: { ...prev.ranker, model: e.target.value },
                              }))
                            }
                            className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                          >
                            {getModelsForKey(agentMappings["ranker"]?.key_id).map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.name} ({m.id})
                              </option>
                            ))}
                          </select>
                        </td>
                      </tr>

                      {/* 3. Metadata */}
                      <tr>
                        <td className="py-4 pr-4">
                          <p className="font-bold text-foreground">Metadata</p>
                          <p className="text-xs text-muted-foreground">Membuat judul viral, caption & hashtag</p>
                        </td>
                        <td className="py-4 px-4">
                          <select
                            value={agentMappings["metadata"]?.key_id || ""}
                            onChange={(e) => {
                              const newKeyId = e.target.value
                              const available = getModelsForKey(newKeyId)
                              setAgentMappings((prev) => ({
                                ...prev,
                                metadata: {
                                  ...prev.metadata,
                                  key_id: newKeyId,
                                  model: available[0]?.id || "gpt-4o-mini",
                                },
                              }))
                            }}
                            className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                          >
                            <option value="">-- Pilih dari Kunci Tersimpan ({keys.length} Kunci) --</option>
                            {keys.map((k) => (
                              <option key={k.id} value={k.id}>
                                {k.provider.toUpperCase()} ({k.key_hint})
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="py-4 pl-4">
                          <select
                            value={agentMappings["metadata"]?.model || ""}
                            onChange={(e) =>
                              setAgentMappings((prev) => ({
                                ...prev,
                                metadata: { ...prev.metadata, model: e.target.value },
                              }))
                            }
                            className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                          >
                            {getModelsForKey(agentMappings["metadata"]?.key_id).map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.name} ({m.id})
                              </option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <button
                  type="submit"
                  disabled={updateAgentModelsMutation.isPending}
                  className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-md transition disabled:opacity-50"
                >
                  {updateAgentModelsMutation.isPending ? "Menyimpan Perubahan..." : "Simpan Penugasan Model"}
                </button>
              </form>
            </>
          )}
        </div>
      )}

      {/* TAB 4: USAGE HISTORY & AUDIT LOG */}
      {activeTab === "history" && (
        <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-border pb-4 gap-4">
            <div>
              <h2 className="text-lg font-bold">Usage History & Audit Log</h2>
              <p className="text-xs text-muted-foreground mt-1">
                Catatan komprehensif seluruh pemanggilan model AI melalui Unified Gateway. Biaya ditanggung via akun BYOK masing-masing.
              </p>
            </div>

            {usageHistory && (
              <div className="flex items-center space-x-3 text-xs">
                <div className="bg-muted px-3 py-1.5 rounded-xl border border-border">
                  <span className="text-muted-foreground">Total Request: </span>
                  <strong className="text-foreground">{usageHistory.total_requests}</strong>
                </div>
                <div className="bg-purple-500/10 px-3 py-1.5 rounded-xl border border-purple-500/20 text-purple-400">
                  <span>Total Token: </span>
                  <strong>{usageHistory.total_tokens.toLocaleString()}</strong>
                </div>
              </div>
            )}
          </div>

          {loadingUsage ? (
            <div className="py-8 text-center text-xs text-muted-foreground">Memuat data riwayat penggunaan...</div>
          ) : !usageHistory || usageHistory.items.length === 0 ? (
            <div className="py-8 text-center text-xs text-muted-foreground border border-dashed rounded-xl border-border">
              Belum ada aktivitas pemanggilan gateway yang tercatat.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted-foreground uppercase font-semibold">
                    <th className="py-2.5 pr-3">Waktu</th>
                    <th className="py-2.5 px-3">Provider</th>
                    <th className="py-2.5 px-3">Model</th>
                    <th className="py-2.5 px-3">Tokens (In / Out)</th>
                    <th className="py-2.5 px-3">Latency</th>
                    <th className="py-2.5 pl-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono">
                  {usageHistory.items.map((log) => (
                    <tr key={log.id} className="hover:bg-muted/30">
                      <td className="py-3 pr-3 text-muted-foreground text-[11px]">
                        {new Date(log.created_at).toLocaleString("id-ID")}
                      </td>
                      <td className="py-3 px-3 uppercase font-bold text-foreground">
                        {log.provider || "openai"}
                      </td>
                      <td className="py-3 px-3 text-purple-400">
                        {log.model}
                      </td>
                      <td className="py-3 px-3 text-muted-foreground">
                        {log.tokens_in} / {log.tokens_out} ({log.total_tokens})
                      </td>
                      <td className="py-3 px-3 text-muted-foreground">
                        {log.latency_ms}ms
                      </td>
                      <td className="py-3 pl-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                            log.status === "success"
                              ? "bg-green-500/10 text-green-400 border border-green-500/20"
                              : "bg-red-500/10 text-red-400 border border-red-500/20"
                          }`}
                        >
                          {log.status === "success" ? "OK" : "ERROR"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
