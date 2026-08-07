<template>
  <div class="result-page">
    <div class="top-bar">
      <router-link to="/" class="back-link">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 12h-15m0 0l6.75 6.75M4.5 12l6.75-6.75"/>
        </svg>
        返回上传页
      </router-link>
      <span class="file-name">{{ result?.filename || '视频分析结果' }}</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-box">
      <div class="spinner"></div>
      <p>加载分析结果中...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-box">{{ error }}</div>

    <!-- Main content -->
    <div v-else-if="result" class="result-layout">
      <!-- 视频播放器 -->
      <VideoPlayer
        ref="videoRef"
        :src="videoSrc"
        :seekTime="seekTime"
        @timeUpdate="onTimeUpdate"
      />

      <!-- 分段时间轴 -->
      <div v-if="result.segments?.length" class="segment-timeline">
        <div
          v-for="(seg, i) in result.segments"
          :key="i"
          :class="['timeline-seg', { active: activeSegIdx === i }]"
          :style="{ width: segWidth(seg) + '%' }"
          @click="seekTo(seg.start)"
          :title="`${fmtTs(seg.start)} ${(seg.text||'').substring(0, 30)}...`"
        >
          <div class="seg-bar"></div>
        </div>
      </div>
      <div v-if="result.segments?.length" class="timeline-ticks">
        <span>00:00</span>
        <span v-if="totalDuration > 0">{{ fmtTs(totalDuration) }}</span>
      </div>

      <!-- Meta -->
      <div class="panel">
        <div class="panel-header">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"/>
          </svg>
          分析概览
        </div>
        <div class="panel-body compact">
          <div class="meta-grid">
            <div class="meta-item">
              <span class="meta-label">文件名</span>
              <span class="meta-value">{{ result.filename }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">语言</span>
              <span class="meta-value">{{ langLabel(result.language) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">时长</span>
              <span class="meta-value">{{ fmtDuration(result.duration) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">片段数</span>
              <span class="meta-value">{{ result.segments?.length || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="panel">
        <div class="tabs">
          <button :class="['tab-btn', { active: activeTab === 'summary' }]" @click="activeTab = 'summary'">视频总结</button>
          <button :class="['tab-btn', { active: activeTab === 'highlights' }]" @click="activeTab = 'highlights'">视频要点</button>
          <button :class="['tab-btn', { active: activeTab === 'transcript' }]" @click="activeTab = 'transcript'">转录文本</button>
          <button v-if="result.translation" :class="['tab-btn', { active: activeTab === 'translation' }]" @click="activeTab = 'translation'">翻译</button>
        </div>

        <div class="content-area" @click="onTimestampClick">
          <!-- Summary -->
          <div v-if="activeTab === 'summary'" v-html="renderMarkdown(result.summary)"></div>

          <!-- Highlights -->
          <div v-else-if="activeTab === 'highlights'">
            <div v-if="highlightItems.length" class="highlight-list">
              <div v-for="(item, i) in highlightItems" :key="i" class="highlight-row">
                <button class="hl-time" @click="seekTo(item.seconds)">🎬 {{ item.ts }}</button>
                <span class="hl-text">{{ item.text }}</span>
              </div>
            </div>
            <div v-else v-html="renderMarkdown(result.highlights || '暂无要点数据')"></div>
          </div>

          <!-- Translation -->
          <div v-else-if="activeTab === 'translation'" v-html="renderMarkdown(result.translation)"></div>

          <!-- Transcript (段落 + 全部字幕) -->
          <div v-else-if="activeTab === 'transcript'">
            <div v-if="result.paragraphs" class="paragraph-view" v-html="renderMarkdown(result.paragraphs)"></div>
            <h3 v-if="result.paragraphs && result.segments?.length" style="font-size:.88rem;color:var(--text2);margin:20px 0 10px;">全部字幕</h3>
            <div v-if="result.segments?.length" class="transcript-lines">
              <div
                v-for="(seg, i) in result.segments"
                :key="i"
                :class="['transcript-line', { active: activeSegIdx === i }]"
                @click="seekTo(seg.start)"
              >
                <span class="ts-label">{{ fmtTs(seg.start) }}</span>
                <span class="ts-text">{{ seg.text }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import VideoPlayer from '../components/VideoPlayer.vue'
import * as api from '../api/index.js'

const route = useRoute()
const props = defineProps({ taskId: String })

const result = ref(null)
const loading = ref(true)
const error = ref('')
const activeTab = ref('summary')
const seekTime = ref(-1)
const activeSegIdx = ref(-1)
const videoRef = ref(null)

const videoSrc = computed(() => api.getVideoUrl(props.taskId))
const totalDuration = computed(() => {
  const segs = result.value?.segments
  return segs?.length ? segs[segs.length - 1].end : 0
})

const langMap = { zh:'中文',en:'English',ja:'日本語',ko:'한국어',fr:'Français',de:'Deutsch',es:'Español',ru:'Русский',ar:'العربية',pt:'Português',it:'Italiano' }
function langLabel(c) { return langMap[c] || c || '--' }

// Parse highlights table
const highlightItems = computed(() => {
  const raw = result.value?.highlights || ''
  if (!raw) return []
  const items = []
  const rowRe = /\|\s*(?:\*{0,2})?\[?(\d{1,2}):(\d{2})(?::(\d{2}))?\]?(?:\*{0,2})?\s*\|\s*(.+?)\s*\|/g
  let m
  while ((m = rowRe.exec(raw)) !== null) {
    let secs = parseInt(m[1]) * 60 + parseInt(m[2])
    if (m[3]) secs = parseInt(m[1]) * 3600 + parseInt(m[2]) * 60 + parseInt(m[3])
    const text = m[4].replace(/\*{1,2}/g, '').trim()
    if (text && text !== '关键信息' && text !== '时间' && text !== '---') {
      items.push({ ts: fmtTs(secs), seconds: secs, text })
    }
  }
  return items
})

function fmtDuration(s) {
  if (!s && s !== 0) return '--'
  const m = Math.floor(s/60), sec = Math.floor(s%60)
  return m>0 ? `${m}分${sec}秒` : `${sec}秒`
}
function fmtTs(s) {
  if (s == null) return '--:--'
  const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = Math.floor(s%60)
  if (h>0) return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
  return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
}
function segWidth(seg) {
  if (!totalDuration.value) return 0
  return ((seg.end - seg.start) / totalDuration.value) * 100
}

function seekTo(seconds) {
  seekTime.value = seconds
  if (videoRef.value) videoRef.value.seekTo(seconds)
}
function onTimeUpdate(time) {
  const segs = result.value?.segments || []
  const idx = segs.findIndex(s => time >= s.start && time <= s.end)
  activeSegIdx.value = idx
}
function onTimestampClick(e) {
  const link = e.target.closest('.ts-link')
  if (link) {
    const secs = parseFloat(link.dataset.start)
    if (!isNaN(secs)) seekTo(secs)
  }
}

// Markdown
function esc(t) { return t ? String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') : '' }
function renderMarkdown(md) {
  if (!md) return '<p class="st-empty">暂无内容</p>'
  let h = esc(md)
  h = h.replace(/\[(\d{1,2}):(\d{2})(?::(\d{2}))?(?:-(\d{1,2}):(\d{2})(?::(\d{2}))?)?\]/g, (match, h1, m1, s1, h2, m2, s2) => {
    let start = s1 ? parseInt(h1)*3600+parseInt(m1)*60+parseInt(s1) : parseInt(h1)*60+parseInt(m1)
    let end = null
    if (h2 !== undefined) end = s2 ? parseInt(h2)*3600+parseInt(m2)*60+parseInt(s2) : parseInt(h2)*60+parseInt(m2)
    const title = end ? `${fmtTs(start)}-${fmtTs(end)}` : fmtTs(start)
    return `<span class="ts-link" data-start="${start}" data-end="${end||start}" title="${title}">🎬 ${match}</span>`
  })
  h = h.replace(/^### (.+)$/gm,'<h3>$1</h3>')
  h = h.replace(/^## (.+)$/gm,'<h2>$1</h2>')
  h = h.replace(/^# (.+)$/gm,'<h1>$1</h1>')
  h = h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
  h = h.replace(/\*(.+?)\*/g,'<em>$1</em>')
  h = h.replace(/^- (.+)$/gm,'<li>$1</li>')
  h = h.replace(/^---$/gm,'<hr>')
  h = h.replace(/^\|(.+)\|$/gm, line => {
    const cells = line.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('')
    return cells ? `<tr>${cells}</tr>` : ''
  })
  h = h.replace(/((?:<tr>.*?<\/tr>\s*)+)/g,'<table>$1</table>')
  h = h.replace(/((?:<li>.*?<\/li>\s*)+)/g,'<ul>$1</ul>')
  h = h.replace(/\n\n/g,'</p><p>')
  h = h.replace(/\n/g,'<br>')
  h = '<p>'+h+'</p>'
  h = h.replace(/<p>\s*<\/p>/g,'')
  h = h.replace(/<p><(h[123]|ul|table|hr)/g,'<$1')
  h = h.replace(/<\/(h[123]|ul|table)><\/p>/g,'</$1>')
  return h
}

onMounted(async () => {
  try {
    const data = await api.getFullResult(props.taskId)
    if (!data || !data.task_id) throw new Error('结果不存在')
    result.value = data
  } catch (err) {
    error.value = '加载失败: ' + err.message
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.result-page { margin-top: 8px; }
.top-bar { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.back-link { display: inline-flex; align-items: center; gap: 6px; color: var(--primary); text-decoration: none; font-size: .9rem; font-weight: 600; }
.back-link:hover { color: var(--primary-hover); }
.file-name { font-size: .88rem; color: var(--text2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.loading-box { text-align: center; padding: 60px 20px; color: var(--text2); }
.spinner { width: 36px; height: 36px; border: 3px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin .8s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

.result-layout { display: flex; flex-direction: column; gap: 16px; }

/* Timeline */
.segment-timeline { display: flex; gap: 2px; height: 16px; background: var(--surface2); border-radius: 3px; overflow: hidden; cursor: pointer; }
.timeline-seg { height: 100%; position: relative; }
.timeline-seg .seg-bar { height: 100%; width: 100%; background: var(--border); border-radius: 1px; transition: background var(--transition); }
.timeline-seg:hover .seg-bar { background: var(--primary); }
.timeline-seg.active .seg-bar { background: var(--primary); }
.timeline-ticks { display: flex; justify-content: space-between; font-size: .7rem; color: var(--text2); margin-top: 2px; }

.meta-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }
.meta-item { display: flex; flex-direction: column; gap: 2px; }
.meta-label { font-size: .72rem; color: var(--text2); font-weight: 500; text-transform: uppercase; letter-spacing: .05em; }
.meta-value { font-size: .9rem; font-weight: 600; }

.tabs { display: flex; border-bottom: 2px solid var(--border); padding: 0 20px; }
.tab-btn { background: none; border: none; padding: 12px 20px; font-family: var(--font); font-size: .88rem; font-weight: 600; color: var(--text2); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all var(--transition); }
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--primary); border-bottom-color: var(--primary); }

.content-area { padding: 24px; font-size: .92rem; line-height: 1.75; max-height: 60vh; overflow-y: auto; }

.content-area :deep(h1) { font-size: 1.3rem; margin: 20px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
.content-area :deep(h2) { font-size: 1.1rem; margin: 18px 0 8px; color: var(--primary); }
.content-area :deep(h3) { font-size: 1rem; margin: 14px 0 6px; }
.content-area :deep(ul) { padding-left: 20px; margin: 6px 0 12px; }
.content-area :deep(li) { margin: 4px 0; }
.content-area :deep(strong) { color: var(--primary); font-weight: 600; }
.content-area :deep(p) { margin: 10px 0; }
.content-area :deep(hr) { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.content-area :deep(table) { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: .85rem; }
.content-area :deep(th) { text-align: left; padding: 8px 12px; background: var(--surface2); border-bottom: 2px solid var(--border); color: var(--text2); font-weight: 600; font-size: .78rem; }
.content-area :deep(td) { padding: 8px 12px; border-bottom: 1px solid var(--border); }
.content-area :deep(tr:hover td) { background: var(--primary-bg); }
.content-area :deep(.ts-link) { color: var(--primary); font-weight: 600; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; transition: all var(--transition); }
.content-area :deep(.ts-link):hover { background: var(--primary-bg); border-radius: 3px; }

/* Highlights */
.highlight-list { display: flex; flex-direction: column; gap: 4px; }
.highlight-row { display: flex; align-items: flex-start; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.highlight-row:last-child { border-bottom: none; }
.hl-time { font-family: var(--mono); font-size: .8rem; font-weight: 700; color: var(--primary); background: var(--primary-bg); border: none; padding: 2px 10px; border-radius: var(--radius-sm); cursor: pointer; white-space: nowrap; transition: all var(--transition); flex-shrink: 0; }
.hl-time:hover { background: var(--primary); color: #fff; }
.hl-text { font-size: .88rem; line-height: 1.6; padding-top: 2px; }

/* Transcript */
.transcript-lines { font-size: .85rem; line-height: 1.9; }
.transcript-line { display: flex; gap: 10px; padding: 6px 8px; border-radius: 4px; cursor: pointer; transition: background var(--transition); }
.transcript-line:hover { background: #e8eaf0; }
.transcript-line.active { background: var(--primary-bg); }
.ts-label { font-family: var(--mono); font-size: .78rem; color: var(--primary); font-weight: 700; white-space: nowrap; min-width: 50px; padding-top: 1px; }
.ts-text { flex: 1; }

.st-empty { text-align: center; color: var(--text2); padding: 40px 0; font-size: .9rem; }
.paragraph-view { border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 8px; }

@media (max-width: 640px) {
  .tabs { padding: 0 12px; }
  .tab-btn { padding: 10px 14px; font-size: .82rem; }
  .content-area { padding: 16px; }
}
</style>
