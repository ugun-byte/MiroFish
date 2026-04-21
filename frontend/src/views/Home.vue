<template>
  <div class="home-container">
    <!-- ═══ Ambient Background Particles ═══ -->
    <canvas ref="particleCanvas" class="particle-bg"></canvas>

    <!-- ═══ Navigation ═══ -->
    <nav class="navbar">
      <div class="nav-brand-group">
        <div class="prism-icon-mark">◆</div>
        <div class="nav-brand">PRISM</div>
      </div>
      <div class="nav-links">
        <div class="active-model-badge" v-if="currentModelName" @click="showSettingsModal = true">
          <span class="model-dot" :class="{ 'dot-online': currentModelName }">●</span>
          <span class="model-name-text">{{ currentModelName }}</span>
        </div>
        <button class="settings-btn" @click="showSettingsModal = true" title="LLM Settings">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        </button>
        <LanguageSwitcher />
        <a href="https://github.com/666ghj/MiroFish" target="_blank" class="github-link">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>
        </a>
      </div>
    </nav>

    <div class="main-content">
      <!-- ═══ HERO SECTION ═══ -->
      <section class="hero-section">
        <div class="hero-left">
          <div class="tag-row">
            <span class="prism-tag">
              <span class="tag-diamond">◆</span>
              {{ $t('home.tagline') }}
            </span>
            <span class="version-text">{{ $t('home.version') }}</span>
          </div>
          
          <h1 class="main-title">
            <span class="title-line-1">{{ $t('home.heroTitle1') }}</span>
            <span class="title-line-2">
              <span class="gradient-text">{{ $t('home.heroTitle2') }}</span>
            </span>
          </h1>
          
          <div class="hero-desc">
            <p>
              <i18n-t keypath="home.heroDesc" tag="span">
                <template #brand><span class="highlight-brand">{{ $t('home.heroDescBrand') }}</span></template>
                <template #agentScale><span class="highlight-accent">{{ $t('home.heroDescAgentScale') }}</span></template>
                <template #optimalSolution><span class="highlight-code">{{ $t('home.heroDescOptimalSolution') }}</span></template>
              </i18n-t>
            </p>
            <p class="slogan-text">
              <span class="slogan-bar"></span>
              {{ $t('home.slogan') }}<span class="blinking-cursor">_</span>
            </p>
          </div>
        </div>
        
        <div class="hero-right">
          <div class="prism-logo-container">
            <div class="prism-logo-glow"></div>
            <img src="/prism-logo.png" alt="PRISM Logo" class="prism-logo" />
            <div class="prism-logo-ring"></div>
          </div>
          
          <button class="scroll-down-btn" @click="scrollToBottom">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 13l5 5 5-5M7 6l5 5 5-5"/></svg>
          </button>
        </div>
      </section>

      <!-- ═══ DASHBOARD SECTION ═══ -->
      <section class="dashboard-section">
        <!-- Left: Status & Workflow -->
        <div class="left-panel">
          <div class="panel-header">
            <span class="status-diamond">◆</span>
            {{ $t('home.systemStatus') }}
          </div>
          
          <h2 class="section-title">{{ $t('home.systemReady') }}</h2>
          <p class="section-desc">{{ $t('home.systemReadyDesc') }}</p>
          
          <div class="metrics-row">
            <div class="metric-card">
              <div class="metric-value">{{ $t('home.metricLowCost') }}</div>
              <div class="metric-label">{{ $t('home.metricLowCostDesc') }}</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">{{ $t('home.metricHighAvail') }}</div>
              <div class="metric-label">{{ $t('home.metricHighAvailDesc') }}</div>
            </div>
          </div>

          <!-- Workflow Steps -->
          <div class="steps-container">
            <div class="steps-header">
              <span class="steps-icon">◇</span>
              {{ $t('home.workflowSequence') }}
            </div>
            <div class="workflow-list">
              <div class="workflow-item" v-for="i in 5" :key="i">
                <span class="step-num">{{ String(i).padStart(2, '0') }}</span>
                <div class="step-connector" v-if="i < 5"></div>
                <div class="step-info">
                  <div class="step-title">{{ $t(`home.step${String(i).padStart(2,'0')}Title`) }}</div>
                  <div class="step-desc">{{ $t(`home.step${String(i).padStart(2,'0')}Desc`) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Console -->
        <div class="right-panel">
          <div class="console-box">
            <!-- Upload Area -->
            <div class="console-section">
              <div class="console-header">
                <span class="console-label">{{ $t('home.realitySeed') }}</span>
                <span class="console-meta">{{ $t('home.supportedFormats') }}</span>
              </div>
              
              <div 
                class="upload-zone"
                :class="{ 'drag-over': isDragOver, 'has-files': files.length > 0 }"
                @dragover.prevent="handleDragOver"
                @dragleave.prevent="handleDragLeave"
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
              >
                <input
                  ref="fileInput"
                  type="file"
                  multiple
                  accept=".pdf,.md,.txt"
                  @change="handleFileSelect"
                  style="display: none"
                  :disabled="loading"
                />
                
                <div v-if="files.length === 0" class="upload-placeholder">
                  <div class="upload-icon-wrap">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                  </div>
                  <div class="upload-title">{{ $t('home.dragToUpload') }}</div>
                  <div class="upload-hint">{{ $t('home.orBrowse') }}</div>
                </div>
                
                <div v-else class="file-list">
                  <div v-for="(file, index) in files" :key="index" class="file-item">
                    <span class="file-icon">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    </span>
                    <span class="file-name">{{ file.name }}</span>
                    <button @click.stop="removeFile(index)" class="remove-btn">×</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Divider -->
            <div class="console-divider">
              <span>{{ $t('home.inputParams') }}</span>
            </div>

            <!-- Input Area -->
            <div class="console-section">
              <div class="console-header">
                <span class="console-label">{{ $t('home.simulationPrompt') }}</span>
              </div>
              <div class="input-wrapper">
                <textarea
                  v-model="formData.simulationRequirement"
                  class="code-input"
                  :placeholder="$t('home.promptPlaceholder')"
                  rows="6"
                  :disabled="loading"
                ></textarea>
                <div class="model-badge">{{ $t('home.engineBadge') }}</div>
              </div>
            </div>

            <!-- PRISM Quant Analysis Ticker input -->
            <div class="console-section">
              <div class="console-header">
                <span class="console-label">PRISM Quant Target (Optional)</span>
              </div>
              <div class="input-wrapper">
                <input
                  v-model="formData.ticker"
                  type="text"
                  class="code-input ticker-input"
                  placeholder="e.g. AAPL, TSLA, 005930.KS"
                  :disabled="loading"
                  style="text-transform: uppercase;"
                />
              </div>
            </div>

            <!-- Launch Button -->
            <div class="console-section btn-section">
              <button 
                class="start-engine-btn"
                @click="startSimulation"
                :disabled="!canSubmit || loading"
              >
                <span class="btn-prism-icon">◆</span>
                <span v-if="!loading">{{ $t('home.startEngine') }}</span>
                <span v-else>{{ $t('home.initializing') }}</span>
                <svg class="btn-arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- History Database -->
      <HistoryDatabase />
    </div>

    <!-- ═══ LLM Settings Modal ═══ -->
    <Teleport to="body">
      <div v-if="showSettingsModal" class="settings-overlay" @click.self="showSettingsModal = false">
        <div class="settings-modal">
          <div class="modal-header">
            <div class="modal-title">
              <span class="modal-icon">⚙</span>
              {{ $t('settings.title') }}
            </div>
            <button class="modal-close" @click="showSettingsModal = false">✕</button>
          </div>

          <div class="modal-section">
            <div class="section-label">{{ $t('settings.quickPreset') }}</div>
            <div class="preset-grid">
              <div 
                v-for="preset in presets" 
                :key="preset.id"
                class="preset-card"
                :class="{ 'preset-active': selectedPresetId === preset.id }"
                @click="selectPreset(preset)"
              >
                <div class="preset-icon">{{ preset.icon }}</div>
                <div class="preset-info">
                  <div class="preset-name">{{ preset.name }}</div>
                  <div class="preset-desc">{{ preset.description }}</div>
                </div>
                <div v-if="selectedPresetId === preset.id" class="preset-check">✓</div>
              </div>
            </div>
          </div>

          <div class="modal-section">
            <div class="section-label">{{ $t('settings.manualConfig') }}</div>
            <div class="config-fields">
              <div class="config-field">
                <label>API Key</label>
                <input 
                  type="password" 
                  v-model="settingsForm.api_key"
                  :placeholder="$t('settings.apiKeyPlaceholder')"
                  class="config-input"
                />
              </div>
              <div class="config-field">
                <label>Base URL</label>
                <input 
                  type="text" 
                  v-model="settingsForm.base_url"
                  placeholder="https://openrouter.ai/api/v1"
                  class="config-input"
                />
              </div>
              <div class="config-field">
                <label>Model Name</label>
                <input 
                  type="text" 
                  v-model="settingsForm.model_name"
                  placeholder="openai-codex/gpt-5.4"
                  class="config-input"
                />
              </div>
            </div>
          </div>

          <div class="modal-actions">
            <div class="action-status" v-if="settingsStatus">
              <span :class="settingsStatusClass">{{ settingsStatus }}</span>
            </div>
            <div class="action-buttons">
              <button class="btn-cancel" @click="showSettingsModal = false">
                {{ $t('common.cancel') }}
              </button>
              <button class="btn-save" @click="saveSettings" :disabled="settingsSaving">
                <span v-if="!settingsSaving">{{ $t('settings.save') }}</span>
                <span v-else>{{ $t('settings.saving') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { getLLMConfig, updateLLMConfig, getLLMPresets } from '../api/config'

const router = useRouter()

// Form data
const formData = ref({ simulationRequirement: '', ticker: '' })
const files = ref([])
const loading = ref(false)
const error = ref('')
const isDragOver = ref(false)
const fileInput = ref(null)

// Particle canvas
const particleCanvas = ref(null)
let animationId = null

const canSubmit = computed(() => {
  return formData.value.simulationRequirement.trim() !== '' && files.value.length > 0
})

// File handling
const triggerFileInput = () => { if (!loading.value) fileInput.value?.click() }
const handleFileSelect = (event) => addFiles(Array.from(event.target.files))
const handleDragOver = () => { if (!loading.value) isDragOver.value = true }
const handleDragLeave = () => { isDragOver.value = false }
const handleDrop = (e) => {
  isDragOver.value = false
  if (loading.value) return
  addFiles(Array.from(e.dataTransfer.files))
}

const addFiles = (newFiles) => {
  const validFiles = newFiles.filter(file => {
    const ext = file.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'txt'].includes(ext)
  })
  files.value.push(...validFiles)
}

const removeFile = (index) => { files.value.splice(index, 1) }

const scrollToBottom = () => {
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
}

const startSimulation = () => {
  if (!canSubmit.value || loading.value) return
  let finalRequirement = formData.value.simulationRequirement
  if (formData.value.ticker.trim()) {
    finalRequirement += `\n[Quant Target Ticker: ${formData.value.ticker.trim().toUpperCase()}]`
  }
  
  import('../store/pendingUpload.js').then(({ setPendingUpload }) => {
    setPendingUpload(files.value, finalRequirement)
    router.push({ name: 'Process', params: { projectId: 'new' } })
  })
}

// ═══ Particle Background ═══
const initParticles = () => {
  const canvas = particleCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let particles = []
  
  const resize = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  resize()
  window.addEventListener('resize', resize)
  
  // Create particles
  for (let i = 0; i < 60; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      radius: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.4 + 0.1,
    })
  }
  
  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    particles.forEach((p, i) => {
      p.x += p.vx
      p.y += p.vy
      
      if (p.x < 0) p.x = canvas.width
      if (p.x > canvas.width) p.x = 0
      if (p.y < 0) p.y = canvas.height
      if (p.y > canvas.height) p.y = 0
      
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(60, 120, 255, ${p.alpha})`
      ctx.fill()
      
      // Connect nearby particles
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[j].x - p.x
        const dy = particles[j].y - p.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 150) {
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.strokeStyle = `rgba(60, 120, 255, ${0.08 * (1 - dist / 150)})`
          ctx.lineWidth = 0.5
          ctx.stroke()
        }
      }
    })
    
    animationId = requestAnimationFrame(animate)
  }
  animate()
}

// ═══ LLM Settings ═══
const showSettingsModal = ref(false)
const currentModelName = ref('')
const presets = ref([])
const selectedPresetId = ref('custom')
const settingsForm = ref({ api_key: '', base_url: '', model_name: '' })
const settingsSaving = ref(false)
const settingsStatus = ref('')
const settingsStatusClass = ref('')

const selectPreset = (preset) => {
  selectedPresetId.value = preset.id
  if (preset.id !== 'custom') {
    settingsForm.value.base_url = preset.base_url
    settingsForm.value.model_name = preset.model_name
    if (preset.default_api_key) {
      settingsForm.value.api_key = preset.default_api_key
    } else if (!preset.requires_api_key) {
      settingsForm.value.api_key = preset.default_api_key || 'ollama'
    }
  }
}

const saveSettings = async () => {
  settingsSaving.value = true
  settingsStatus.value = ''
  try {
    const payload = {}
    if (settingsForm.value.api_key) payload.api_key = settingsForm.value.api_key
    if (settingsForm.value.base_url) payload.base_url = settingsForm.value.base_url
    if (settingsForm.value.model_name) payload.model_name = settingsForm.value.model_name
    const res = await updateLLMConfig(payload)
    if (res.success) {
      currentModelName.value = res.data.model_name
      selectedPresetId.value = res.data.active_preset_id
      settingsStatus.value = '✓ 설정이 저장되었습니다!'
      settingsStatusClass.value = 'status-success'
      setTimeout(() => { showSettingsModal.value = false; settingsStatus.value = '' }, 1500)
    }
  } catch (err) {
    settingsStatus.value = '✗ 저장 실패: ' + (err.message || '알 수 없는 오류')
    settingsStatusClass.value = 'status-error'
  } finally { settingsSaving.value = false }
}

const loadCurrentConfig = async () => {
  try {
    const [configRes, presetsRes] = await Promise.all([getLLMConfig(), getLLMPresets()])
    if (configRes.success) {
      currentModelName.value = configRes.data.model_name
      selectedPresetId.value = configRes.data.active_preset_id
      settingsForm.value.base_url = configRes.data.base_url
      settingsForm.value.model_name = configRes.data.model_name
    }
    if (presetsRes.success) { presets.value = presetsRes.data.presets }
  } catch (err) { console.warn('LLM config load failed:', err) }
}

onMounted(() => {
  loadCurrentConfig()
  initParticles()
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
})
</script>

<style scoped>
/* ═══ PARTICLE BACKGROUND ═══ */
.particle-bg {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  z-index: 0;
  pointer-events: none;
}

/* ═══ CONTAINER ═══ */
.home-container {
  min-height: 100vh;
  position: relative;
  font-family: var(--font-main);
  color: var(--text-main);
}

/* ═══ NAVIGATION ═══ */
.navbar {
  height: 64px;
  background: rgba(2, 0, 10, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--bg-panel-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.prism-icon-mark {
  color: var(--prism-blue);
  font-size: 1.2rem;
  text-shadow: var(--glow-blue);
  animation: prism-pulse 3s ease-in-out infinite;
}

.nav-brand {
  font-family: var(--font-display);
  font-weight: 800;
  letter-spacing: 4px;
  font-size: 1.3rem;
  background: linear-gradient(135deg, var(--prism-blue), var(--prism-indigo));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 14px;
}

.github-link {
  color: var(--text-muted);
  display: flex;
  align-items: center;
  transition: all 0.3s;
  padding: 8px;
  border-radius: 8px;
}
.github-link:hover {
  color: var(--prism-blue);
  background: rgba(60, 120, 255, 0.08);
}

/* ═══ MAIN CONTENT ═══ */
.main-content {
  max-width: 1440px;
  margin: 0 auto;
  padding: 60px 48px;
  position: relative;
  z-index: 1;
}

/* ═══ HERO SECTION ═══ */
.hero-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 100px;
  min-height: 480px;
}

.hero-left {
  flex: 1;
  padding-right: 80px;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.prism-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, rgba(60, 120, 255, 0.12), rgba(99, 102, 241, 0.08));
  border: 1px solid rgba(60, 120, 255, 0.3);
  color: var(--prism-blue);
  padding: 5px 14px;
  font-family: var(--font-display);
  font-weight: 600;
  letter-spacing: 1.5px;
  font-size: 0.75rem;
  border-radius: 20px;
  text-transform: uppercase;
  box-shadow: var(--glow-blue);
}

.tag-diamond {
  font-size: 0.6rem;
  animation: prism-pulse 2s ease-in-out infinite;
}

.version-text {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 0.8rem;
  letter-spacing: 0.5px;
}

.main-title {
  margin: 0 0 36px 0;
}

.title-line-1 {
  display: block;
  font-family: var(--font-display);
  font-size: 3.8rem;
  font-weight: 300;
  line-height: 1.15;
  letter-spacing: -1px;
  color: var(--text-main);
}

.title-line-2 {
  display: block;
  line-height: 1.15;
}

.gradient-text {
  font-family: var(--font-display);
  font-size: 4.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--prism-blue) 0%, var(--prism-indigo) 40%, var(--prism-violet) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -2px;
  filter: drop-shadow(0 0 20px rgba(60, 120, 255, 0.25));
}

.hero-desc {
  font-size: 1.05rem;
  line-height: 1.85;
  color: var(--text-secondary);
  max-width: 600px;
  font-weight: 400;
}

.hero-desc p { margin-bottom: 1.5rem; }

.highlight-brand {
  color: var(--prism-blue);
  font-weight: 700;
  font-family: var(--font-display);
}

.highlight-accent {
  color: var(--prism-indigo);
  font-weight: 700;
  font-family: var(--font-mono);
  font-size: 0.95em;
}

.highlight-code {
  background: rgba(60, 120, 255, 0.1);
  border: 1px solid rgba(60, 120, 255, 0.2);
  padding: 2px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.88em;
  color: var(--prism-blue);
  font-weight: 600;
}

.slogan-text {
  font-size: 1.15rem;
  font-weight: 500;
  color: var(--text-main);
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 12px;
}

.slogan-bar {
  width: 3px;
  height: 24px;
  background: linear-gradient(180deg, var(--prism-blue), var(--prism-violet));
  border-radius: 2px;
  flex-shrink: 0;
  box-shadow: var(--glow-blue);
}

.blinking-cursor {
  color: var(--prism-blue);
  animation: blink 1s step-end infinite;
  font-weight: 700;
  font-family: var(--font-mono);
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ═══ PRISM LOGO ═══ */
.hero-right {
  flex: 0 0 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
}

.prism-logo-container {
  position: relative;
  width: 360px;
  height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.prism-logo-glow {
  position: absolute;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(60, 120, 255, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  animation: float 6s ease-in-out infinite;
}

.prism-logo {
  width: 280px;
  height: 280px;
  object-fit: contain;
  position: relative;
  z-index: 2;
  filter: drop-shadow(0 0 30px rgba(60, 120, 255, 0.3));
  animation: float 6s ease-in-out infinite;
}

.prism-logo-ring {
  position: absolute;
  width: 340px;
  height: 340px;
  border: 1px solid rgba(60, 120, 255, 0.15);
  border-radius: 50%;
  animation: prism-glow 4s ease-in-out infinite;
}

.scroll-down-btn {
  width: 44px;
  height: 44px;
  border: 1px solid var(--bg-panel-border);
  background: var(--bg-panel);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: all 0.3s;
}
.scroll-down-btn:hover {
  color: var(--prism-blue);
  border-color: var(--prism-blue);
  box-shadow: var(--glow-blue);
  transform: translateY(2px);
}

/* ═══ DASHBOARD SECTION ═══ */
.dashboard-section {
  display: flex;
  gap: 60px;
  padding-top: 80px;
  position: relative;
  align-items: flex-start;
}

.dashboard-section::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--prism-blue), var(--prism-indigo), transparent);
  box-shadow: var(--glow-blue);
}

/* Left Panel */
.left-panel { flex: 0.85; }

.panel-header {
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.status-diamond {
  color: var(--prism-blue);
  font-size: 0.7rem;
  text-shadow: var(--glow-blue);
}

.section-title {
  font-family: var(--font-display);
  font-size: 2.2rem;
  font-weight: 600;
  margin: 0 0 12px 0;
  letter-spacing: -0.5px;
}

.section-desc {
  color: var(--text-secondary);
  margin-bottom: 28px;
  line-height: 1.7;
  font-size: 0.95rem;
}

/* Metrics */
.metrics-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  border: 1px solid var(--bg-panel-border);
  background: var(--bg-panel);
  backdrop-filter: blur(12px);
  border-radius: var(--radius-md);
  padding: 20px 28px;
  min-width: 160px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.metric-card:hover {
  transform: translateY(-3px);
  border-color: var(--prism-blue);
  box-shadow: var(--glow-blue);
}

.metric-value {
  font-family: var(--font-display);
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 4px;
  background: linear-gradient(135deg, var(--text-main), var(--prism-blue));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.metric-label {
  font-size: 0.82rem;
  color: var(--text-muted);
}

/* Steps */
.steps-container {
  border: 1px solid var(--bg-panel-border);
  background: var(--bg-panel);
  backdrop-filter: blur(12px);
  border-radius: var(--radius-lg);
  padding: 28px;
}

.steps-header {
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.steps-icon {
  color: var(--prism-blue);
  font-size: 1rem;
}

.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.workflow-item {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  position: relative;
}

.step-num {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--prism-blue);
  opacity: 0.5;
  min-width: 22px;
  padding-top: 2px;
}

.step-info { flex: 1; }

.step-title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 3px;
  letter-spacing: 0.3px;
}

.step-desc {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.5;
}

/* ═══ RIGHT PANEL — CONSOLE ═══ */
.right-panel { flex: 1.15; }

.console-box {
  border: 1px solid var(--bg-panel-border);
  background: var(--bg-panel);
  backdrop-filter: blur(16px);
  border-radius: var(--radius-lg);
  padding: 6px;
  box-shadow: var(--shadow-deep), 0 0 40px rgba(60, 120, 255, 0.05);
  position: relative;
  overflow: hidden;
}

.console-box::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--prism-blue), var(--prism-indigo), transparent);
  opacity: 0.6;
}

.console-section { padding: 20px; }
.console-section.btn-section { padding-top: 0; }

.console-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 14px;
}

.console-label {
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 1px;
  text-transform: uppercase;
}

.console-meta {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  opacity: 0.7;
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed rgba(60, 120, 255, 0.25);
  background: rgba(60, 120, 255, 0.03);
  border-radius: var(--radius-md);
  height: 190px;
  overflow-y: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}
.upload-zone:hover,
.upload-zone.drag-over {
  border-color: var(--prism-blue);
  background: rgba(60, 120, 255, 0.08);
  box-shadow: inset 0 0 30px rgba(60, 120, 255, 0.06), var(--glow-blue);
}
.upload-zone.has-files { align-items: flex-start; }

.upload-placeholder { text-align: center; }

.upload-icon-wrap {
  width: 48px; height: 48px;
  border: 1px solid var(--bg-panel-border);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
  color: var(--prism-blue);
  background: rgba(60, 120, 255, 0.06);
}

.upload-title {
  font-weight: 500;
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.upload-hint {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--text-muted);
}

.file-list {
  width: 100%;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  background: rgba(60, 120, 255, 0.05);
  padding: 8px 14px;
  border: 1px solid var(--bg-panel-border);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.82rem;
  gap: 10px;
}

.file-icon { color: var(--prism-blue); flex-shrink: 0; }
.file-name { flex: 1; }
.remove-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: var(--text-muted);
  padding: 0 4px;
}
.remove-btn:hover { color: var(--error); }

/* Divider */
.console-divider {
  display: flex;
  align-items: center;
  margin: 6px 0;
  padding: 0 8px;
}

.console-divider::before,
.console-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--bg-panel-border), transparent);
}

.console-divider span {
  padding: 0 14px;
  font-family: var(--font-display);
  font-size: 0.65rem;
  color: var(--text-muted);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  font-weight: 600;
}

/* Code Input */
.input-wrapper {
  position: relative;
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.code-input {
  width: 100%;
  background: rgba(2, 0, 10, 0.8);
  border: 1px solid var(--bg-panel-border);
  color: var(--text-accent);
  font-family: var(--font-mono);
  font-size: 0.9rem;
  padding: 16px;
  resize: none;
  outline: none;
  border-radius: var(--radius-sm);
  transition: all 0.3s;
}
.code-input:focus {
  border-color: var(--prism-blue);
  box-shadow: 0 0 20px rgba(60, 120, 255, 0.1), inset 0 0 10px rgba(60, 120, 255, 0.04);
}
.code-input::placeholder { color: var(--text-muted); opacity: 0.5; }

.model-badge {
  position: absolute;
  bottom: 10px; right: 14px;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--text-muted);
  opacity: 0.5;
}

/* ═══ START ENGINE BUTTON ═══ */
.start-engine-btn {
  width: 100%;
  padding: 16px 24px;
  background: linear-gradient(135deg, rgba(60, 120, 255, 0.12), rgba(99, 102, 241, 0.08));
  color: var(--prism-blue);
  border: 1px solid rgba(60, 120, 255, 0.3);
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: 3px;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  border-radius: var(--radius-md);
  text-transform: uppercase;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.start-engine-btn::before {
  content: '';
  position: absolute;
  top: 0; left: -100%; right: 0; bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(60, 120, 255, 0.1), transparent);
  transition: left 0.6s;
}
.start-engine-btn:not(:disabled):hover::before { left: 100%; }

.start-engine-btn:not(:disabled):hover {
  background: linear-gradient(135deg, var(--prism-blue), var(--prism-indigo));
  color: white;
  border-color: transparent;
  box-shadow: var(--glow-prism-strong);
  transform: translateY(-2px);
}

.start-engine-btn:not(:disabled):active { transform: translateY(0); }

.start-engine-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.btn-prism-icon {
  font-size: 0.85rem;
  opacity: 0.8;
}

.btn-arrow {
  transition: transform 0.3s;
}
.start-engine-btn:hover .btn-arrow { transform: translateX(4px); }

/* ═══ RESPONSIVE ═══ */
@media (max-width: 1024px) {
  .hero-section { flex-direction: column; align-items: flex-start; }
  .hero-left { padding-right: 0; margin-bottom: 40px; }
  .hero-right { flex: unset; width: 100%; align-items: center; }
  .prism-logo { width: 200px; height: 200px; }
  .dashboard-section { flex-direction: column; }
  .title-line-1 { font-size: 2.5rem; }
  .gradient-text { font-size: 3rem; }
}

/* ═══ MODEL BADGE ═══ */
.active-model-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border: 1px solid rgba(60, 120, 255, 0.2);
  border-radius: 20px;
  background: rgba(60, 120, 255, 0.05);
  cursor: pointer;
  transition: all 0.3s;
  font-family: var(--font-mono);
  font-size: 0.75rem;
}
.active-model-badge:hover {
  background: rgba(60, 120, 255, 0.1);
  border-color: rgba(60, 120, 255, 0.4);
  box-shadow: var(--glow-blue);
}
.model-dot { font-size: 0.55rem; color: #475569; }
.model-dot.dot-online {
  color: var(--success);
  text-shadow: var(--success-glow);
  animation: prism-pulse 2s ease-in-out infinite;
}
.model-name-text { color: var(--prism-blue); letter-spacing: 0.5px; }

.settings-btn {
  background: none;
  border: 1px solid rgba(60, 120, 255, 0.15);
  color: var(--text-muted);
  width: 36px; height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}
.settings-btn:hover {
  color: var(--prism-blue);
  border-color: var(--prism-blue);
  background: rgba(60, 120, 255, 0.06);
  box-shadow: var(--glow-blue);
  transform: rotate(45deg);
}

/* ═══ SETTINGS MODAL ═══ */
.settings-overlay {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.25s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.settings-modal {
  width: 560px;
  max-height: 85vh;
  overflow-y: auto;
  background: linear-gradient(135deg, rgba(4, 2, 16, 0.97), rgba(8, 4, 24, 0.97));
  border: 1px solid rgba(60, 120, 255, 0.18);
  border-radius: var(--radius-lg);
  box-shadow: 0 0 60px rgba(60, 120, 255, 0.08), var(--shadow-deep);
  animation: modalSlideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes modalSlideUp {
  from { transform: translateY(30px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(60, 120, 255, 0.1);
}
.modal-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--prism-blue);
  text-shadow: var(--glow-blue);
}
.modal-icon { font-size: 1.3rem; }
.modal-close {
  background: none; border: none;
  color: var(--text-muted);
  font-size: 1.2rem;
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px;
  transition: all 0.2s;
}
.modal-close:hover { color: var(--error); background: rgba(239, 68, 68, 0.1); }

.modal-section { padding: 20px 24px; }
.section-label {
  font-family: var(--font-display);
  font-size: 0.78rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 14px;
  font-weight: 600;
}

.preset-grid { display: flex; flex-direction: column; gap: 10px; }
.preset-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border: 1px solid rgba(60, 120, 255, 0.08);
  border-radius: var(--radius-md);
  background: rgba(60, 120, 255, 0.02);
  cursor: pointer;
  transition: all 0.3s;
}
.preset-card:hover {
  border-color: rgba(60, 120, 255, 0.25);
  background: rgba(60, 120, 255, 0.05);
  transform: translateX(4px);
}
.preset-card.preset-active {
  border-color: var(--prism-blue);
  background: rgba(60, 120, 255, 0.08);
  box-shadow: var(--glow-blue);
}
.preset-icon { font-size: 1.8rem; width: 40px; text-align: center; flex-shrink: 0; }
.preset-info { flex: 1; min-width: 0; }
.preset-name {
  font-family: var(--font-mono);
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 2px;
}
.preset-desc {
  font-size: 0.73rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.preset-check {
  color: var(--prism-blue);
  font-weight: 700;
  font-size: 1.2rem;
  text-shadow: var(--glow-blue);
}

.config-fields { display: flex; flex-direction: column; gap: 14px; }
.config-field label {
  display: block;
  font-family: var(--font-mono);
  font-size: 0.73rem;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.config-input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(60, 120, 255, 0.12);
  border-radius: 8px;
  color: var(--text-main);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  outline: none;
  transition: all 0.3s;
  box-sizing: border-box;
}
.config-input:focus {
  border-color: var(--prism-blue);
  background: rgba(60, 120, 255, 0.04);
  box-shadow: 0 0 12px rgba(60, 120, 255, 0.1);
}
.config-input::placeholder { color: #374151; }

.modal-actions {
  padding: 16px 24px 20px;
  border-top: 1px solid rgba(60, 120, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.action-status { font-size: 0.8rem; font-family: var(--font-mono); }
.status-success { color: var(--success); text-shadow: var(--success-glow); }
.status-error { color: var(--error); text-shadow: var(--error-glow); }
.action-buttons { display: flex; gap: 12px; }
.btn-cancel {
  padding: 8px 20px;
  border: 1px solid rgba(60, 120, 255, 0.15);
  border-radius: 8px;
  background: transparent;
  color: var(--text-muted);
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 600;
}
.btn-cancel:hover { border-color: var(--text-muted); color: var(--text-main); }
.btn-save {
  padding: 8px 28px;
  border: 1px solid var(--prism-blue);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(60, 120, 255, 0.15), rgba(99, 102, 241, 0.1));
  color: var(--prism-blue);
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 700;
}
.btn-save:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--prism-blue), var(--prism-indigo));
  color: white;
  box-shadow: var(--glow-prism-strong);
}
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
.ticker-input {
  resize: none;
  height: 48px;
  font-size: 1.1rem;
  letter-spacing: 2px;
  font-weight: 600;
  color: var(--prism-blue);
}
.ticker-input::placeholder {
  font-weight: 400;
  letter-spacing: 1px;
}
</style>

<style>
/* English locale adjustments */
html[lang="en"] .main-title .title-line-1 {
  font-size: 3.2rem;
}
html[lang="en"] .gradient-text {
  font-size: 3.8rem;
}
html[lang="en"] .hero-desc {
  text-align: left;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>
