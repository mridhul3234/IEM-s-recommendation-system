const configuredApiBaseUrl = import.meta.env.PUBLIC_API_BASE_URL?.trim();

// Astro exposes PUBLIC_ variables to the browser at build time. Keep the
// development fallback local, but never silently send production traffic to
// an unrelated or stale deployment.
const fallbackApiBaseUrl = import.meta.env.DEV ? 'http://localhost:8000' : '';

export const apiBaseUrl = (configuredApiBaseUrl || fallbackApiBaseUrl).replace(/\/+$/, '');

export function getApiBaseUrl() {
  if (!apiBaseUrl) {
    throw new Error(
      'API configuration is missing. Set PUBLIC_API_BASE_URL to the Render service URL and redeploy Vercel.'
    );
  }
  return apiBaseUrl;
}
