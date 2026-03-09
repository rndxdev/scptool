<template>
  <div class="relative" ref="wrapper">
    <div class="relative">
      <input
        ref="inputEl"
        :value="modelValue"
        @input="onInput($event.target.value)"
        @keydown="onKeydown"
        @focus="onFocus"
        @blur="onBlur"
        class="input w-full pr-8"
        :placeholder="placeholder"
        autocomplete="off"
        spellcheck="false"
      />
      <!-- Loading spinner inside input -->
      <div v-if="loading" class="absolute right-2.5 top-1/2 -translate-y-1/2">
        <svg class="animate-spin w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    </div>

    <!-- Autocomplete dropdown -->
    <div
      v-if="showDropdown && suggestions.length"
      class="absolute z-20 left-0 right-0 mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-2xl overflow-hidden"
    >
      <div class="max-h-52 overflow-y-auto">
        <button
          v-for="(s, i) in suggestions" :key="s.name"
          @mousedown.prevent="selectSuggestion(s)"
          class="w-full text-left px-3 py-1.5 flex items-center gap-2 text-sm transition"
          :class="i === highlightIndex ? 'bg-blue-600/30 text-white' : 'text-gray-300 hover:bg-gray-700/60'"
        >
          <svg v-if="s.is_dir" class="w-3.5 h-3.5 text-blue-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <svg v-else class="w-3.5 h-3.5 text-gray-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span class="truncate">{{ s.name }}<span v-if="s.is_dir" class="text-gray-500">/</span></span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import api from './api.js'

const props = defineProps({
  modelValue: { type: String, default: '' },
  serverId: { type: String, default: '' },
  placeholder: { type: String, default: '/home/user/uploads' },
})

const emit = defineEmits(['update:modelValue'])

const inputEl = ref(null)
const wrapper = ref(null)

const suggestions = ref([])
const showDropdown = ref(false)
const highlightIndex = ref(-1)
const loading = ref(false)

// Cache: parentDir -> entries[]
const dirCache = new Map()

let fetchId = 0 // dedup in-flight requests
let debounceTimer = null
let navigating = false // true while arrow-key navigating, prevents highlight reset

function onInput(value) {
  navigating = false
  highlightIndex.value = -1
  emit('update:modelValue', value)
  debouncedFetch(value)
}

function onFocus() {
  // Only reshow existing suggestions, don't fire new requests on focus
  if (suggestions.value.length) {
    showDropdown.value = true
  }
}

function onBlur() {
  // Small delay so mousedown on suggestion fires first
  setTimeout(() => { showDropdown.value = false }, 150)
}

function onKeydown(e) {
  const dropdownActive = showDropdown.value && suggestions.value.length > 0

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (!dropdownActive) {
      debouncedFetch(props.modelValue, true)
      return
    }
    navigating = true
    highlightIndex.value = Math.min(highlightIndex.value + 1, suggestions.value.length - 1)
    scrollToHighlighted()
    return
  }

  if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (!dropdownActive) return
    navigating = true
    highlightIndex.value = Math.max(highlightIndex.value - 1, 0)
    scrollToHighlighted()
    return
  }

  if (e.key === 'Enter' || e.key === 'Tab') {
    if (dropdownActive) {
      e.preventDefault()
      if (highlightIndex.value >= 0 && highlightIndex.value < suggestions.value.length) {
        selectSuggestion(suggestions.value[highlightIndex.value])
      } else if (suggestions.value.length === 1) {
        selectSuggestion(suggestions.value[0])
      }
    } else if (e.key === 'Tab') {
      e.preventDefault()
      debouncedFetch(props.modelValue, true)
    }
    return
  }

  if (e.key === 'Escape') {
    if (dropdownActive) {
      e.preventDefault()
      showDropdown.value = false
    }
    return
  }
}

function scrollToHighlighted() {
  nextTick(() => {
    const list = wrapper.value?.querySelector('.overflow-y-auto')
    const item = list?.children[highlightIndex.value]
    if (item) {
      item.scrollIntoView({ block: 'nearest' })
    }
  })
}

function selectSuggestion(entry) {
  const parentDir = getParentDir(props.modelValue)
  const base = parentDir === '/' ? '/' : parentDir + '/'
  const newPath = base + entry.name
  if (entry.is_dir) {
    emit('update:modelValue', newPath + '/')
    // Auto-fetch children of this dir
    nextTick(() => debouncedFetch(newPath + '/', true))
  } else {
    emit('update:modelValue', newPath)
    showDropdown.value = false
  }
  highlightIndex.value = -1
}

function debouncedFetch(value, immediate = false) {
  clearTimeout(debounceTimer)
  if (immediate) {
    fetchSuggestions(value)
  } else {
    debounceTimer = setTimeout(() => fetchSuggestions(value), 200)
  }
}

async function fetchSuggestions(value) {
  if (!props.serverId || !value) {
    suggestions.value = []
    showDropdown.value = false
    return
  }

  // Figure out what directory to list and what prefix to filter by
  const parentDir = getParentDir(value)
  const partial = getPartialName(value)

  const id = ++fetchId

  // Check cache first
  if (dirCache.has(parentDir)) {
    const entries = dirCache.get(parentDir)
    filterAndShow(entries, partial, id)
    return
  }

  loading.value = true
  try {
    const result = await api.browseRemote(props.serverId, parentDir)
    if (id !== fetchId) {
      loading.value = false
      return
    }
    const entries = result.entries || []
    dirCache.set(parentDir, entries)
    if (result.path !== parentDir) {
      dirCache.set(result.path, entries)
    }
    filterAndShow(entries, partial, id)
  } catch {
    suggestions.value = []
    showDropdown.value = false
  } finally {
    loading.value = false
  }
}

function filterAndShow(entries, partial, id) {
  if (id !== fetchId) return
  let filtered = entries
  if (partial) {
    const lower = partial.toLowerCase()
    filtered = entries.filter(e => e.name.toLowerCase().startsWith(lower))
  }
  filtered = filtered.slice(0, 15)
  suggestions.value = filtered
  // Don't reset highlight if user is arrow-navigating
  if (!navigating) {
    highlightIndex.value = filtered.length === 1 ? 0 : -1
  }
  showDropdown.value = filtered.length > 0
}

function getParentDir(path) {
  if (!path || path === '/' || path === '~') return path || '~'
  // If path ends with /, the parent is the path itself (we're listing that dir)
  if (path.endsWith('/')) {
    const cleaned = path.replace(/\/+$/, '')
    return cleaned || '/'
  }
  const idx = path.lastIndexOf('/')
  if (idx <= 0) return '/'
  return path.substring(0, idx)
}

function getPartialName(path) {
  if (!path || path === '/' || path === '~') return ''
  if (path.endsWith('/')) return '' // listing full dir, no filter
  const idx = path.lastIndexOf('/')
  return path.substring(idx + 1)
}

// Clear cache when server changes
watch(() => props.serverId, () => {
  dirCache.clear()
  suggestions.value = []
  showDropdown.value = false
})
</script>
