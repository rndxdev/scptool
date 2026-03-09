import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export default {
  // Servers
  getServers: () => api.get('/servers').then(r => r.data),
  createServer: (data) => api.post('/servers', data).then(r => r.data),
  updateServer: (id, data) => api.put(`/servers/${id}`, data).then(r => r.data),
  deleteServer: (id) => api.delete(`/servers/${id}`).then(r => r.data),
  testConnection: (id) => api.post(`/servers/${id}/test`).then(r => r.data),

  // SSH Detection
  detectSSH: () => api.get('/ssh/detect').then(r => r.data),

  // Upload
  uploadFiles: (serverId, remoteDir, files, onProgress) => {
    const form = new FormData()
    form.append('server_id', serverId)
    form.append('remote_dir', remoteDir)
    for (const f of files) {
      form.append('files', f)
    }
    return api.post('/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    }).then(r => r.data)
  },

  // Browse
  browseRemote: (serverId, path) =>
    api.get(`/servers/${serverId}/browse`, { params: { path } }).then(r => r.data),
}
