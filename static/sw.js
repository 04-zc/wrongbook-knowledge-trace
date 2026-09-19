const CACHE_NAME = 'wrongbook-shell-v3';
const META_CACHE = 'wrongbook-sw-meta';
const META_USER_URL = '/__wrongbook_user_id';
const USER_CACHE_PREFIX = 'wrongbook-user-';
const APP_SHELL = [
    '/',
    '/static/style.css',
    '/static/app.js',
    '/static/vue.global.js',
    '/static/axios.min.js',
    '/static/vendor/echarts.min.js',
    '/static/vendor/katex/katex.min.css',
    '/static/vendor/katex/katex.min.js',
    '/static/manifest.webmanifest',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png'
];
const USER_API_PATHS = new Set([
    '/api/auth/me',
    '/api/questions',
    '/api/questions/page',
    '/api/questions/trash',
    '/api/subjects',
    '/api/knowledge_points',
    '/api/kp_tree',
    '/api/weak_points',
    '/api/analytics/trend',
    '/api/analytics/priority',
    '/api/knowledge_graph',
    '/api/reports/summary',
    '/api/review/today',
    '/api/review/plans'
]);

let currentUserId = null;

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(APP_SHELL))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(
                keys
                    .filter(key => key.startsWith('wrongbook-shell-') && key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('message', event => {
    const data = event.data || {};
    if (data.type === 'SET_USER' && data.userId) {
        event.waitUntil(setCurrentUserId(String(data.userId)));
    }
    if (data.type === 'CLEAR_USER') {
        event.waitUntil(clearUserCaches());
    }
});

self.addEventListener('fetch', event => {
    const request = event.request;
    if (request.method !== 'GET') return;

    const url = new URL(request.url);
    if (url.origin !== self.location.origin) return;

    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstApi(request, url));
        return;
    }

    if (request.mode === 'navigate') {
        event.respondWith(networkFirstNavigation(request));
        return;
    }

    event.respondWith(networkFirstStatic(request));
});

function isCacheableApi(pathname) {
    if (USER_API_PATHS.has(pathname)) return true;
    return /^\/api\/questions\/\d+$/.test(pathname);
}

async function setCurrentUserId(userId) {
    currentUserId = userId;
    const metaCache = await caches.open(META_CACHE);
    await metaCache.put(META_USER_URL, new Response(userId, {
        headers: { 'Content-Type': 'text/plain' }
    }));
}

async function getCurrentUserId() {
    if (currentUserId) return currentUserId;
    const metaCache = await caches.open(META_CACHE);
    const response = await metaCache.match(META_USER_URL);
    if (!response) return null;
    currentUserId = (await response.text()).trim() || null;
    return currentUserId;
}

async function clearUserCaches() {
    currentUserId = null;
    const keys = await caches.keys();
    await Promise.all(
        keys
            .filter(key => key.startsWith(USER_CACHE_PREFIX))
            .map(key => caches.delete(key))
    );
    const metaCache = await caches.open(META_CACHE);
    await metaCache.delete(META_USER_URL);
}

async function getUserCache() {
    const userId = await getCurrentUserId();
    if (!userId) return null;
    return caches.open(USER_CACHE_PREFIX + userId + '-v3');
}

async function networkFirstApi(request, url) {
    if (!isCacheableApi(url.pathname)) {
        return fetch(request);
    }
    const cache = await getUserCache();
    if (!cache) return fetch(request);

    try {
        const response = await fetch(request);
        if (response.ok) {
            await cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        const cached = await cache.match(request);
        if (cached) return cached;
        return new Response(JSON.stringify({
            error: '当前处于离线状态，且这项数据还没有缓存。'
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json; charset=utf-8' }
        });
    }
}

async function networkFirstNavigation(request) {
    const cache = await caches.open(CACHE_NAME);
    try {
        const response = await fetch(request);
        if (response.ok) await cache.put('/', response.clone());
        return response;
    } catch (error) {
        return (await cache.match('/')) || Response.error();
    }
}

async function networkFirstStatic(request) {
    const cache = await caches.open(CACHE_NAME);
    try {
        const response = await fetch(request);
        if (response.ok) await cache.put(request, response.clone());
        return response;
    } catch (error) {
        const cached = await cache.match(request, { ignoreSearch: true });
        if (cached) return cached;
        throw error;
    }
}
