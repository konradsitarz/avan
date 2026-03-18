<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">N</div>
        <div class="brand-text">
          <span class="brand-name">Nava</span>
          <span class="brand-sub">Panel zarządzania</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/briefing" class="nav-item" active-class="active">
          <span class="nav-icon">&#128203;</span>
          <span>Briefing</span>
        </router-link>
        <router-link to="/feed" class="nav-item" active-class="active">
          <span class="nav-icon">&#9888;</span>
          <span>Zgłoszenia</span>
        </router-link>
        <router-link to="/timeline" class="nav-item" active-class="active">
          <span class="nav-icon">&#128339;</span>
          <span>Oś czasu</span>
        </router-link>
        <router-link to="/respond" class="nav-item" active-class="active">
          <span class="nav-icon">&#9993;</span>
          <span>Odpowiedzi</span>
        </router-link>
        <router-link to="/rules" class="nav-item" active-class="active">
          <span class="nav-icon">&#9881;</span>
          <span>Reguły</span>
        </router-link>
      </nav>

    </aside>

    <main class="main-content">
      <router-view />
    </main>

    <FireBar />
  </div>
</template>

<script setup>
import FireBar from './components/FireBar.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: #0f1117;
  color: #e1e4e8;
}

:root {
  --bg-primary: #0f1117;
  --bg-secondary: #161b22;
  --bg-card: #1c2129;
  --bg-hover: #242a33;
  --border: #2d333b;
  --text-primary: #e1e4e8;
  --text-secondary: #8b949e;
  --text-muted: #6e7681;
  --accent: #58a6ff;
  --accent-hover: #79b8ff;
  --urgent: #f85149;
  --high: #d29922;
  --medium: #58a6ff;
  --low: #8b949e;
  --success: #3fb950;
  --sidebar-width: 240px;
}

.admin-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
  border-bottom: 1px solid var(--border);
}

.brand-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #58a6ff, #3b82f6);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  color: white;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-weight: 700;
  font-size: 16px;
  color: var(--text-primary);
}

.brand-sub {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-nav {
  padding: 12px 8px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s;
  margin-bottom: 2px;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(88, 166, 255, 0.12);
  color: var(--accent);
}

.nav-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  padding: 24px;
  padding-bottom: 80px;
  min-height: 100vh;
}

/* Shared utility classes */
.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.btn {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  background: var(--bg-card);
  color: var(--text-primary);
}

.btn:hover {
  background: var(--bg-hover);
  border-color: var(--text-muted);
}

.btn-primary {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.btn-primary:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
}

.btn-danger {
  background: transparent;
  border-color: var(--urgent);
  color: var(--urgent);
}

.btn-danger:hover {
  background: rgba(248, 81, 73, 0.15);
}

.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.badge-urgent { background: rgba(248,81,73,0.15); color: var(--urgent); }
.badge-high { background: rgba(210,153,34,0.15); color: var(--high); }
.badge-medium { background: rgba(88,166,255,0.15); color: var(--medium); }
.badge-low { background: rgba(139,148,158,0.15); color: var(--low); }

.badge-email { background: rgba(88,166,255,0.1); color: var(--accent); }
.badge-sms { background: rgba(63,185,80,0.1); color: var(--success); }
.badge-voice { background: rgba(210,153,34,0.1); color: var(--high); }

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--text-muted);
}

.empty-state p {
  margin-top: 8px;
  font-size: 14px;
}

input, select, textarea {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--text-primary);
  font-size: 13px;
  font-family: inherit;
  width: 100%;
}

input:focus, select:focus, textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.15);
}

label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
</style>
