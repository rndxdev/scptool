<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <!-- Header -->
    <header class="mb-8">
      <h1 class="text-3xl font-bold text-white flex items-center gap-3">
        <span class="bg-blue-600 rounded-lg p-2">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </span>
        SCP Tool
      </h1>
      <p class="text-gray-400 mt-1">Secure file transfers without the terminal</p>
    </header>

    <!-- Server Selection / Management -->
    <div class="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">Server</h2>
        <div class="flex gap-2">
          <button
            @click="detectSSH"
            class="text-sm bg-gray-700 hover:bg-gray-600 px-3 py-1.5 rounded-lg transition flex items-center gap-1.5"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Detect SSH
          </button>
          <button
            @click="showServerForm = true; showDetected = false; editingServer = null; resetForm()"
            class="text-sm bg-blue-600 hover:bg-blue-700 px-3 py-1.5 rounded-lg transition"
          >
            + Add Manually
          </button>
        </div>
      </div>

      <!-- Detected SSH Hosts -->
      <div v-if="showDetected && !showServerForm" class="mb-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-medium text-gray-400">Detected from ~/.ssh/config</h3>
          <button @click="showDetected = false" class="text-xs text-gray-500 hover:text-gray-300">Dismiss</button>
        </div>

        <div v-if="detectedKeys.length" class="mb-3 flex flex-wrap gap-2">
          <span v-for="k in detectedKeys" :key="k.path"
            class="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded-md flex items-center gap-1.5">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
            {{ k.name }} ({{ k.type }})
          </span>
        </div>

        <div v-if="detectedHosts.length" class="space-y-2">
          <button
            v-for="h in detectedHosts" :key="h.alias"
            @click="importDetected(h)"
            class="w-full text-left px-4 py-3 rounded-lg border border-gray-700 hover:border-blue-500 bg-gray-800/50 hover:bg-blue-500/10 transition flex items-center justify-between"
          >
            <div>
              <div class="font-medium">{{ h.alias }}</div>
              <div class="text-sm text-gray-400">
                {{ h.user || '(no user)' }}@{{ h.hostname }}:{{ h.port }}
              </div>
              <div v-if="h.identity_file" class="text-xs text-gray-500 mt-0.5">
                Key: {{ h.identity_file.split(/[/\\]/).pop() }}
              </div>
            </div>
            <span class="text-xs text-blue-400 bg-blue-500/10 px-2 py-1 rounded">Import</span>
          </button>
        </div>

        <div v-else class="text-gray-500 text-sm text-center py-4">
          No hosts found in ~/.ssh/config
          <span v-if="detectedKeys.length">
            — but {{ detectedKeys.length }} key{{ detectedKeys.length > 1 ? 's' : '' }} detected.
            Click "+ Add Manually" and keys will be pre-filled.
          </span>
        </div>
      </div>

      <!-- Server List -->
      <div v-if="servers.length && !showServerForm" class="space-y-2">
        <button
          v-for="s in servers" :key="s.id"
          @click="selectedServer = s"
          class="w-full text-left px-4 py-3 rounded-lg border transition flex items-center justify-between group"
          :class="selectedServer?.id === s.id
            ? 'border-blue-500 bg-blue-500/10'
            : 'border-gray-700 hover:border-gray-600 bg-gray-800/50'"
        >
          <div>
            <div class="font-medium">{{ s.name }}</div>
            <div class="text-sm text-gray-400">{{ s.username }}@{{ s.host }}:{{ s.port }}</div>
          </div>
          <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition">
            <button @click.stop="startEdit(s)" class="text-gray-400 hover:text-white text-xs px-2 py-1 bg-gray-700 rounded">
              Edit
            </button>
            <button @click.stop="testServer(s.id)" class="text-gray-400 hover:text-green-400 text-xs px-2 py-1 bg-gray-700 rounded">
              Test
            </button>
            <button @click.stop="deleteServer(s.id)" class="text-gray-400 hover:text-red-400 text-xs px-2 py-1 bg-gray-700 rounded">
              Delete
            </button>
          </div>
        </button>
      </div>

      <div v-else-if="!showServerForm && !showDetected" class="text-gray-500 text-center py-6">
        No servers configured. Click "Detect SSH" to auto-import or add one manually.
      </div>

      <!-- Server Form -->
      <div v-if="showServerForm" class="space-y-4">
        <h3 class="font-medium text-gray-300">{{ editingServer ? 'Edit' : 'Add' }} Server</h3>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-gray-400 mb-1">Name</label>
            <input v-model="form.name" class="input" placeholder="My Server" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Host</label>
            <input v-model="form.host" class="input" placeholder="192.168.1.100" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Port</label>
            <input v-model.number="form.port" type="number" class="input" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Username</label>
            <input v-model="form.username" class="input" placeholder="root" />
          </div>
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Auth Type</label>
          <div class="flex gap-4">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="radio" v-model="form.auth_type" value="key" class="accent-blue-500" />
              <span class="text-sm">SSH Key</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="radio" v-model="form.auth_type" value="password" class="accent-blue-500" />
              <span class="text-sm">Password</span>
            </label>
          </div>
        </div>

        <div v-if="form.auth_type === 'key'">
          <label class="block text-sm text-gray-400 mb-1">SSH Key Path</label>
          <input v-model="form.key_path" class="input" placeholder="C:\Users\you\.ssh\id_rsa" />
          <label class="block text-sm text-gray-400 mb-1 mt-3">Key Passphrase (optional)</label>
          <input v-model="form.key_passphrase" type="password" class="input" />
        </div>

        <div v-if="form.auth_type === 'password'">
          <label class="block text-sm text-gray-400 mb-1">Password</label>
          <input v-model="form.password" type="password" class="input" />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Default Remote Directory</label>
          <RemoteDirInput
            v-model="form.default_remote_dir"
            :server-id="editingServer?.id || ''"
          />
        </div>

        <div class="flex gap-3">
          <button @click="saveServer" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition text-sm">
            {{ editingServer ? 'Update' : 'Add' }} Server
          </button>
          <button @click="showServerForm = false" class="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition text-sm">
            Cancel
          </button>
        </div>
      </div>

      <!-- Toast -->
      <div v-if="toast" class="mt-3 text-sm px-3 py-2 rounded-lg" :class="toast.type === 'ok' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'">
        {{ toast.message }}
      </div>
    </div>

    <!-- Upload Area -->
    <div v-if="selectedServer" class="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
      <h2 class="text-lg font-semibold mb-4">Upload Files</h2>

      <div class="mb-4">
        <label class="block text-sm text-gray-400 mb-1">Remote Directory</label>
        <RemoteDirInput
          v-model="remoteDir"
          :server-id="selectedServer?.id || ''"
        />
      </div>

      <!-- Drop Zone -->
      <div
        @dragover.prevent="dragOver = true"
        @dragleave="dragOver = false"
        @drop.prevent="handleDrop"
        @click="$refs.fileInput.click()"
        class="border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition"
        :class="dragOver ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 hover:border-gray-500'"
      >
        <svg class="w-12 h-12 mx-auto mb-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p class="text-gray-400 mb-1">Drop files here or click to browse</p>
        <p class="text-gray-600 text-sm">Files will be uploaded to {{ selectedServer.name }}</p>
        <p class="text-gray-600 text-xs mt-1">Max 2 GB per upload</p>
      </div>
      <input ref="fileInput" type="file" multiple class="hidden" @change="handleFileSelect" />

      <!-- Selected Files -->
      <div v-if="pendingFiles.length" class="mt-4 space-y-2">
        <div v-for="(f, i) in pendingFiles" :key="i"
          class="flex items-center justify-between bg-gray-800 rounded-lg px-4 py-2">
          <div class="flex items-center gap-3">
            <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span class="text-sm">{{ f.name }}</span>
            <span class="text-xs text-gray-500">{{ formatSize(f.size) }}</span>
          </div>
          <button @click="pendingFiles.splice(i, 1)" class="text-gray-500 hover:text-red-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <button
          @click="uploadAll"
          :disabled="uploading"
          class="w-full mt-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 py-3 rounded-lg font-medium transition"
        >
          <span v-if="uploading" class="flex items-center justify-center gap-2">
            <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Uploading... {{ uploadPercent }}%
          </span>
          <span v-else>Upload {{ pendingFiles.length }} file{{ pendingFiles.length > 1 ? 's' : '' }}</span>
        </button>
      </div>

      <!-- Upload Results -->
      <div v-if="uploadResults.length" class="mt-4 space-y-2">
        <h3 class="text-sm font-medium text-gray-400 mb-2">Results</h3>
        <div v-for="r in uploadResults" :key="r.local_path"
          class="flex items-center gap-3 text-sm px-4 py-2 rounded-lg"
          :class="r.status === 'success' ? 'bg-green-900/30 text-green-300' : 'bg-red-900/30 text-red-300'">
          <svg v-if="r.status === 'success'" class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <svg v-else class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <span>{{ r.remote_path || r.local_path }}</span>
          <span v-if="r.error" class="text-red-400 text-xs">{{ r.error }}</span>
        </div>
      </div>
    </div>

    <!-- No server selected prompt -->
    <div v-else-if="servers.length && !showServerForm" class="bg-gray-900 rounded-xl border border-gray-800 p-12 text-center">
      <p class="text-gray-500">Select a server above to start uploading files</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from './api.js'
