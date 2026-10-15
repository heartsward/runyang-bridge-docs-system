<template>
  <div class="welcome-view">
    <!-- 顶部导航条 -->
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <n-icon :component="LayersOutline" size="26" color="#38bdf8" />
          <span class="brand-name">润扬大桥运维知识库</span>
        </div>
        <div class="topbar-actions">
          <n-button quaternary class="nav-btn" @click="handleStartUse">
            {{ authService.isAuthenticated() ? '进入系统' : '登录' }}
          </n-button>
          <n-button type="primary" class="cta-btn-small" @click="handleStartUse">
            开始使用
          </n-button>
        </div>
      </div>
    </header>

    <!-- Hero 主视觉 -->
    <section class="hero">
      <div class="hero-bg" aria-hidden="true"></div>
      <div class="hero-content">
        <div class="hero-badge">AI Wiki · 运维知识底座</div>
        <h1 class="hero-title">
          文档、设备、知识<br />
          <span class="hero-title-accent">一处管理，处处可查</span>
        </h1>
        <p class="hero-subtitle">
          面向高速公路机电与信息化运维的一体化平台——文档在线预览、设备资产台账、
          全文智能搜索，并以 AI Wiki 理念将知识沉淀为 Markdown，无缝接入智能体。
        </p>
        <div class="hero-actions">
          <n-button type="primary" size="large" class="cta-btn" @click="handleStartUse">
            {{ authService.isAuthenticated() ? '进入系统' : '登录并开始使用' }}
          </n-button>
          <n-button size="large" class="cta-btn-ghost" @click="handleSearch">
            <template #icon>
              <n-icon :component="SearchOutline" />
            </template>
            智能搜索
          </n-button>
        </div>
        <div class="hero-stats">
          <div class="stat">
            <div class="stat-num">多格式</div>
            <div class="stat-label">文档在线预览</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat">
            <div class="stat-num">全文索引</div>
            <div class="stat-label">秒级内容检索</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat">
            <div class="stat-num">MCP 接口</div>
            <div class="stat-label">智能体直接读写</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 核心功能 -->
    <section class="features">
      <div class="section-inner">
        <h2 class="section-title">核心功能</h2>
        <p class="section-desc">从资料归档到现场运维，覆盖日常工作的完整闭环</p>
        <div class="feature-grid">
          <div class="feature-card" v-for="f in features" :key="f.title">
            <div class="feature-icon" :style="{ background: f.bg, color: f.color }">
              <n-icon :component="f.icon" size="28" />
            </div>
            <h3 class="feature-title">{{ f.title }}</h3>
            <p class="feature-desc">{{ f.desc }}</p>
            <ul class="feature-points">
              <li v-for="p in f.points" :key="p">{{ p }}</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- AI Wiki 理念 -->
    <section class="aiwiki">
      <div class="section-inner aiwiki-inner">
        <div class="aiwiki-text">
          <h2 class="section-title left">AI Wiki 理念</h2>
          <p class="aiwiki-lead">
            每一份上传的文档都会被自动提取为结构化 Markdown——标题、表格、图片全部保留，
            知识不再是躺在网盘里的二进制文件，而是人和机器都能直接阅读、检索、引用的活文档。
          </p>
          <ul class="aiwiki-list">
            <li>
              <n-icon :component="SparklesOutline" size="18" color="#0e7490" />
              <span><b>知识 Markdown 化</b>——原文与提取内容双轨存储，预览、搜索、引用同一来源</span>
            </li>
            <li>
              <n-icon :component="TerminalOutline" size="18" color="#0e7490" />
              <span><b>智能体无缝接入</b>——MCP 工具接口 + 固定 API 令牌，AI 助手可直接查台账、读文档、写回结果</span>
            </li>
            <li>
              <n-icon :component="ShieldCheckmarkOutline" size="18" color="#0e7490" />
              <span><b>人机审计分离</b>——脚本走专用服务账号，人工走账号登录，每一次改动都可追溯</span>
            </li>
          </ul>
        </div>
        <div class="aiwiki-visual" aria-hidden="true">
          <div class="mock-window">
            <div class="mock-titlebar">
              <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
              <span class="mock-name">wiki/asset_report.md</span>
            </div>
            <div class="mock-body">
              <div class="mock-line h"># 资产排查情况统计表</div>
              <div class="mock-line">| 设备 | 网络 | 状态 |</div>
              <div class="mock-line dim">| 核心交换机 | 收费网 | 在用 |</div>
              <div class="mock-line dim">| 防火墙 | 办公网 | 维保到期 ⚠ |</div>
              <div class="mock-line accent">→ 智能体：已按分组筛选并回填维保日期</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="section-inner footer-inner">
        <span>润扬大桥运维资产管理系统</span>
        <span class="footer-dim">文档管理 · 资产管理 · 智能搜索 · AI Wiki</span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { NButton, NIcon } from 'naive-ui'
