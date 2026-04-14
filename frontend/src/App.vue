<template>
  <router-view />
</template>

<script setup>
// 使用 Vue Router 来管理页面
</script>

<style>
/* 🌐 GLOBAL CSS VARIABLES - JARVIS CYBERPUNK THEME */
:root {
  --bg-deep: #050814;
  --bg-panel: rgba(13, 17, 33, 0.7);
  --bg-panel-border: rgba(0, 242, 254, 0.15);
  
  --text-main: #e2e8f0;
  --text-muted: #94a3b8;
  
  --cyan-primary: #00f2fe;
  --cyan-glow: 0 0 10px rgba(0, 242, 254, 0.4), 0 0 20px rgba(0, 242, 254, 0.2);
  --cyan-glow-strong: 0 0 15px rgba(0, 242, 254, 0.6), 0 0 30px rgba(0, 242, 254, 0.4);
  
  --accent-blue: #1e3a8a;
  --accent-blue-glow: 0 0 10px rgba(30, 58, 138, 0.6);
  
  --alert-red: #ff2a55;
  --alert-red-glow: 0 0 10px rgba(255, 42, 85, 0.4);
  
  --success-green: #00ff9d;
  
  --font-cyber: 'Orbitron', 'Space Grotesk', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --font-main: 'Inter', 'Noto Sans KR', sans-serif;
}

/* 全局样式重置 - Global Style Reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: var(--bg-deep);
  color: var(--text-main);
  background-image: 
    radial-gradient(circle at 50% 0%, rgba(0, 242, 254, 0.05) 0%, transparent 50%),
    linear-gradient(to bottom, rgba(5, 8, 20, 0.9) 0%, var(--bg-deep) 100%);
  background-attachment: fixed;
  font-family: var(--font-main);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 滚动条样式 - Cyborg Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--bg-deep);
  border-left: 1px solid rgba(255,255,255,0.05);
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 242, 254, 0.3);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--cyan-primary);
  box-shadow: var(--cyan-glow);
}

/* Base button resets */
button {
  font-family: inherit;
  outline: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

/* Global Glass View Transition Class (Reusable) */
.glass-panel {
  background: var(--bg-panel);
  border: 1px solid var(--bg-panel-border);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 8px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
}
</style>