import RemoteDirInput from './RemoteDirInput.vue'

const servers = ref([])
const selectedServer = ref(null)
const showServerForm = ref(false)
const editingServer = ref(null)
const toast = ref(null)

const showDetected = ref(false)
const detectedHosts = ref([])
const detectedKeys = ref([])

const form = ref({
  name: '', host: '', port: 22, username: '',
  auth_type: 'key', key_path: '', key_passphrase: '',
  password: '', default_remote_dir: '~',
})

const remoteDir = ref('~')
const pendingFiles = ref([])
const uploading = ref(false)
const uploadPercent = ref(0)
const uploadResults = ref([])
const dragOver = ref(false)


onMounted(async () => {
  await loadServers()
  // Auto-detect on first visit if no servers configured
  if (!servers.value.length) {
    await detectSSH()
  }
})

watch(selectedServer, (s) => {
  if (s) remoteDir.value = s.default_remote_dir || '~'
})

async function loadServers() {
  servers.value = await api.getServers()
}

async function detectSSH() {
  try {
    const result = await api.detectSSH()
    detectedHosts.value = result.hosts || []
    detectedKeys.value = result.keys || []
    showDetected.value = true
    showServerForm.value = false
  } catch (e) {
    showToast('error', 'Failed to detect SSH config')
  }
}

