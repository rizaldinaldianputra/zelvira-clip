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
  ArrowRight,
  ExternalLink,
  Info,
} from "lucide-react"
import { api } from "@/lib/api"
import { AIKey, AgentModelMapping } from "@/types"

export const Settings: React.FC = () => {
  const queryClient = useQueryClient()

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

  // Queries
  const { data: keys = [], isLoading: loadingKeys } = useQuery({
    queryKey: ["aiKeys"],
    queryFn: api.getKeys,
  })

  const { data: allModels = [] } = useQuery({
    queryKey: ["allModels"],
    queryFn: () => api.getModels(),
  })

  const getModelsForKey = (keyId: string) => {
    const selectedKey = keys.find((k) => k.id === keyId)
    const prov = selectedKey ? selectedKey.provider : provider
    const filtered = allModels.filter((m) => {
      // Return provider-specific models or all if not matched
      return true
    })
    return allModels
  }

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

  // Mutations
  const addKeyMutation = useMutation({
    mutationFn: (data: { provider: string; api_key: string; base_url?: string }) => api.addKey(data),
    onSuccess: () => {
      // Clear key from state immediately after save as specified
      setApiKey("")
      setBaseUrl("")
      setTestResult(null)
      setKeyError(null)
      queryClient.invalidateQueries({ queryKey: ["aiKeys"] })
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
      queryClient.invalidateQueries({ queryKey: ["agentModels"] })
    },
  })

  const updateAgentModelsMutation = useMutation({
    mutationFn: (mappings: AgentModelMapping[]) => api.updateAgentModels(mappings),
    onSuccess: () => {
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
      queryClient.invalidateQueries({ queryKey: ["agentModels"] })
    },
  })

  // Test connection
  const handleTestConnection = async () => {
    if (!apiKey.trim()) {
      setTestResult({ success: false, message: "Masukkan API key terlebih dahulu untuk pengujian." })
      return
    }

    setTesting(true)
    setTestResult(null)

    try {
      const res = await api.testKey({
        provider,
        api_key: apiKey.trim(),
        model: testModel,
        base_url: baseUrl.trim() || undefined,
      })
      setTestResult(res)
    } catch (err: any) {
      setTestResult({ success: false, message: err.message || "Pengujian koneksi gagal." })
    } finally {
      setTesting(false)
    }
  }

  const handleSaveKey = (e: React.FormEvent) => {
    e.preventDefault()
    if (!apiKey.trim()) {
      setKeyError("Kunci API tidak boleh kosong.")
      return
    }
    addKeyMutation.mutate({
      provider,
      api_key: apiKey.trim(),
      base_url: provider === "custom" ? baseUrl.trim() : undefined,
    })
  }

  const handleSaveAgentModels = (e: React.FormEvent) => {
    e.preventDefault()
    const payload: AgentModelMapping[] = Object.entries(agentMappings).map(([agent_name, conf]) => ({
      agent_name,
      key_id: conf.key_id || undefined,
      model: conf.model,
    }))
    updateAgentModelsMutation.mutate(payload)
  }

  return (
    <div className="container max-w-4xl mx-auto px-4 py-8 sm:py-12 space-y-10">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight flex items-center space-x-2">
          <KeyRound className="h-7 w-7 text-purple-600" />
          <span>Pengaturan Kunci AI (BYOK)</span>
        </h1>
        <p className="text-sm text-muted-foreground">
          Gunakan model dan API key Anda sendiri. Kunci dienkripsi menggunakan standar Fernet di database dan tidak pernah dikirimkan kembali ke antarmuka.
        </p>
      </div>

      {/* Security notice */}
      <div className="flex items-start space-x-3 rounded-2xl border border-purple-500/20 bg-purple-500/5 p-4 text-xs text-muted-foreground">
        <ShieldCheck className="h-5 w-5 text-purple-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="text-foreground">Jaminan Keamanan & Privasi:</strong>
          <p>
            API key hanya digunakan secara eksklusif untuk menjalankan job milik Anda. Key disimpan terenkripsi dengan Fernet (AES-128-CBC + HMAC-SHA256) dan dilindungi dari SSRF (Private IP Blocking).
          </p>
        </div>
      </div>

      {/* SECTION 1: Kunci API */}
      <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-sm space-y-6">
        <div className="flex items-center space-x-2 border-b border-border pb-4">
          <Plus className="h-5 w-5 text-purple-600" />
          <h2 className="text-lg font-bold">1. Tambah Kunci API Baru</h2>
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
                  else if (val === "nvidia") {
                    setTestModel("meta/llama-3.1-70b-instruct")
                    setBaseUrl("https://integrate.api.nvidia.com/v1")
                  } else if (val === "openrouter") setTestModel("meta-llama/llama-3.1-8b-instruct")
                }}
                className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none"
              >
                <option value="openai">OpenAI (Official)</option>
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="gemini">Google Gemini</option>
                <option value="deepseek">DeepSeek</option>
                <option value="openrouter">OpenRouter</option>
                <option value="nvidia">NVIDIA NIM (build.nvidia.com)</option>
                <option value="custom">Custom (OpenAI-Compatible Base URL)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Model Pengujian</label>
              <div className="space-y-1.5">
                {allModels.length > 0 ? (
                  <select
                    value={testModel}
                    onChange={(e) => setTestModel(e.target.value)}
                    className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none"
                  >
                    {allModels
                      .filter((m) => provider === "custom" || m.provider === provider || m.id.startsWith(provider))
                      .concat(allModels.filter((m) => provider !== "custom" && m.provider !== provider && !m.id.startsWith(provider)))
                      .map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} ({m.id})
                        </option>
                      ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={testModel}
                    onChange={(e) => setTestModel(e.target.value)}
                    placeholder="misal: gpt-4o-mini, meta/llama-3.1-70b-instruct"
                    className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none"
                  />
                )}
                {/* Manual input override if user wants custom string */}
                <input
                  type="text"
                  value={testModel}
                  onChange={(e) => setTestModel(e.target.value)}
                  placeholder="Atau ketik model ID manual di sini..."
                  className="w-full rounded-lg border border-dashed border-border/70 bg-muted/20 px-3 py-1.5 text-xs focus:border-purple-600 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {(provider === "custom" || provider === "nvidia") && (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase">
                Base URL ({provider === "nvidia" ? "NVIDIA NIM Endpoint" : "OpenAI Compatible"})
              </label>
              <input
                type="url"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder={provider === "nvidia" ? "https://integrate.api.nvidia.com/v1" : "https://ai.sumopod.com/v1"}
                className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none"
              />
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Masukkan API key Anda (contoh: sk-...)"
              className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:border-purple-600 focus:outline-none"
            />
          </div>

          {/* Test Status feedback */}
          {testResult && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-center space-x-2 ${
                testResult.success
                  ? "bg-green-500/10 text-green-500 border-green-500/20"
                  : "bg-red-500/10 text-red-500 border-red-500/20"
              }`}
            >
              {testResult.success ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : <AlertCircle className="h-4 w-4 shrink-0" />}
              <div>
                <span>{testResult.message}</span>
                {testResult.latency_ms ? <span className="ml-2 font-mono">({testResult.latency_ms} ms)</span> : null}
              </div>
            </div>
          )}

          <div className="flex items-center space-x-3 pt-2">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testing || !apiKey}
              className="px-4 py-2.5 rounded-xl border border-border text-xs font-semibold hover:bg-muted transition disabled:opacity-50"
            >
              {testing ? "Menguji Koneksi..." : "Tes Koneksi"}
            </button>

            <button
              type="submit"
              disabled={addKeyMutation.isPending || !apiKey}
              className="flex-1 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-sm transition disabled:opacity-50"
            >
              {addKeyMutation.isPending ? "Menyimpan..." : "Simpan Kunci Terenkripsi"}
            </button>
          </div>
        </form>

        {/* Saved Keys List */}
        <div className="pt-6 border-t border-border space-y-3">
          <h3 className="text-sm font-bold text-foreground">Daftar Kunci Tersimpan</h3>
          {keys.length === 0 ? (
            <p className="text-xs text-muted-foreground">Belum ada kunci API tersimpan.</p>
          ) : (
            <div className="space-y-2">
              {keys.map((k) => (
                <div
                  key={k.id}
                  className="flex items-center justify-between p-3 rounded-xl border border-border bg-muted/30 text-xs"
                >
                  <div className="flex items-center space-x-3">
                    <span className="font-bold uppercase px-2 py-0.5 rounded bg-purple-600/10 text-purple-600 border border-purple-600/20">
                      {k.provider}
                    </span>
                    <span className="font-mono text-muted-foreground">{k.key_hint}</span>
                    {k.base_url && <span className="text-[10px] text-muted-foreground truncate max-w-[180px]">{k.base_url}</span>}
                  </div>

                  <button
                    onClick={() => {
                      if (confirm("Hapus kunci ini?")) {
                        deleteKeyMutation.mutate(k.id)
                      }
                    }}
                    className="p-1.5 text-muted-foreground hover:text-red-500 rounded-md transition"
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

      {/* SECTION 2: Model per Tugas */}
      <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-sm space-y-6">
        <div className="flex items-center space-x-2 border-b border-border pb-4">
          <Cpu className="h-5 w-5 text-indigo-500" />
          <h2 className="text-lg font-bold">2. Penugasan Model AI per Agent</h2>
        </div>

        <div className="flex items-start space-x-2 p-3 rounded-xl bg-muted/50 text-xs text-muted-foreground">
          <Info className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
          <p>
            <strong>Tips Efisiensi:</strong> Moment Finder memproses banyak teks per chunk sehingga cukup menggunakan model murah (misal <code>gpt-4o-mini</code> atau <code>gemini-1.5-flash</code>). Ranker membutuhkan penalaran tinggi untuk memilih klip terbaik sehingga disarankan menggunakan model unggulan (misal <code>gpt-4o</code> atau <code>claude-3-5-sonnet</code>).
          </p>
        </div>

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
                  <th className="py-2 pr-4 font-semibold">Tugas Agent</th>
                  <th className="py-2 px-4 font-semibold">Kunci API Terpilih</th>
                  <th className="py-2 pl-4 font-semibold">Nama Model (Ketik / Pilih)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {/* 1. Moment Finder */}
                <tr>
                  <td className="py-4 pr-4">
                    <p className="font-bold text-foreground">Moment Finder</p>
                    <p className="text-xs text-muted-foreground">Mendeteksi momen viral di tiap chunk</p>
                  </td>
                  <td className="py-4 px-4">
                    <select
                      value={agentMappings["moment_finder"]?.key_id || ""}
                      onChange={(e) =>
                        setAgentMappings((prev) => ({
                          ...prev,
                          moment_finder: { ...prev.moment_finder, key_id: e.target.value },
                        }))
                      }
                      className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                    >
                      <option value="">Paling Sesuai / Otomatis</option>
                      {keys.map((k) => (
                        <option key={k.id} value={k.id}>
                          {k.provider.toUpperCase()} ({k.key_hint})
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-4 pl-4">
                    <select
                      value={agentMappings["moment_finder"]?.model || "gpt-4o-mini"}
                      onChange={(e) =>
                        setAgentMappings((prev) => ({
                          ...prev,
                          moment_finder: { ...prev.moment_finder, model: e.target.value },
                        }))
                      }
                      className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                    >
                      {allModels.map((m) => (
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
                    <p className="text-xs text-muted-foreground">Menilai dan memilih top 5 klip terbaik</p>
                  </td>
                  <td className="py-4 px-4">
                    <select
                      value={agentMappings["ranker"]?.key_id || ""}
                      onChange={(e) =>
                        setAgentMappings((prev) => ({
                          ...prev,
                          ranker: { ...prev.ranker, key_id: e.target.value },
                        }))
                      }
                      className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                    >
                      <option value="">Paling Sesuai / Otomatis</option>
                      {keys.map((k) => (
                        <option key={k.id} value={k.id}>
                          {k.provider.toUpperCase()} ({k.key_hint})
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-4 pl-4">
                    <select
                      value={agentMappings["ranker"]?.model || "gpt-4o"}
                      onChange={(e) =>
                        setAgentMappings((prev) => ({
                          ...prev,
                          ranker: { ...prev.ranker, model: e.target.value },
                        }))
                      }
                      className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                    >
                      {allModels.map((m) => (
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
                    <p className="text-xs text-muted-foreground">Membuat judul viral, caption & 5 hashtag</p>
                  </td>
                  <td className="py-4 px-4">
                    <select
                      value={agentMappings["metadata"]?.key_id || ""}
                      onChange={(e) =>
                        setAgentMappings((prev) => ({
                          ...prev,
                          metadata: { ...prev.metadata, key_id: e.target.value },
                        }))
                      }
                      className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                    >
                      <option value="">Paling Sesuai / Otomatis</option>
                      {keys.map((k) => (
                        <option key={k.id} value={k.id}>
                          {k.provider.toUpperCase()} ({k.key_hint})
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-4 pl-4">
                    <select
                      value={agentMappings["metadata"]?.model || "gpt-4o-mini"}
                      onChange={(e) =>
                        setAgentMappings((prev) => ({
                          ...prev,
                          metadata: { ...prev.metadata, model: e.target.value },
                        }))
                      }
                      className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:border-purple-600 focus:outline-none"
                    >
                      {allModels.map((m) => (
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
      </div>
    </div>
  )
}