import {
  LayersOutline,
  SearchOutline,
  DocumentTextOutline,
  HardwareChipOutline,
  SparklesOutline,
  TerminalOutline,
  ShieldCheckmarkOutline
} from '@vicons/ionicons5'
import { authService } from '@/services'

const router = useRouter()

const features = [
  {
    title: '文档管理',
    icon: DocumentTextOutline,
    color: '#1d4ed8',
    bg: 'rgba(29, 78, 216, 0.08)',
    desc: '运维资料统一归档，上传即可在线预览，自动提取正文与图片。',
    points: ['多格式在线预览（OnlyOffice）', '自动 Markdown 提取', '分类 / 标签 / 版本管理']
  },
  {
    title: '资产管理',
    icon: HardwareChipOutline,
    color: '#0e7490',
    bg: 'rgba(14, 116, 144, 0.08)',
    desc: '设备台账结构化维护，维保到期一目了然，支持多网段与自定义分组。',
    points: ['维保到期 / 启用日期跟踪', '办公网 / 收费网 / 监控网筛选', '自定义分组 · Excel 一键导出']
  },
  {
    title: '智能搜索',
    icon: SearchOutline,
    color: '#b45309',
    bg: 'rgba(180, 83, 9, 0.08)',
    desc: '基于全文索引的内容级检索，命中片段高亮定位，预览直达原文。',
    points: ['全文索引秒级响应', '关键词高亮与上下文定位', '搜索结果内直接预览']
  },
  {
    title: 'AI Wiki · 智能体',
    icon: SparklesOutline,
    color: '#7c3aed',
    bg: 'rgba(124, 58, 237, 0.08)',
    desc: '知识库即接口。AI 助手通过 MCP 与固定令牌直接读写系统，成为你的运维搭子。',
    points: ['MCP 工具接口开箱即用', '固定 API 令牌免登录操作', '台账查询 / 文档问答 / 自动回填']
  }
]

const handleStartUse = () => {
  if (authService.isAuthenticated()) {
    router.push('/documents')
  } else {
    router.push('/login')
  }
}

const handleSearch = () => {
  if (authService.isAuthenticated()) {
    router.push('/search')
  } else {
    router.push('/login')
  }
}
</script>

<style scoped>
.welcome-view {
  min-height: 100vh;
  background: #f8fafc;
  color: #1e293b;
  font-family: system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
}

