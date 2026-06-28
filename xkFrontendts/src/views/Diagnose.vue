<template>
  <a-layout class="min-h-screen" style="background-color: #e0e0e0">
    <a-layout-header class="flex flex-row justify-between items-center" style="background-color: #e0e0e0; height: 64px; line-height: 64px">
      <router-link to="/">
        <div class="bg-[url(../assets/myLogo.png)] bg-cover bg-center h-10 w-50"></div>
      </router-link>
    </a-layout-header>
    <a-layout-content class="flex rounded-lg overflow-hidden" style="height: calc(100vh - 64px); background-color: #f5f5f5">
      <!-- 左侧：历史列表 -->
      <div class="overflow-y-auto p-3" style="width: 280px; min-width: 280px; background-color: #eeeef0" @scroll="onScroll" ref="listPanel">
        <div class="px-3 py-3 mb-2 flex justify-between items-center">
          <div><span class="font-bold text-base">同步历史</span></div>
          <div>
            <a-button size="small" @click="refresh" :disabled="loading">
              <div class="flex items-center"><ReloadOutlined :spin="loading" /></div>
            </a-button>
          </div>
        </div>
        <div
          v-for="log in logs"
          :key="log.id"
          class="py-2 px-3 cursor-pointer text-sm"
          :class="{ 'selected-item': selectedId === log.id }"
          style="border-bottom: 1px solid #e5e5e7"
          @click="selectLog(log)"
        >
          <div class="flex items-center gap-2">
            <span v-if="log.status === 'running'" class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
            <span v-else-if="log.status === 'completed'" class="w-2 h-2 rounded-full bg-green-500"></span>
            <span v-else class="w-2 h-2 rounded-full bg-red-500"></span>
            <span class="truncate">{{ log.calendarName }}</span>
          </div>
          <div class="text-gray-400 text-sm mt-1">{{ log.startTime }}</div>
        </div>
        <div v-if="loadingMore" class="text-center py-2"><a-spin size="small" /></div>
      </div>

      <!-- 右侧：详情面板 -->
      <div class="flex-1 flex flex-col">
        <template v-if="selectedLog">
          <div class="px-3 py-3 flex items-center gap-2" style="background-color: #fafafa; border-bottom: 1px solid #f0f0f0">
            <span class="font-bold text-base">{{ selectedLog.calendarName }}</span>
            <a-tag v-if="selectedLog.status === 'completed'" color="success">完成</a-tag>
            <a-tag v-else-if="selectedLog.status === 'failed'" color="error">失败</a-tag>
            <a-tag v-else-if="selectedLog.status === 'running'" color="processing">进行中</a-tag>
            <span v-if="selectedLog.msg" class="text-gray-400 text-sm truncate">{{ selectedLog.msg }}</span>
          </div>
          <div v-if="selectedLog.errorMessage" class="px-3 py-2 bg-red-50 text-red-600 text-sm">
            {{ selectedLog.errorMessage }}
          </div>
          <div ref="logPanel" class="flex-1 overflow-y-auto p-3 font-mono text-sm" style="background-color: #fafafa">
            <div v-if="logLines.length === 0 && selectedLog.status !== 'running'" class="text-gray-400">
              暂无日志内容
            </div>
            <div v-for="(line, i) in logLines" :key="i" :class="logLineClass(line.level)" class="leading-relaxed">{{ line.message }}</div>
          </div>
        </template>
        <div v-else class="flex-1 flex items-center justify-center text-gray-400">
          请选择左侧一条日志查看详情
        </div>
      </div>
    </a-layout-content>
  </a-layout>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios'
import { ReloadOutlined } from '@ant-design/icons-vue'

interface FetchLog {
  id: number
  calendarId: number
  calendarName: string
  startTime: string
  endTime: string | null
  status: string
  totalCourses: number
  totalPages: number
  msg: string | null
  errorMessage: string | null
  fullLog?: string | null
}

interface LogLine {
  level: 'info' | 'warning' | 'error'
  message: string
}

/** 解析 fullLog 中的一行 NDJSON → LogLine */
function parseLogLine(raw: string): LogLine {
  try {
    const obj = JSON.parse(raw)
    if (obj.l && obj.m) {
      return { level: obj.l, message: obj.m }
    }
  } catch { /* malformed line */ }
  return { level: 'info', message: raw }
}

