# SCP Tool Roadmap

## Must-have (security/functionality)

1. **Authentication** — Right now anyone who can hit port 8000 can use your servers. Need login (even just a simple password/token, or OAuth if you want proper multi-user).
2. **HTTPS** — Passwords and files are sent in plaintext HTTP. Need TLS (reverse proxy with nginx/caddy, or built-in SSL certs).
3. **Per-user server configs** — Right now all servers are in one shared JSON file. Each user needs their own isolated configs so they can't see/use each other's SSH credentials.
4. **Per-user encryption keys** — Currently one Fernet key encrypts all passwords. Each user's credentials need their own key.
5. **Host key verification UX** — We switched to RejectPolicy which is secure, but other users won't have your known_hosts. Need a "trust on first use" flow — show the fingerprint, let them accept it, save it per-user.
6. **Rate limiting** — Prevent brute-force/abuse on the API endpoints.
7. **Upload size configurability** — Different users may need different limits. Admin-configurable.

## Should-have (usability)

8. **Database backend** — Replace the JSON file with SQLite or Postgres. JSON doesn't handle concurrent writes safely.
9. **Transfer history/logs** — "What did I upload, when, where?" Audit trail.
10. **Download support** — People will expect to pull files too, not just push.
11. **Drag-and-drop folders** — Upload entire directories, not just individual files.
12. **Chunked/resumable uploads** — For large files (like your 6 GB VDI), support resume on failure instead of starting over.
13. **Progress via WebSocket** — Real-time per-file progress instead of polling.
14. **Error messages that help** — "Connection refused" → "Check if SSH is running on port 22". User-friendly error mapping.

## Nice-to-have (polish)

15. **Multi-language** — i18n if you're targeting international users.
16. **Dark/light theme toggle** — Currently dark only.
17. **Mobile-responsive layout** — Tailwind makes this easy but it needs testing.
18. **Bookmarked paths** — Save frequently used remote directories per server.
19. **Notifications** — Browser notification when a long upload finishes.
20. **Deployment packaging** — Docker image so others can `docker run` it in one command.
