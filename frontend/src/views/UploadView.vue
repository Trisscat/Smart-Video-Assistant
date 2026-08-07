<template>
  <div>
    <!-- 上传面板 -->
    <div class="panel">
      <div class="panel-header">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
        </svg>
        视频分析
      </div>
      <div class="panel-body">
        <!-- 已选文件网格 + 处理进度覆盖 -->
        <div v-if="files.length || tasks.length" class="files-grid">
          <!-- 待上传的文件卡片 -->
          <div v-for="f in files" :key="f.id" class="file-card">
            <div class="card-thumb">
              <video v-if="isVideo(f.name)" :src="fileUrl(f)" muted preload="metadata" />
              <div v-else class="audio-placeholder">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"/>
                </svg>
              </div>
            </div>
            <div class="card-info">
              <span class="card-name" :title="f.name">{{ f.name }}</span>
              <span class="card-size">{{ formatSize(f.size) }}</span>
            </div>
            <button class="card-remove" @click="removeFile(f.id)" title="移除">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <!-- 处理中的任务卡片 — spinner 等待 -->
          <div v-for="task in tasks" :key="task.id" class="file-card">
            <div class="card-thumb task-thumb">
              <video v-if="task.videoUrl" :src="task.videoUrl" muted />
              <div v-else class="audio-placeholder">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"/>
                </svg>
              </div>
              <!-- spinner 等待覆盖层 -->
              <div class="wait-overlay">
                <div class="wait-spinner"></div>
                <p class="wait-text">{{ waitMessage(task) }}</p>
              </div>
            </div>
            <div class="card-info">
              <span class="card-name" :title="task.filename">{{ task.filename }}</span>
              <span :class="'badge-sm ' + taskBadge(task.status)">{{ statusLabel(task.status) }}</span>
            </div>
            <button
              v-if="!isTerminal(task.status)"
              class="card-remove"
              @click="cancelTaskItem(task.id)"
              title="取消"
              style="opacity:1; background: var(--danger);"
            >✕</button>
          </div>
          <!-- Add more -->
          <div class="file-card add-more" @click="fileInputRef?.click()">
            <div class="add-icon">+</div>
            <span class="add-text">继续添加</span>
          </div>
        </div>

        <!-- 空上传区 -->
        <div
          v-else
          :class="['upload-zone', { drag: isDragging }]"
          @click="fileInputRef?.click()"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
        >
          <div class="upload-icon">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z"/>
            </svg>
          </div>
          <p class="upload-title">拖拽文件到此处，或点击选择</p>
          <p class="upload-hint">支持 MP4 · AVI · MKV · MOV · WebM 等视频格式</p>
        </div>

        <input ref="fileInputRef" type="file" multiple
          accept=".mp4,.avi,.mkv,.mov,.webm,.flv,.wmv,.m4v"
          style="display:none" @change="onFileChange" />

        <!-- 控制栏 -->
        <div v-if="files.length || tasks.length" class="controls">
          <div class="file-count">
            {{ files.length ? `已选择 ${files.length} 个文件` : '' }}
            {{ files.length && tasks.length ? ' · ' : '' }}
            {{ tasks.filter(t => !isTerminal(t.status)).length ? `${tasks.filter(t => !isTerminal(t.status)).length} 个处理中` : '' }}
          </div>
          <button class="btn btn-primary" :disabled="!files.length || uploading" @click="startProcessing">
            <svg v-if="!uploading" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z"/>
            </svg>
            {{ uploading ? '上传中...' : '开始分析' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 错误 -->
    <div v-for="(err, i) in errors" :key="'err-'+i" class="panel" style="border-color:var(--danger);">
      <div class="panel-body compact"><div class="error-box">{{ err }}</div></div>
    </div>

    <!-- 历史 -->
    <div v-if="history.length" class="panel">
      <div class="panel-header">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        历史记录
        <span class="count">共 {{ historyTotal }} 条</span>
      </div>
      <div class="panel-body compact">
        <div v-for="h in history" :key="h.task_id" class="history-row">
          <div class="hist-info" @click="openHistory(h)">
            <span class="hist-name">{{ h.filename }}</span>
            <span class="hist-meta">
              <span :class="'badge-sm ' + histBadge(h.status)">{{ histLabel(h.status) }}</span>
              {{ formatDate(h.created_at) }}
            </span>
          </div>
          <button
            class="hist-delete"
            @click.stop="deleteHistoryItem(h.task_id, h.filename)"
            title="删除"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as api from '../api/index.js'

const router = useRouter()

const files = ref([])
const uploading = ref(false)
const tasks = ref([])
const errors = ref([])
const history = ref([])
const historyTotal = ref(0)
const isDragging = ref(false)
const fileInputRef = ref(null)
const pollTimers = {}
const wsSockets = {}
const urlCache = {}

const videoExts = ['.mp4','.avi','.mkv','.mov','.webm','.flv','.wmv','.m4v']
const mediaExts = '.mp4.avi.mkv.mov.webm.flv.wmv.m4v'

const isTerminal = (s) => s === 'completed' || s === 'failed' || s === 'cancelled'

const statusMap = {
  pending: '排队中', extracting: '提取音频', transcribing: '语音识别',
  analyzing: 'AI分析', completed: '完成', failed: '失败', cancelled: '已取消',
}
function statusLabel(s) { return statusMap[s] || s }
function taskBadge(s) {
  if (s === 'completed') return 'badge-ok'
  if (s === 'failed') return 'badge-fail'
  if (s === 'cancelled') return 'badge-cancel'
  return 'badge-running'
}
function histLabel(s) { return s === 'completed' ? '完成' : s === 'failed' ? '失败' : s || '--' }
function histBadge(s) {
  if (s === 'completed') return 'badge-ok'
  if (s === 'failed') return 'badge-fail'
  return 'badge-cancel'
}
function isVideo(n) { return videoExts.includes(n.substring(n.lastIndexOf('.')).toLowerCase()) }
function formatSize(b) { return b < 1048576 ? (b/1024).toFixed(0)+' KB' : (b/1048576).toFixed(1)+' MB' }
function formatDate(d) { if (!d) return ''; return new Date(d).toLocaleDateString('zh-CN') }
function waitMessage(task) {
  const dur = task.duration || 0
  if (dur > 0) {
    const mins = dur / 60
    if (mins <= 2) return '正在处理，请稍候...'
    if (mins <= 10) return '视频较长，加载可能稍久，请耐心等待'
    return '视频时长较长，解析中，可能需要 5-10 分钟，请耐心等待'
  }
  // 还没拿到时长
  if (task.status === 'extracting') return '正在提取音频，请稍候...'
  if (task.status === 'transcribing') return '正在语音识别，请稍候...'
  if (task.status === 'analyzing') return '正在 AI 分析，请耐心等待...'
  return '正在处理，请稍候...'
}
function fileUrl(f) {
  if (!urlCache[f.id]) urlCache[f.id] = URL.createObjectURL(f)
  return urlCache[f.id]
}

// ── 文件 ──
function onDrop(e) {
  isDragging.value = false
  if (e.dataTransfer.files.length) doAdd(Array.from(e.dataTransfer.files))
}
function onFileChange(e) {
  if (e.target.files.length) { doAdd(Array.from(e.target.files)); e.target.value = '' }
}
function doAdd(list) {
  const media = list.filter(f => mediaExts.includes(f.name.substring(f.name.lastIndexOf('.')).toLowerCase()))
  if (media.length) addFiles(media)
}
function addFiles(newFiles) {
  for (const f of newFiles) {
    if (!files.value.find(x => x.name === f.name && x.size === f.size))
      files.value.push(Object.assign(f, { id: Date.now() + Math.random() }))
  }
}
function removeFile(fileId) {
  const idx = files.value.findIndex(f => f.id === fileId)
  if (idx >= 0) {
    if (urlCache[files.value[idx].id]) { URL.revokeObjectURL(urlCache[files.value[idx].id]); delete urlCache[files.value[idx].id] }
    files.value.splice(idx, 1)
  }
}

// ── 上传 ──
async function startProcessing() {
  if (!files.value.length) return
  uploading.value = true
  errors.value = []
  try {
    const data = await api.uploadVideos(files.value)
    for (const t of data.tasks) {
      // 找到对应的 File 对象保留 videoUrl
      const fileObj = files.value.find(f => f.name === t.filename)
      tasks.value.push({
        id: t.task_id, filename: t.filename, status: t.status || 'pending', progress: 0,
        videoUrl: fileObj ? URL.createObjectURL(fileObj) : null,
      })
      setTimeout(() => connectOrPoll(t.task_id), 300)
    }
  } catch (err) { errors.value.push('上传失败: ' + err.message) }
  files.value.forEach(f => { if (urlCache[f.id]) { URL.revokeObjectURL(urlCache[f.id]); delete urlCache[f.id] } })
  files.value = []
  uploading.value = false
}

function connectOrPoll(taskId) {
  // 直接走轮询 — 比 WebSocket 更可靠
  startPolling(taskId)
}

function startFallbackPoll(taskId) {
  const task = tasks.value.find(t => t.id === taskId)
  if (task && !isTerminal(task.status)) startPolling(taskId)
}
function startPolling(taskId) {
  if (pollTimers[taskId]) clearInterval(pollTimers[taskId])
  pollTimers[taskId] = setInterval(() => poll(taskId), 1500)
}
async function poll(taskId) {
  const task = tasks.value.find(t => t.id === taskId)
  if (!task) { clearInterval(pollTimers[taskId]); return }
  try {
    const data = await api.getTask(taskId)
    updateTask(taskId, data)
    // 完成后自动跳转
    if (data.status === 'completed') {
      clearInterval(pollTimers[taskId])
      router.push({ name: 'Result', params: { taskId } })
    } else if (isTerminal(data.status)) {
      clearInterval(pollTimers[taskId])
    }
  } catch (err) { clearInterval(pollTimers[taskId]) }
}
function updateTask(taskId, data) {
  const task = tasks.value.find(t => t.id === taskId)
  if (!task) return
  task.status = data.status || task.status
  task.progress = data.progress || 0
  if (data.duration) task.duration = data.duration  // 拿后端返回的时长
}
async function cancelTaskItem(taskId) {
  try {
    await api.cancelTask(taskId)
    const t = tasks.value.find(x => x.id === taskId)
    if (t) t.status = 'cancelled'
    clearInterval(pollTimers[taskId])
  } catch (e) { /* */ }
}

// ── 历史 & 恢复任务 ──
async function loadHistory() {
  try {
    const data = await api.getHistory(1, 50)
    history.value = data.items || []
    historyTotal.value = data.total || 0
  } catch (e) { /* */ }
}

/* 页面加载时恢复未完成任务 — 但不自动跳转（避免阻塞返回导航） */
async function recoverTasks() {
  try {
    const data = await api.getTasks()
    const all = data.tasks || []

    for (const t of all) {
      if (t.status === 'completed' || t.status === 'failed' || t.status === 'cancelled') continue
      const existing = tasks.value.find(x => x.id === t.task_id)
      if (!existing) {
        tasks.value.push({
          id: t.task_id,
          filename: t.filename,
          status: t.status,
          progress: t.progress || 0,
          duration: t.duration || 0,
          videoUrl: null,
        })
      }
      startPolling(t.task_id)
    }
  } catch (e) { /* */ }
}
function openHistory(h) {
  if (h.status === 'completed') router.push({ name: 'Result', params: { taskId: h.task_id } })
}
async function deleteHistoryItem(taskId, filename) {
  try {
    await api.deleteHistory(taskId)
    history.value = history.value.filter(h => h.task_id !== taskId)
    historyTotal.value = Math.max(0, historyTotal.value - 1)
  } catch (e) { /* */ }
}

/* 页面加载时不主动恢复任务 — 避免从结果页返回时被强制跳转 */
onMounted(() => {
  loadHistory()
})

/* 离开页面时清除所有轮询，避免后台持续请求卡住路由 */
onUnmounted(() => {
  Object.values(pollTimers).forEach(clearInterval)
  pollTimers.length = 0
  Object.values(wsSockets).forEach(ws => { try { ws.close() } catch (_) { /* */ } })
  wsSockets.length = 0
  // 清理 urlCache
  Object.values(urlCache).forEach(u => URL.revokeObjectURL(u))
  urlCache.length = 0
  // 清空 task 列表，防止 recoverTasks 重复添加
  tasks.value = []
})
</script>

<style scoped>
.upload-zone {
  border: 2px dashed var(--border); border-radius: var(--radius);
  padding: 52px 24px; text-align: center; cursor: pointer;
  transition: border-color var(--transition), background var(--transition);
}
.upload-zone:hover, .upload-zone.drag { border-color: var(--primary); background: var(--primary-bg); }
.upload-icon { color: var(--text2); margin-bottom: 10px; }
.upload-icon svg { width: 44px; height: 44px; }
.upload-title { font-weight: 600; margin-bottom: 2px; font-size: 1rem; }
.upload-hint { color: var(--text2); font-size: .85rem; margin-top: 6px; }

.files-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px; margin-bottom: 4px;
}
.file-card {
  position: relative; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden;
  transition: box-shadow var(--transition);
}
.file-card:hover { box-shadow: var(--shadow-lg); }
.card-thumb { width: 100%; height: 130px; background: #000; overflow: hidden; position: relative; }
.card-thumb video { width: 100%; height: 100%; object-fit: cover; }
.audio-placeholder {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #1e1b4b, #312e81); color: #a5b4fc;
}

/* spinner 等待覆盖层 */
.task-thumb video { opacity: .55; }
.task-thumb .audio-placeholder { opacity: .55; }
.wait-overlay {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 16px; gap: 10px;
  background: linear-gradient(to top, rgba(0,0,0,.80) 0%, rgba(0,0,0,.25) 55%, transparent 100%);
}
.wait-spinner {
  width: 28px; height: 28px; border: 3px solid rgba(255,255,255,.25);
  border-top-color: #fff; border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.wait-text {
  font-size: .72rem; color: rgba(255,255,255,.9); font-weight: 500;
  text-align: center; line-height: 1.4; max-width: 90%;
  text-shadow: 0 1px 2px rgba(0,0,0,.5);
}

.card-info { padding: 10px 12px; display: flex; flex-direction: column; gap: 3px; }
.card-name { font-size: .8rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.badge-sm { align-self: flex-start; }
.card-remove {
  position: absolute; top: 6px; right: 6px; width: 22px; height: 22px;
  border: none; background: rgba(0,0,0,.55); color: #fff; border-radius: 50%;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity var(--transition);
}
.file-card:hover .card-remove { opacity: 1; }
.add-more {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  border: 2px dashed var(--border); cursor: pointer; background: var(--surface2);
}
.add-more:hover { border-color: var(--primary); background: var(--primary-bg); }
.add-icon { font-size: 2rem; color: var(--text2); font-weight: 300; line-height: 1; }
.add-text { font-size: .82rem; color: var(--text2); margin-top: 4px; }

.controls { display: flex; align-items: center; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
.file-count { flex: 1; min-width: 0; font-size: .88rem; color: var(--primary); }

.badge-ok { background: var(--success-bg); color: #065f46; }
.badge-fail { background: var(--danger-bg); color: var(--danger); }
.badge-cancel { background: var(--surface2); color: var(--text2); }
.badge-running { background: var(--primary-bg); color: var(--primary); }

.history-row {
  display: flex; align-items: center; gap: 10px; padding: 10px 0;
  border-bottom: 1px solid var(--border);
  transition: background var(--transition);
}
.history-row:last-child { border-bottom: none; }
.history-row:hover { background: var(--primary-bg); border-radius: 4px; padding-left: 8px; padding-right: 4px; }
.hist-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; cursor: pointer; }
.hist-name { font-size: .85rem; font-weight: 600; }
.hist-meta { font-size: .72rem; color: var(--text2); display: flex; align-items: center; gap: 6px; }
.hist-delete {
  border: none; background: none; color: var(--text2); cursor: pointer;
  padding: 6px; border-radius: var(--radius-sm); flex-shrink: 0;
  opacity: 0; transition: all var(--transition);
}
.history-row:hover .hist-delete { opacity: 1; }
.hist-delete:hover { background: var(--danger-bg); color: var(--danger); }

@media (max-width: 640px) {
  .files-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
  .card-thumb { height: 100px; }
  .controls { flex-direction: column; align-items: stretch; }
}
</style>