function importDetected(host) {
  form.value = {
    name: host.alias,
    host: host.hostname,
    port: host.port || 22,
    username: host.user || '',
    auth_type: 'key',
    key_path: host.identity_file || '',
    key_passphrase: '',
    password: '',
    default_remote_dir: '~',
  }
  editingServer.value = null
  showServerForm.value = true
  showDetected.value = false
}

function resetForm() {
  // Pre-fill key path from detected keys if available
  const bestKey = detectedKeys.value.length ? detectedKeys.value[0].path : ''
  form.value = {
    name: '', host: '', port: 22, username: '',
    auth_type: 'key', key_path: bestKey, key_passphrase: '',
    password: '', default_remote_dir: '~',
  }
}

function startEdit(server) {
  editingServer.value = server
  form.value = {
    name: server.name,
    host: server.host,
    port: server.port,
    username: server.username,
    auth_type: server.auth_type || 'key',
    key_path: server.key_path || '',
    key_passphrase: '',
    password: '',
    default_remote_dir: server.default_remote_dir || '~',
  }
  showServerForm.value = true
}

async function saveServer() {
  try {
    if (editingServer.value) {
      await api.updateServer(editingServer.value.id, form.value)
    } else {
      await api.createServer(form.value)
    }
    showServerForm.value = false
    await loadServers()
    showToast('ok', editingServer.value ? 'Server updated' : 'Server added')
  } catch (e) {
    showToast('error', e.response?.data?.detail || 'Failed to save server')
  }
}

async function deleteServer(id) {
  await api.deleteServer(id)
  if (selectedServer.value?.id === id) selectedServer.value = null
  await loadServers()
  showToast('ok', 'Server deleted')
}

async function testServer(id) {
  showToast('ok', 'Testing connection...')
  const result = await api.testConnection(id)
  showToast(result.status, result.message)
}

function handleDrop(e) {
  dragOver.value = false
  const files = [...e.dataTransfer.files]
  pendingFiles.value.push(...files)
}

function handleFileSelect(e) {
  const files = [...e.target.files]
  pendingFiles.value.push(...files)
  e.target.value = ''
}

async function uploadAll() {
  if (!selectedServer.value || !pendingFiles.value.length) return
  uploading.value = true
  uploadPercent.value = 0
  uploadResults.value = []

  try {
    const result = await api.uploadFiles(
      selectedServer.value.id,
      remoteDir.value,
      pendingFiles.value,
      (e) => {
        if (e.total) uploadPercent.value = Math.round((e.loaded / e.total) * 100)
      },
    )
    uploadResults.value = result.results
    pendingFiles.value = []
  } catch (e) {
    showToast('error', e.response?.data?.detail || 'Upload failed')
  } finally {
    uploading.value = false
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function showToast(type, message) {
  toast.value = { type, message }
  setTimeout(() => { toast.value = null }, 4000)
}
</script>

<style>
.input {
  @apply w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm
    focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition;
}
</style>
