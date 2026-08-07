<template>
  <div class="app">
    <header class="header">
      <router-link to="/" class="brand-link">
        <div class="icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z"/>
          </svg>
        </div>
        <h1>智能视频助手</h1>
      </router-link>
      <p>上传视频 → AI 自动转写、总结、要点、字幕转写</p>
      <p>若您上传多个视频，视频跳转返回上传界面后，请不要关闭，长视频后台处理中，等待处理完成后自动跳转</p>
      <p>历史记录可从下方历史记录查询</p>
    </header>
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
:root {
  color-scheme: light;
  --bg: #f8f9fb;
  --surface: #ffffff;
  --surface2: #f3f4f6;
  --text: #1f2937;
  --text2: #6b7280;
  --primary: #6366f1;
  --primary-bg: #eef2ff;
  --primary-hover: #4f46e5;
  --border: #e5e7eb;
  --success: #10b981;
  --success-bg: #d1fae5;
  --warn: #f59e0b;
  --warn-bg: #fef3c7;
  --danger: #ef4444;
  --danger-bg: #fee2e2;
  --radius: 10px;
  --radius-sm: 6px;
  --shadow: 0 1px 2px rgba(0,0,0,.06), 0 1px 3px rgba(0,0,0,.04);
  --shadow-lg: 0 4px 12px rgba(0,0,0,.08), 0 1px 4px rgba(0,0,0,.04);
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
  --mono: "SF Mono", "JetBrains Mono", "Fira Code", monospace;
  --transition: 150ms ease;
}

*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }

body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
}

.app { max-width: 1024px; margin: 0 auto; padding: 32px 20px 48px; }

.header { text-align: center; margin-bottom: 36px; }
.header .icon {
  width: 56px; height: 56px; border-radius: 16px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: inline-flex; align-items: center; justify-content: center;
  margin-bottom: 12px;
}
.header .icon svg { width: 28px; height: 28px; color: #fff; }
.header h1 { font-size: 1.75rem; font-weight: 700; letter-spacing: -.02em; }
.header p { color: var(--text2); margin-top: 4px; font-size: .95rem; }
.brand-link { text-decoration: none; color: inherit; }

/* Shared primitives */
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  margin-bottom: 20px;
  overflow: hidden;
}
.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 10px;
  font-weight: 600; font-size: .95rem;
}
.panel-header .count { margin-left: auto; font-size: .78rem; color: var(--text2); font-weight: 400; }
.panel-body { padding: 20px; }
.panel-body.compact { padding: 14px 20px; }

.error-box {
  background: var(--danger-bg); color: var(--danger);
  padding: 14px 18px; border-radius: var(--radius-sm);
  font-size: .9rem; border: 1px solid #fecaca;
}

.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 20px; border-radius: var(--radius-sm);
  font-family: var(--font); font-size: .88rem; font-weight: 600;
  border: none; cursor: pointer; transition: all var(--transition); white-space: nowrap;
}
.btn-primary { background: var(--primary); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--primary-hover); }
.btn-primary:disabled { opacity: .45; cursor: not-allowed; }
.btn-ghost {
  background: none; border: 1px solid var(--border); color: var(--text2);
}
.btn-ghost:hover { background: var(--surface2); color: var(--text); }
.btn-danger { background: var(--danger-bg); color: var(--danger); border: 1px solid #fecaca; }
.btn-danger:hover { background: #fecaca; }

.badge-sm {
  display: inline-block; padding: 1px 7px; border-radius: 10px;
  font-size: .67rem; font-weight: 600;
}

@media (max-width: 640px) {
  .app { padding: 16px 12px 32px; }
}
</style>
