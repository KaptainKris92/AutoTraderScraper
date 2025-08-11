export const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export function apiUrl(path) {
  if (/^https?:\/\//i.test(path)) return path; // already absolute
  const needsSlash = path.startsWith("/") ? "" : "/";
  return `${API_BASE}${needsSlash}${path}`;
}

export function apiFetch(path, init) {
  return fetch(apiUrl(path), init);
}
