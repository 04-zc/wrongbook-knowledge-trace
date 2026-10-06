// PWA 离线回归：在 Node 中加载 static/sw.js，用桩对象验证缓存策略。
// 运行：node tools/test_pwa_offline.js
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const PASS = [];
const FAIL = [];

function check(name, condition, detail) {
    const line = detail === undefined ? name : name + ' :: ' + detail;
    (condition ? PASS : FAIL).push(line);
}

class FakeResponse {
    constructor(body, init) {
        const options = init || {};
        this.body = body;
        this.status = options.status === undefined ? 200 : options.status;
        this.headers = options.headers || {};
        this.ok = this.status >= 200 && this.status < 300;
    }

    clone() {
        return new FakeResponse(this.body, { status: this.status, headers: this.headers });
    }

    text() {
        return Promise.resolve(String(this.body));
    }

    static error() {
        return new FakeResponse('', { status: 0 });
    }
}

function requestUrl(request) {
    return typeof request === 'string' ? request : request.url;
}

class FakeCache {
    constructor() {
        this.store = new Map();
    }

    addAll(urls) {
        urls.forEach(url => this.store.set(url, new FakeResponse('shell')));
        return Promise.resolve();
    }

    put(request, response) {
        this.store.set(requestUrl(request), response.clone());
        return Promise.resolve();
    }

    match(request) {
        return Promise.resolve(this.store.get(requestUrl(request)));
    }

    delete(request) {
        this.store.delete(requestUrl(request));
        return Promise.resolve(true);
    }
}

const cacheStores = new Map();
const handlers = {};
let fetchCalls = [];
let fetchImpl = () => Promise.reject(new Error('fetch stub 未设置'));

const sandbox = {
    console,
    URL,
    Response: FakeResponse,
    fetch: request => {
        fetchCalls.push(requestUrl(request));
        return fetchImpl(request);
    },
    caches: {
        open: name => {
            if (!cacheStores.has(name)) cacheStores.set(name, new FakeCache());
            return Promise.resolve(cacheStores.get(name));
        },
        keys: () => Promise.resolve(Array.from(cacheStores.keys())),
        delete: name => {
            cacheStores.delete(name);
            return Promise.resolve(true);
        }
    },
    self: {
        location: { origin: 'http://localhost:5000' },
        addEventListener: (type, handler) => {
            handlers[type] = handler;
        },
        skipWaiting: () => Promise.resolve(),
        clients: { claim: () => Promise.resolve() }
    }
};

vm.createContext(sandbox);
const swPath = path.join(__dirname, '..', 'static', 'sw.js');
vm.runInContext(fs.readFileSync(swPath, 'utf8'), sandbox, { filename: 'sw.js' });

async function fire(type, event) {
    let waited = null;
    event.waitUntil = promise => {
        waited = promise;
    };
    handlers[type](event);
    if (waited) await waited;
}

async function requestThroughWorker(url) {
    let responded = null;
    handlers.fetch({
        request: { method: 'GET', url, mode: 'cors' },
        respondWith: promise => {
            responded = promise;
        }
    });
    if (responded) return await responded;
    return null;
}

(async () => {
    await fire('install', {});
    const shell = cacheStores.get('wrongbook-shell-v6');
    check('安装时写入 v6 外壳缓存',
        Boolean(shell && shell.store.has('/static/app.js')));

    fetchCalls = [];
    const uploadResponse = await requestThroughWorker('http://localhost:5000/uploads/u1/secret.png');
    check('上传文件请求不经过 Service Worker', uploadResponse === null);
    check('上传文件不触发网络或缓存写入', fetchCalls.length === 0);

    await fire('message', { data: { type: 'SET_USER', userId: '1' } });
    if (!cacheStores.has('wrongbook-user-1-v6')) {
        cacheStores.set('wrongbook-user-1-v6', new FakeCache());
    }
    fetchCalls = [];
    fetchImpl = () => Promise.resolve(new FakeResponse('me-json'));
    const meResponse = await requestThroughWorker('http://localhost:5000/api/auth/me');
    const userCache = cacheStores.get('wrongbook-user-1-v6');
    check('/api/auth/me 走网络', Boolean(meResponse) && meResponse.body === 'me-json');
    check('/api/auth/me 不写入缓存',
        !(userCache && userCache.store.has('http://localhost:5000/api/auth/me')));

    userCache.store.set('http://localhost:5000/api/questions', new FakeResponse('cached-questions'));
    fetchImpl = () => Promise.reject(new Error('offline'));
    const offlineResponse = await requestThroughWorker('http://localhost:5000/api/questions');
    check('离线时业务接口回退到用户缓存',
        Boolean(offlineResponse) && offlineResponse.body === 'cached-questions');

    fetchImpl = () => Promise.resolve(new FakeResponse('fresh-questions'));
    await requestThroughWorker('http://localhost:5000/api/questions');
    check('在线时业务接口刷新用户缓存',
        userCache.store.get('http://localhost:5000/api/questions').body === 'fresh-questions');

    cacheStores.set('wrongbook-shell-v4', new FakeCache());
    cacheStores.set('wrongbook-user-9-v4', new FakeCache());
    await fire('activate', {});
    check('升级时清理 v4 外壳缓存', !cacheStores.has('wrongbook-shell-v4'));
    check('升级时清理旧用户缓存', !cacheStores.has('wrongbook-user-9-v4'));
    check('升级后保留 v6 缓存',
        cacheStores.has('wrongbook-shell-v6') && cacheStores.has('wrongbook-user-1-v6'));

    console.log('=== PASS (' + PASS.length + ') ===');
    PASS.forEach(name => console.log('  ok  ' + name));
    if (FAIL.length) {
        console.log('=== FAIL (' + FAIL.length + ') ===');
        FAIL.forEach(name => console.log('  XX  ' + name));
    }
    process.exitCode = FAIL.length ? 1 : 0;
})().catch(error => {
    console.error('FAILED: ' + error.message);
    process.exitCode = 1;
});