/* ===== 顶部导航 ===== */
.topbar {
  position: absolute;
  top: 0; left: 0; right: 0;
  z-index: 10;
}
.topbar-inner {
  max-width: 1120px;
  margin: 0 auto;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-name {
  font-size: 17px;
  font-weight: 600;
  color: #f1f5f9;
  letter-spacing: 0.5px;
}
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.nav-btn { color: #cbd5e1 !important; }
.cta-btn-small { border-radius: 8px; }

/* ===== Hero ===== */
.hero {
  position: relative;
  padding: 140px 24px 90px;
  overflow: hidden;
  background: linear-gradient(160deg, #0b1f3a 0%, #123356 55%, #0e4a5c 100%);
}
.hero-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 45% at 75% 20%, rgba(56, 189, 248, 0.14), transparent 60%),
    radial-gradient(ellipse 50% 40% at 15% 85%, rgba(14, 116, 144, 0.22), transparent 60%),
    repeating-linear-gradient(90deg, rgba(148, 163, 184, 0.05) 0 1px, transparent 1px 72px),
    repeating-linear-gradient(0deg, rgba(148, 163, 184, 0.05) 0 1px, transparent 1px 72px);
}
.hero-content {
  position: relative;
  max-width: 860px;
  margin: 0 auto;
  text-align: center;
}
.hero-badge {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 999px;
  border: 1px solid rgba(56, 189, 248, 0.35);
  background: rgba(56, 189, 248, 0.1);
  color: #7dd3fc;
  font-size: 13px;
  letter-spacing: 1px;
  margin-bottom: 28px;
}
.hero-title {
  margin: 0 0 24px;
  font-size: 46px;
  line-height: 1.28;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: 1px;
}
.hero-title-accent {
  background: linear-gradient(90deg, #38bdf8, #34d399);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.hero-subtitle {
  margin: 0 auto 40px;
  max-width: 640px;
  font-size: 16.5px;
  line-height: 1.9;
  color: #b6c5d8;
}
.hero-actions {
  display: flex;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
}
.cta-btn {
  border-radius: 10px;
  padding: 0 28px;
  height: 46px;
  font-size: 16px;
  background: linear-gradient(90deg, #2563eb, #0e7490);
  border: none;
}
.cta-btn-ghost {
  border-radius: 10px;
  padding: 0 24px;
  height: 46px;
  font-size: 16px;
  color: #e2e8f0 !important;
  border: 1px solid rgba(148, 163, 184, 0.4) !important;
  background: rgba(148, 163, 184, 0.08) !important;
}
.hero-stats {
  margin-top: 56px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 36px;
  flex-wrap: wrap;
}
.stat-num {
  font-size: 19px;
  font-weight: 700;
  color: #e2e8f0;
}
.stat-label {
  margin-top: 4px;
  font-size: 13px;
  color: #8fa3bc;
}
.stat-divider {
  width: 1px;
  height: 34px;
  background: rgba(148, 163, 184, 0.25);
}

/* ===== 通用 section ===== */
.section-inner {
  max-width: 1120px;
  margin: 0 auto;
  padding: 0 24px;
}
.section-title {
  margin: 0 0 10px;
  font-size: 30px;
  font-weight: 700;
  color: #0f172a;
  text-align: center;
}
.section-title.left { text-align: left; }
.section-desc {
  margin: 0 0 44px;
  text-align: center;
  font-size: 15px;
  color: #64748b;
}

/* ===== 功能卡片 ===== */
.features { padding: 76px 0 60px; }
.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 22px;
}
@media (max-width: 1024px) { .feature-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 620px)  { .feature-grid { grid-template-columns: 1fr; } }
.feature-card {
  background: #ffffff;
  border: 1px solid #e8edf3;
  border-radius: 16px;
  padding: 28px 24px;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
}
.feature-icon {
  width: 52px;
  height: 52px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
}
.feature-title {
  margin: 0 0 10px;
  font-size: 18px;
  font-weight: 650;
  color: #0f172a;
}
.feature-desc {
  margin: 0 0 16px;
  font-size: 14px;
  line-height: 1.75;
  color: #475569;
}
.feature-points {
  margin: 0;
  padding: 0;
  list-style: none;
}
.feature-points li {
  position: relative;
  padding: 4px 0 4px 16px;
  font-size: 13px;
  color: #64748b;
}
.feature-points li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 11px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
}

/* ===== AI Wiki ===== */
.aiwiki {
  background: linear-gradient(180deg, #eef4fa 0%, #f8fafc 100%);
  padding: 76px 0;
}
.aiwiki-inner {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 56px;
  align-items: center;
}
@media (max-width: 900px) { .aiwiki-inner { grid-template-columns: 1fr; } }
.aiwiki-lead {
  margin: 18px 0 26px;
  font-size: 16px;
  line-height: 2;
  color: #334155;
}
.aiwiki-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.aiwiki-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14.5px;
  line-height: 1.8;
  color: #475569;
}
.aiwiki-list li b { color: #0f172a; }
.aiwiki-list li .n-icon { margin-top: 5px; flex-shrink: 0; }

.aiwiki-visual { display: flex; justify-content: center; }
.mock-window {
  width: 100%;
  max-width: 420px;
  background: #0f172a;
  border-radius: 14px;
  box-shadow: 0 20px 44px rgba(15, 23, 42, 0.25);
  overflow: hidden;
}
.mock-titlebar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  background: rgba(148, 163, 184, 0.08);
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.red { background: #f87171; }
.dot.yellow { background: #fbbf24; }
.dot.green { background: #34d399; }
.mock-name {
  margin-left: 8px;
  font-size: 12px;
  color: #94a3b8;
  font-family: Consolas, Menlo, monospace;
}
.mock-body { padding: 20px 18px; }
.mock-line {
  font-family: Consolas, Menlo, monospace;
  font-size: 13px;
  line-height: 2.1;
  color: #cbd5e1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.mock-line.h { color: #7dd3fc; font-weight: 700; }
.mock-line.dim { color: #7c8ba1; }
.mock-line.accent { color: #34d399; margin-top: 8px; }

/* ===== 页脚 ===== */
.footer {
  border-top: 1px solid #e8edf3;
  padding: 26px 0;
}
.footer-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 13px;
  color: #64748b;
}
.footer-dim { color: #94a3b8; }
</style>
