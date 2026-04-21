<template>
  <router-view />
</template>

<script setup>
// PRISM - AI Prediction Engine
</script>

<style>
/* 🌐 GLOBAL CSS VARIABLES - PRISM DESIGN SYSTEM */
:root {
  /* ═══ Deep space backgrounds ═══ */
  --bg-deep: #02000a;
  --bg-surface: #080414;
  --bg-panel: rgba(8, 4, 24, 0.75);
  --bg-panel-hover: rgba(12, 6, 32, 0.85);
  --bg-panel-border: rgba(60, 120, 255, 0.15);
  --bg-panel-border-hover: rgba(60, 120, 255, 0.35);
  
  /* ═══ Text hierarchy ═══ */
  --text-main: #e8ecf4;
  --text-secondary: #a0aec0;
  --text-muted: #64748b;
  --text-accent: #7eb8ff;
  
  /* ═══ Primary: Electric Blue Spectrum ═══ */
  --blue-50: #e6f0ff;
  --blue-100: #b3d4ff;
  --blue-200: #80b8ff;
  --blue-300: #4d9cff;
  --blue-400: #1a80ff;
  --blue-500: #0066ff;
  --blue-600: #0052cc;
  --blue-700: #003d99;
  --blue-800: #002966;
  --blue-900: #001433;
  
  /* ═══ Accent: Prism refraction colors ═══ */
  --prism-blue: #3c78ff;
  --prism-indigo: #6366f1;
  --prism-violet: #8b5cf6;
  --prism-cyan: #22d3ee;
  --prism-white: #f0f6ff;

  /* ═══ Glows & Shadows ═══ */
  --glow-blue: 0 0 12px rgba(60, 120, 255, 0.4), 0 0 24px rgba(60, 120, 255, 0.2);
  --glow-blue-strong: 0 0 20px rgba(60, 120, 255, 0.6), 0 0 40px rgba(60, 120, 255, 0.3);
  --glow-prism: 0 0 12px rgba(99, 102, 241, 0.4), 0 0 24px rgba(60, 120, 255, 0.2);
  --glow-prism-strong: 0 0 20px rgba(99, 102, 241, 0.6), 0 0 40px rgba(60, 120, 255, 0.3), 0 0 60px rgba(139, 92, 246, 0.15);
  --shadow-deep: 0 8px 32px rgba(0, 0, 0, 0.6), 0 2px 8px rgba(0, 0, 0, 0.4);
  
  /* ═══ Semantic colors ═══ */
  --success: #10b981;
  --success-glow: 0 0 10px rgba(16, 185, 129, 0.4);
  --warning: #f59e0b;
  --warning-glow: 0 0 10px rgba(245, 158, 11, 0.4);
  --error: #ef4444;
  --error-glow: 0 0 10px rgba(239, 68, 68, 0.4);
  
  /* ═══ Legacy compatibility aliases ═══ */
  --cyan-primary: var(--prism-blue);
  --cyan-glow: var(--glow-blue);
  --cyan-glow-strong: var(--glow-blue-strong);
  --accent-blue: var(--blue-700);
  --accent-blue-glow: var(--glow-blue);
  --alert-red: var(--error);
  --alert-red-glow: var(--error-glow);
  --success-green: var(--success);
  
  /* ═══ Typography ═══ */
  --font-display: 'Exo 2', 'Rajdhani', sans-serif;
  --font-cyber: 'Exo 2', 'Orbitron', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --font-main: 'Inter', 'Noto Sans KR', sans-serif;
  
  /* ═══ Spacing & Radius ═══ */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;
}

/* Global Style Reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: var(--bg-deep);
  color: var(--text-main);
  font-family: var(--font-main);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
  
  /* Deep space mesh gradient */
  background-image: 
    radial-gradient(ellipse at 20% 0%, rgba(60, 120, 255, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 10%, rgba(99, 102, 241, 0.06) 0%, transparent 40%),
    radial-gradient(ellipse at 50% 100%, rgba(139, 92, 246, 0.04) 0%, transparent 50%),
    linear-gradient(180deg, var(--bg-deep) 0%, #04001a 100%);
  background-attachment: fixed;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Cyborg Scrollbar */
::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(60, 120, 255, 0.25);
  border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--prism-blue);
  box-shadow: var(--glow-blue);
}

/* Base button reset */
button {
  font-family: inherit;
  outline: none;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Glass Panel (Reusable) */
.glass-panel {
  background: var(--bg-panel);
  border: 1px solid var(--bg-panel-border);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-deep);
}

.glass-panel:hover {
  border-color: var(--bg-panel-border-hover);
}

/* Global Animations */
@keyframes prism-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes prism-glow {
  0%, 100% { box-shadow: var(--glow-blue); }
  50% { box-shadow: var(--glow-blue-strong); }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* Selection styling */
::selection {
  background: rgba(60, 120, 255, 0.3);
  color: var(--prism-white);
}
</style>