const LEVEL_CLASS: Record<string, string> = {
  info: 'text-gray-600',
  warning: 'text-amber-600',
  error: 'text-red-600',
}

export default defineComponent({
  components: { ReloadOutlined },
  data() {
    return {
      loading: false,
      loadingMore: false,
      logs: [] as FetchLog[],
      page: 1,
      pageSize: 30,
      hasMore: true,
      selectedId: null as number | null,
      selectedLog: null as FetchLog | null,
      logLines: [] as LogLine[],
      eventSource: null as EventSource | null,
    }
  },
  mounted() {
    this.fetchHistory()
  },
  beforeUnmount() {
    this.closeSSE()
  },
  methods: {
    logLineClass(level: string): string {
      return LEVEL_CLASS[level] || 'text-gray-700'
    },
    async fetchHistory() {
      this.loading = true
      this.page = 1
      try {
        const res = await axios.get('/api/sync/history', {
          params: { page: 1, pageSize: this.pageSize }
        })
        this.logs = res.data.data
        this.hasMore = res.data.data.length < (res.data.pagination?.total || 0)
      } catch {
        // silent
      } finally {
        this.loading = false
      }
    },
    async loadMore() {
      if (this.loadingMore || !this.hasMore) return
      this.loadingMore = true
      this.page++
      try {
        const res = await axios.get('/api/sync/history', {
          params: { page: this.page, pageSize: this.pageSize }
        })
        const more = res.data.data
        this.logs.push(...more)
        this.hasMore = this.logs.length < (res.data.pagination?.total || 0)
      } catch {
        // silent
      } finally {
        this.loadingMore = false
      }
    },
    refresh() {
      this.fetchHistory()
    },
    onScroll() {
      const el = this.$refs.listPanel as HTMLElement
      if (!el) return
      if (el.scrollHeight - el.scrollTop - el.clientHeight < 50) {
        this.loadMore()
      }
    },
    async selectLog(log: FetchLog) {
      this.selectedId = log.id
      this.closeSSE()
      this.logLines = []

      // 获取完整数据（含 fullLog）
      try {
        const res = await axios.get(`/api/sync/history/${log.id}`)
        this.selectedLog = res.data.data
        if (this.selectedLog?.fullLog) {
          this.logLines = this.selectedLog.fullLog
            .split('\n')
            .filter(line => line.trim())
            .map(parseLogLine)
        }
      } catch {
        this.selectedLog = log
      }

      // 如果在运行中 → 连接 SSE
      if (log.status === 'running') {
        this.connectSSE(log.id)
      }

      // 滚动日志到底部
      this.$nextTick(() => {
        const panel = this.$refs.logPanel as HTMLElement
        if (panel) panel.scrollTop = panel.scrollHeight
      })
    },
    connectSSE(logId: number) {
      const url = `/api/sync/history/${logId}/stream`
      this.eventSource = new EventSource(url)

      this.eventSource.addEventListener('log', (e) => {
        try {
          const data = JSON.parse(e.data)
          this.logLines.push({ level: data.level || 'info', message: data.message })
          this.$nextTick(() => {
            const panel = this.$refs.logPanel as HTMLElement
            if (panel) panel.scrollTop = panel.scrollHeight
          })
        } catch { /* ignore */ }
      })

      this.eventSource.addEventListener('end', () => {
        this.closeSSE()
        axios.get(`/api/sync/history/${logId}`)
          .then(res => {
            this.selectedLog = res.data.data
            if (this.selectedLog?.fullLog) {
              this.logLines = this.selectedLog.fullLog
                .split('\n')
                .filter(line => line.trim())
                .map(parseLogLine)
            }
            this.$nextTick(() => {
              const panel = this.$refs.logPanel as HTMLElement
              if (panel) panel.scrollTop = panel.scrollHeight
            })
          })
        this.refresh()
      })

      this.eventSource.onerror = () => {
        this.closeSSE()
      }
    },
    closeSSE() {
      if (this.eventSource) {
        this.eventSource.close()
        this.eventSource = null
      }
    },
  },
})
</script>

<style scoped>
.selected-item { background-color: #ccccce; }
</style>
