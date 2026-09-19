const { createApp } = Vue;

axios.interceptors.response.use(
    r => r,
    err => {
        const url = (err.config && err.config.url) || '';
        if (err.response && err.response.status === 401 && url.indexOf('/api/auth/') !== 0) {
            window.location.reload();
        }
        return Promise.reject(err);
    }
);

function emptyForm() {
    return {
        subject_id: null,
        title_text: '',
        title_image: '',
        options: [],
        user_answer: '',
        correct_answer: '',
        analysis: '',
        mistake_reason: '',
        source: 'manual',
        status: 0,
        knowledge_points: []
    };
}

const appOptions = {
    data() {
        return {
            currentNav: 'dashboard',
            mobileMenuOpen: false,
            loading: true,
            error: '',
            authUser: null,
            authMode: 'login',
            authUsername: '',
            authPassword: '',
            authConfirm: '',
            authError: '',
            authLoading: false,
            navs: [
                { key: 'dashboard', label: '首页' },
                { key: 'input', label: '错题录入' },
                { key: 'library', label: '错题库' },
                { key: 'review', label: '复习模式' },
                { key: 'weak', label: '薄弱分析' },
                { key: 'graph', label: '知识图谱' },
                { key: 'report', label: '统计报表' },
                { key: 'trash', label: '回收站' },
                { key: 'settings', label: '学科设置' }
            ],
            subjects: [],
            knowledgePoints: [],
            questions: [],
            trashMode: false,
            trashQuestions: [],
            weakPoints: [],
            kpTree: [],
            settings: {
                llm_api_key: '',
                llm_model: 'deepseek-chat',
                ocr_lang: 'ch',
                ocr_use_orientation: 'true',
                ocr_confidence_threshold: '0.5',
                kp_auto_threshold: '0.8',
                kp_pending_threshold: '0.5'
            },
            pendingKps: [],
            showPendingKpModal: false,
            form: emptyForm(),
            filter: { subject_id: null, status: null, kp_id: null, keyword: '' },
            selectedQuestionIds: [],
            batchStatus: 0,
            batchAction: '',
            batchKpModal: { show: false, selected: [] },
            weakFilter: { subject_id: null },
            weakKpName: '',
            weakParentId: null,
            weakAddHint: '',
            reviewFilter: { subject_id: null },
            reviewAdvice: '',
            reviewKps: [],
            reviewRecommendations: [],
            reviewQuestions: [],
            reviewSelectedKp: null,
            reviewSelectedQuestion: null,
            reviewView: 'home',
            reviewAiContent: '',
            reviewAiLoading: false,
            reviewShowAnswer: false,
            reviewLoading: false,
            reviewPlans: [],
            reviewPlanCounts: { today: 0, overdue: 0, total: 0 },
            planDate: new Date().toISOString().slice(0, 10),
            showPlanModal: false,
            planQuestion: null,
            planNote: '',
            graphFilter: { subject_id: null },
            graphSubject: null,
            graphNodes: [],
            graphChartMode: 'layered',
            graphMobileParent: null,
            graphMobilePath: [],
            reportFilter: { subject_id: null },
            reportData: null,
            trendData: [],
            priorityData: [],
            graphDetail: {
                show: false, kp: null, path: '', materials: [], aiContent: '', aiLoading: false,
                resources: [],
                resourceForm: { type: 'textbook', title: '', url: '', page: '', content: '', attachment: '' },
                tab: 'overview',
                aiResources: [],
                aiResourcesLoading: false
            },
            newSubject: '',
            kpForm: { subject_id: null, parent_id: null, name: '' },
            settingsKpHint: '',
            dirExpanded: {},
            kpSearch: '',
            lastAddedKpId: null,
            showLlmModal: false,
            showAccountModal: false,
            showResetModal: false,
            accountForm: {
                new_username: '',
                rename_password: '',
                old_password: '',
                new_password: '',
                confirm_password: '',
                delete_password: ''
            },
            resetForm: { username: '', new_password: '', confirm_password: '' },
            showKpSelector: false,
            selectedKps: [],
            detailQuestion: null,
            recommending: false,
            showEditModal: false,
            importLoading: false,
            importMessage: '',
            importPreview: [],
            aiLoading: false,
            aiModal: { show: false, kp: null, mode: 'concept', content: '', title: '' },
            typicalModal: { show: false, kp: null, mode: 'typical', ownExamples: [], questions: [], aiContent: '', view: 'own', openAnswer: '' },
            typicalLoading: false,
            typicalAiLoading: false,
            traceModal: { show: false, loading: false, saving: false, data: null },
            mindMapModal: { show: false, map: null, question: null, newLabel: '', newType: 'direct' },
            kpDetail: { show: false, kp: null, path: '', materials: [] },
            cameraActive: false,
            cameraError: '',
            cameraStream: null
        };
    },
    computed: {
        unmasteredCount() {
            return this.questions.filter(q => q.status === 0).length;
        },
        recentQuestions() {
            return this.questions.slice(0, 5);
        },
        filteredQuestions() {
            let list = this.questions;
            if (this.filter.keyword) {
                list = list.filter(q => (q.title_text || '').includes(this.filter.keyword));
            }
            return list;
        },
        filterKps() {
            if (!this.filter.subject_id) return [];
            return this.knowledgePoints.filter(k => k.subject_id === this.filter.subject_id);
        },
        currentWeakSubjectName() {
            const s = this.subjects.find(s => s.id === this.weakFilter.subject_id);
            return s ? s.name : '';
        },
        subjectKnowledgePoints() {
            return this.knowledgePoints.filter(k => k.subject_id === this.kpForm.subject_id);
        },
        selectedDirSubjectName() {
            const s = this.subjects.find(s => s.id === this.kpForm.subject_id);
            return s ? s.name : '';
        },
        kpRows() {
            const search = (this.kpSearch || '').trim().toLowerCase();
            const byId = {};
            const childrenOf = {};
            this.knowledgePoints.forEach(k => {
                byId[k.id] = k;
                if (!childrenOf[k.id]) childrenOf[k.id] = [];
            });
            this.knowledgePoints.forEach(k => {
                const p = k.parent_id && byId[k.parent_id] ? k.parent_id : k.subject_id;
                if (!childrenOf[p]) childrenOf[p] = [];
                childrenOf[p].push(k);
            });
            const searchRelated = new Set();
            let matched = new Set();
            if (search) {
                this.knowledgePoints.forEach(k => {
                    if ((k.name || '').toLowerCase().includes(search)) {
                        let cur = k;
                        matched.add(k.id);
                        while (cur) {
                            searchRelated.add(cur.id);
                            searchRelated.add('s' + cur.subject_id);
                            cur = cur.parent_id && byId[cur.parent_id] ? byId[cur.parent_id] : null;
                        }
                    }
                });
            }
            const rows = [];
            const directChildren = id => (childrenOf[id] || []).sort((a, b) => a.name.localeCompare(b.name));
            const pushKp = (k, depth, open) => {
                const kids = directChildren(k.id);
                const isMatch = search && (k.name || '').toLowerCase().includes(search);
                const hasRelated = search ? (searchRelated.has(k.id)) : false;
                rows.push({
                    key: 'k' + k.id,
                    isSubject: false,
                    name: k.name,
                    node: k,
                    depth,
                    expanded: !search && !!this.dirExpanded[k.id],
                    count: kids.length,
                    highlight: !!isMatch,
                    flash: this.lastAddedKpId === k.id
                });
                const showKids = search ? hasRelated && kids.some(c => searchRelated.has(c.id)) : !!this.dirExpanded[k.id];
                if (showKids) {
                    const pool = search ? kids.filter(c => searchRelated.has(c.id)) : kids;
                    pool.forEach(c => pushKp(c, depth + 1, !!this.dirExpanded[c.id]));
                }
            };
            this.subjects.forEach(s => {
                const kids = directChildren(s.id);
                rows.push({
                    key: 's' + s.id,
                    isSubject: true,
                    name: s.name,
                    node: s,
                    depth: 0,
                    expanded: search ? kids.some(k => searchRelated.has(k.id)) : !!this.dirExpanded['s' + s.id],
                    count: kids.length,
                    highlight: false
                });
                const hasSubjectHit = search && kids.some(k => searchRelated.has(k.id));
                const openKids = search ? hasSubjectHit : !!this.dirExpanded['s' + s.id];
                if (openKids) {
                    const pool = search ? kids.filter(k => searchRelated.has(k.id)) : kids;
                    pool.forEach(k => pushKp(k, 1, !!this.dirExpanded[k.id]));
                }
            });
            return rows;
        },
        graphLevels() {
            const levels = [];
            this.graphNodes.forEach(n => {
                const i = n.level;
                if (!levels[i]) levels[i] = [];
                levels[i].push(n);
            });
            return levels.map((nodes, level) => ({ level, nodes })).filter(item => item.nodes && item.nodes.length);
        },
        graphMobileChildren() {
            const parent = this.graphMobileParent;
            if (parent === null) {
                return this.graphNodes.filter(n => !n.parent_id);
            }
            return this.graphNodes.filter(n => n.parent_id === parent);
        },
        reviewPlanGroups() {
            const today = new Date().toISOString().slice(0, 10);
            const pending = this.reviewPlans.filter(p => p.status === 'pending');
            return {
                overdue: pending.filter(p => p.plan_date < today),
                today: pending.filter(p => p.plan_date === today),
                upcoming: pending.filter(p => p.plan_date > today),
                finished: this.reviewPlans.filter(p => p.status !== 'pending')
            };
        }
    },
    watch: {
        currentNav(value) {
            this.$nextTick(() => {
                if (value === 'weak') this.renderTrendChart();
                if (value === 'graph') this.renderGraphChart();
                if (value === 'report') this.renderReportCharts();
            });
        }
    },
    mounted() {
        this.bootstrap();
    },
    methods: {
        async bootstrap() {
            this.loading = true;
            this.authUser = null;
            try {
                const res = await axios.get('/api/auth/me');
                if (res.data.user) {
                    this.authUser = res.data.user;
                    await this.init();
                }
            } catch (e) {
                // 未登录或会话失效，留在登录页
                this.authUser = null;
            } finally {
                this.loading = false;
            }
        },
        toggleAuthMode() {
            this.authMode = this.authMode === 'login' ? 'register' : 'login';
            this.authError = '';
            this.authConfirm = '';
        },
        async submitAuth() {
            this.authError = '';
            const username = this.authUsername.trim();
            const password = this.authPassword;
            if (!/^[A-Za-z0-9]{3,20}$/.test(username)) {
                this.authError = '账号只能是 3-20 位英文字母或数字';
                return;
            }
            if (!/^[A-Za-z0-9]{6,20}$/.test(password)) {
                this.authError = '密码只能是 6-20 位英文字母或数字';
                return;
            }
            if (this.authMode === 'register' && password !== this.authConfirm) {
                this.authError = '两次输入的密码不一致';
                return;
            }
            this.authLoading = true;
            try {
                const url = this.authMode === 'login' ? '/api/auth/login' : '/api/auth/register';
                const res = await axios.post(url, { username, password });
                this.authUser = res.data.user;
                this.authUsername = '';
                this.authPassword = '';
                this.authConfirm = '';
                this.authMode = 'login';
                this.currentNav = 'dashboard';
                await this.init();
            } catch (e) {
                this.authError = (e.response && e.response.data && e.response.data.error) || '登录失败，请稍后重试';
            } finally {
                this.authLoading = false;
            }
        },
        async switchUser() {
            this.mobileMenuOpen = false;
            try {
                await axios.post('/api/auth/logout');
            } catch (e) {
                // 忽略退出失败，前端仍回到登录页
            }
            this.authUser = null;
            this.authMode = 'login';
            this.authError = '';
            this.authUsername = '';
            this.authPassword = '';
            this.authConfirm = '';
        },
        openAccountModal() {
            this.mobileMenuOpen = false;
            this.accountForm = {
                new_username: '',
                rename_password: '',
                old_password: '',
                new_password: '',
                confirm_password: '',
                delete_password: ''
            };
            this.showAccountModal = true;
        },
        async renameAccount() {
            if (!this.accountForm.new_username || !this.accountForm.rename_password) {
                alert('请输入新账号和当前密码');
                return;
            }
            if (!confirm('确认修改账号名称？')) return;
            try {
                const res = await axios.post('/api/auth/rename', {
                    new_username: this.accountForm.new_username,
                    password: this.accountForm.rename_password
                });
                this.authUser.username = res.data.username;
                this.accountForm.new_username = '';
                this.accountForm.rename_password = '';
                alert('账号已修改');
            } catch (e) {
                alert((e.response && e.response.data && e.response.data.error) || '修改失败');
            }
        },
        async changePassword() {
            if (this.accountForm.new_password !== this.accountForm.confirm_password) {
                alert('两次输入的新密码不一致');
                return;
            }
            if (!confirm('确认修改密码？')) return;
            try {
                await axios.post('/api/auth/change_password', {
                    old_password: this.accountForm.old_password,
                    new_password: this.accountForm.new_password
                });
                this.accountForm.old_password = '';
                this.accountForm.new_password = '';
                this.accountForm.confirm_password = '';
                alert('密码已修改');
            } catch (e) {
                alert((e.response && e.response.data && e.response.data.error) || '修改失败');
            }
        },
        async deleteAccount() {
            if (!confirm('删除账号会清空所有错题、知识树和学习记录，且无法恢复，确定继续？')) return;
            try {
                await axios.delete('/api/auth/account', { data: { password: this.accountForm.delete_password } });
                this.showAccountModal = false;
                this.authUser = null;
                alert('账号已删除');
            } catch (e) {
                alert((e.response && e.response.data && e.response.data.error) || '删除失败');
            }
        },
        async importBackup(event, kind) {
            const file = event.target.files && event.target.files[0];
            event.target.value = '';
            if (!file) return;
            if (!confirm('导入会把备份数据合并到当前账号，确定继续？')) return;
            const fd = new FormData();
            fd.append('file', file);
            try {
                const res = await axios.post(`/api/backup/import/${kind}`, fd);
                const s = res.data.stats || {};
                alert(`导入完成：学科 ${s.subjects || 0}，知识点 ${s.knowledge_points || 0}，错题 ${s.questions || 0}`);
                await this.loadSubjects();
                await this.loadKnowledgePoints();
                await this.loadQuestions();
                await this.loadWeak();
                await this.loadGraph();
            } catch (e) {
                alert((e.response && e.response.data && e.response.data.error) || '导入失败');
            }
        },
        async importBackupPackage(event) {
            const file = event.target.files && event.target.files[0];
            event.target.value = '';
            if (!file) return;
            if (!confirm('导入会把数据包内容合并到当前账号，确定继续？')) return;
            const fd = new FormData();
            fd.append('file', file);
            try {
                const res = await axios.post('/api/backup/import', fd);
                const s = res.data.stats || {};
                alert(`导入完成：学科 ${s.subjects || 0}，知识点 ${s.knowledge_points || 0}，错题 ${s.questions || 0}`);
                await this.loadSubjects();
                await this.loadKnowledgePoints();
                await this.loadQuestions();
                await this.loadWeak();
                await this.loadGraph();
                await this.loadReport();
            } catch (e) {
                alert((e.response && e.response.data && e.response.data.error) || '导入失败');
            }
        },
        openResetModal() {
            this.resetForm = { username: '', new_password: '', confirm_password: '' };
            this.showResetModal = true;
        },
        async resetPassword() {
            if (this.resetForm.new_password !== this.resetForm.confirm_password) {
                alert('两次输入的密码不一致');
                return;
            }
            try {
                await axios.post('/api/auth/reset_password', {
                    username: this.resetForm.username,
                    new_password: this.resetForm.new_password
                });
                this.showResetModal = false;
                alert('密码已重置，请使用新密码登录');
            } catch (e) {
                alert((e.response && e.response.data && e.response.data.error) || '重置失败');
            }
        },
        emptyForm() {
            return emptyForm();
        },
        goTo(key) {
            this.mobileMenuOpen = false;
            if (key === 'trash') {
                this.currentNav = 'library';
                this.openTrash();
                return;
            }
            if (key === 'library') {
                this.trashMode = false;
            }
            this.currentNav = key;
        },
        isNavActive(nav) {
            if (nav.key === 'trash') return this.currentNav === 'library' && this.trashMode;
            if (nav.key === 'library') return this.currentNav === 'library' && !this.trashMode;
            return this.currentNav === nav.key;
        },
        async init() {
            this.loading = true;
            this.error = '';
            try {
                await this.loadSubjects();
                if (this.subjects.length && !this.form.subject_id) {
                    this.form.subject_id = this.subjects[0].id;
                    this.kpForm.subject_id = this.subjects[0].id;
                    this.weakFilter.subject_id = this.subjects[0].id;
                    this.reviewFilter.subject_id = this.subjects[0].id;
                    this.graphFilter.subject_id = this.subjects[0].id;
                    this.reportFilter.subject_id = this.subjects[0].id;
                }
                await this.loadKnowledgePoints();
                await this.loadQuestions();
                await this.loadWeak();
                await this.loadReview();
                await this.loadReviewPlans();
                await this.loadGraph();
                await this.loadReport();
                await this.loadSettings();
                this.$nextTick(() => this.renderMath());
            } catch (e) {
                this.error = '数据加载失败：' + (e.message || e);
                console.error(e);
            } finally {
                this.loading = false;
            }
        },
        async loadSubjects() {
            const res = await axios.get('/api/subjects');
            this.subjects = res.data;
        },
        async loadKnowledgePoints() {
            const res = await axios.get('/api/knowledge_points');
            this.knowledgePoints = res.data;
        },
        async loadQuestions() {
            const params = {};
            if (this.filter.subject_id) params.subject_id = this.filter.subject_id;
            if (this.filter.status !== null) params.status = this.filter.status;
            if (this.filter.kp_id) params.kp_id = this.filter.kp_id;
            const res = await axios.get('/api/questions', { params });
            this.questions = res.data;
            this.selectedQuestionIds = [];
            this.$nextTick(() => this.renderMath());
        },
        async loadWeak() {
            const sid = this.weakFilter.subject_id;
            this.weakPoints = [];
            this.kpTree = [];
            this.weakAddHint = '';
            if (!sid) return;
            const [weakRes, treeRes, trendRes, priorityRes] = await Promise.all([
                axios.get('/api/weak_points', { params: { subject_id: sid, top_n: 20 } }),
                axios.get('/api/kp_tree', { params: { subject_id: sid } }),
                axios.get('/api/analytics/trend', { params: { subject_id: sid, days: 30 } }),
                axios.get('/api/analytics/priority', { params: { subject_id: sid } })
            ]);
            this.weakPoints = weakRes.data;
            this.kpTree = treeRes.data;
            this.trendData = trendRes.data || [];
            this.priorityData = priorityRes.data || [];
            this.$nextTick(() => this.renderTrendChart());
        },
        async loadReview(keepView = false) {
            const sid = this.reviewFilter.subject_id;
            this.reviewLoading = true;
            if (!keepView) {
                this.reviewQuestions = [];
                this.reviewSelectedKp = null;
                this.reviewSelectedQuestion = null;
                this.reviewAiContent = '';
                this.reviewView = 'home';
            }
            try {
                const res = await axios.get('/api/review/today', { params: sid ? { subject_id: sid } : {} });
                this.reviewAdvice = res.data.advice || '';
                this.reviewKps = res.data.knowledge_points || [];
                this.reviewRecommendations = res.data.recommendations || [];
            } finally {
                this.reviewLoading = false;
            }
        },
        async loadReviewPlans() {
            const res = await axios.get('/api/review/plans');
            this.reviewPlans = res.data.plans || [];
            this.reviewPlanCounts = res.data.counts || { today: 0, overdue: 0, total: 0 };
        },
        async generateTodayPlans() {
            if (!confirm('根据当前薄弱知识点自动生成今日复习计划？')) return;
            const res = await axios.post('/api/review/plans/generate', {
                subject_id: this.reviewFilter.subject_id,
                limit: 10
            });
            await this.loadReviewPlans();
            alert(`已生成 ${res.data.created} 条复习计划`);
        },
        openPlanModal(q) {
            this.planQuestion = q;
            this.planDate = new Date().toISOString().slice(0, 10);
            this.planNote = '';
            this.showPlanModal = true;
        },
        async savePlanForQuestion() {
            if (!this.planQuestion || !this.planDate) return;
            if (!confirm(`确认把这道题安排到 ${this.planDate} 复习？`)) return;
            await axios.post('/api/review/plans', {
                question_id: this.planQuestion.id,
                plan_date: this.planDate,
                note: this.planNote
            });
            this.showPlanModal = false;
            await this.loadReviewPlans();
            alert('已加入复习计划');
        },
        async completePlan(plan, result) {
            const label = result === 1 ? '已完成' : '已跳过';
            if (!confirm(`确认把这条计划标记为「${label}」？`)) return;
            await axios.post(`/api/review/plans/${plan.id}/complete`, { result });
            await this.loadReviewPlans();
            await this.loadReview();
            await this.loadQuestions();
        },
        async startPlan(plan) {
            const res = await axios.get(`/api/questions/${plan.question_id}`);
            this.openReviewQuestion(res.data);
        },
        async deletePlan(plan) {
            if (!confirm('确定删除这条复习计划？')) return;
            await axios.delete(`/api/review/plans/${plan.id}`);
            await this.loadReviewPlans();
        },
        async loadGraph() {
            const sid = this.graphFilter.subject_id;
            this.graphNodes = [];
            this.graphSubject = null;
            if (!sid) return;
            const res = await axios.get('/api/knowledge_graph', { params: { subject_id: sid } });
            this.graphSubject = res.data.subject || null;
            this.graphNodes = res.data.nodes || [];
            this.graphMobileParent = null;
            this.graphMobilePath = [];
            this.$nextTick(() => this.renderGraphChart());
        },
        async loadReport() {
            const sid = this.reportFilter.subject_id;
            const res = await axios.get('/api/reports/summary', { params: sid ? { subject_id: sid } : {} });
            this.reportData = res.data;
            this.$nextTick(() => this.renderReportCharts());
        },
        renderReportCharts() {
            if (!window.echarts || !this.reportData) return;
            const statusEl = this.$refs.reportStatusChart;
            const weakEl = this.$refs.reportWeakChart;
            if (statusEl) {
                if (this._reportStatusChart) this._reportStatusChart.dispose();
                this._reportStatusChart = window.echarts.init(statusEl);
                const sc = this.reportData.totals.status_counts || {};
                this._reportStatusChart.setOption({
                    tooltip: { trigger: 'item' },
                    legend: { bottom: 0 },
                    series: [{
                        type: 'pie',
                        radius: ['42%', '70%'],
                        data: [
                            { name: '未掌握', value: sc[0] || 0, itemStyle: { color: '#ef4444' } },
                            { name: '已掌握', value: sc[1] || 0, itemStyle: { color: '#10b981' } },
                            { name: '已复习', value: sc[2] || 0, itemStyle: { color: '#f59e0b' } },
                            { name: '已归档', value: sc[3] || 0, itemStyle: { color: '#94a3b8' } }
                        ]
                    }]
                });
            }
            if (weakEl) {
                if (this._reportWeakChart) this._reportWeakChart.dispose();
                this._reportWeakChart = window.echarts.init(weakEl);
                const items = (this.reportData.weak_points || []).slice().reverse();
                this._reportWeakChart.setOption({
                    tooltip: { trigger: 'axis' },
                    grid: { left: 90, right: 20, top: 20, bottom: 30 },
                    xAxis: { type: 'value', max: 10 },
                    yAxis: { type: 'category', data: items.map(x => x.name) },
                    series: [{
                        type: 'bar',
                        data: items.map(x => x.weak_index),
                        itemStyle: { color: '#2563eb', borderRadius: [0, 4, 4, 0] }
                    }]
                });
            }
        },
        renderTrendChart() {
            if (!window.echarts) return;
            const el = this.$refs.trendChartEl;
            if (!el) return;
            if (this.trendChart) {
                this.trendChart.dispose();
                this.trendChart = null;
            }
            this.trendChart = window.echarts.init(el);
            const dates = this.trendData.map(d => d.date.slice(5));
            this.trendChart.setOption({
                tooltip: { trigger: 'axis' },
                legend: { data: ['新增错题', '复习仍错'], bottom: 0 },
                grid: { left: 40, right: 20, top: 30, bottom: 45 },
                xAxis: { type: 'category', data: dates, boundaryGap: false },
                yAxis: { type: 'value', minInterval: 1 },
                series: [
                    {
                        name: '新增错题',
                        type: 'line',
                        smooth: true,
                        data: this.trendData.map(d => d.added),
                        itemStyle: { color: '#2563eb' },
                        areaStyle: { color: 'rgba(37,99,235,0.12)' }
                    },
                    {
                        name: '复习仍错',
                        type: 'line',
                        smooth: true,
                        data: this.trendData.map(d => d.wrong_reviews),
                        itemStyle: { color: '#dc2626' },
                        areaStyle: { color: 'rgba(220,38,38,0.10)' }
                    }
                ]
            });
        },
        buildGraphTree() {
            const byId = {};
            this.graphNodes.forEach(n => { byId[n.id] = { name: n.name, value: n.question_count || 0, children: [] }; });
            const roots = [];
            this.graphNodes.forEach(n => {
                const item = byId[n.id];
                if (n.parent_id && byId[n.parent_id]) {
                    byId[n.parent_id].children.push(item);
                } else {
                    roots.push(item);
                }
            });
            const clean = node => {
                if (!node.children.length) delete node.children;
                else node.children.forEach(clean);
                return node;
            };
            roots.forEach(clean);
            return { name: this.graphSubject ? this.graphSubject.name : '学科', children: roots };
        },
        renderGraphChart() {
            if (!window.echarts || this.graphChartMode === 'layered') return;
            const el = this.$refs.graphChartEl;
            if (!el || !this.graphSubject) return;
            if (this.graphChart) {
                this.graphChart.dispose();
                this.graphChart = null;
            }
            this.graphChart = window.echarts.init(el);
            const data = this.buildGraphTree();
            if (this.graphChartMode === 'tree') {
                this.graphChart.setOption({
                    tooltip: { trigger: 'item' },
                    series: [{
                        type: 'tree',
                        data: [data],
                        layout: 'orthogonal',
                        orient: 'LR',
                        symbolSize: 12,
                        edgeShape: 'curve',
                        label: { position: 'left', align: 'right', fontSize: 13 },
                        leaves: { label: { position: 'right', align: 'left' } },
                        lineStyle: { color: '#93c5fd', width: 2 },
                        emphasis: { focus: 'descendant' }
                    }]
                });
            } else {
                this.graphChart.setOption({
                    tooltip: { trigger: 'item' },
                    series: [{
                        type: 'sunburst',
                        data: data.children || [],
                        radius: [20, '90%'],
                        label: { rotate: 'radial', fontSize: 12 },
                        itemStyle: { borderColor: '#fff', borderWidth: 2 },
                        levels: [
                            {},
                            { r0: '20%', r: '45%', label: { rotate: 'tangential' } },
                            { r0: '45%', r: '70%' },
                            { r0: '70%', r: '90%', label: { position: 'outside' } }
                        ]
                    }]
                });
            }
        },
        switchGraphMode(mode) {
            this.graphChartMode = mode;
            this.$nextTick(() => this.renderGraphChart());
        },
        openGraphMobileNode(node) {
            const children = this.graphNodes.filter(n => n.parent_id === node.id);
            if (children.length) {
                this.graphMobilePath.push(node);
                this.graphMobileParent = node.id;
            } else {
                this.openGraphNode(node);
            }
        },
        backGraphMobile() {
            const last = this.graphMobilePath.pop();
            this.graphMobileParent = last && last.parent_id ? last.parent_id : null;
        },
        async openGraphNode(kp) {
            const byId = {};
            this.graphNodes.forEach(k => { byId[k.id] = k; });
            const names = [kp.name];
            let cur = kp.parent_id && byId[kp.parent_id] ? byId[kp.parent_id] : null;
            while (cur) {
                names.unshift(cur.name);
                cur = cur.parent_id && byId[cur.parent_id] ? byId[cur.parent_id] : null;
            }
            if (this.graphSubject) names.unshift(this.graphSubject.name);
            this.graphDetail = {
                show: true,
                kp,
                path: names.join(' > '),
                description: kp.description || '',
                materials: [],
                aiContent: '',
                aiLoading: false,
                newType: 'custom',
                newContent: '',
                resources: [],
                resourceForm: { type: 'textbook', title: '', url: '', page: '', content: '', attachment: '' },
                tab: 'overview',
                aiResources: [],
                aiResourcesLoading: false
            };
            try {
                const res = await axios.get('/api/ai/materials', { params: { kp_id: kp.id } });
                this.graphDetail.materials = res.data || [];
                const rr = await axios.get(`/api/knowledge_points/${kp.id}/resources`);
                this.graphDetail.resources = rr.data || [];
            } catch (e) {
                this.graphDetail.materials = [];
            }
        },
        async generateGraphSummary() {
            if (!this.ensureApiKey()) return;
            this.graphDetail.aiLoading = true;
            try {
                const res = await axios.post('/api/ai/generate', {
                    kp_id: this.graphDetail.kp.id,
                    mode: 'summary'
                });
                this.graphDetail.aiContent = this.humanizeMath(res.data.content || '');
            } catch (err) {
                alert((err.response && err.response.data && err.response.data.error) || '生成失败');
            } finally {
                this.graphDetail.aiLoading = false;
            }
        },
        async saveGraphDescription() {
            if (!confirm('确认保存知识点说明？')) return;
            await axios.post(`/api/knowledge_points/${this.graphDetail.kp.id}/description`, {
                description: this.graphDetail.description
            });
            this.graphDetail.kp.description = this.graphDetail.description;
            await this.loadKnowledgePoints();
            await this.loadGraph();
            alert('知识点说明已保存');
        },
        async saveMaterialEdit(m) {
            if (!confirm('确认保存这份知识库内容的修改？')) return;
            await axios.post(`/api/ai/materials/${m.id}`, { content: m.content });
            alert('已保存修改');
        },
        async createMaterial(containerKey) {
            const c = this[containerKey];
            const content = (c.newContent || '').trim();
            if (!content) {
                alert('请输入内容');
                return;
            }
            if (!confirm('确认新增这条知识库内容？')) return;
            await axios.post('/api/ai/materials', {
                kp_id: c.kp.id,
                mode: c.newType,
                content
            });
            c.newContent = '';
            await this.reloadMaterials(containerKey);
        },
        async deleteMaterial(m, containerKey) {
            if (!confirm('确定删除这条知识库内容？')) return;
            await axios.delete(`/api/ai/materials/${m.id}`);
            await this.reloadMaterials(containerKey);
        },
        async reloadMaterials(containerKey) {
            const c = this[containerKey];
            const res = await axios.get('/api/ai/materials', { params: { kp_id: c.kp.id } });
            c.materials = res.data || [];
        },
        async saveGraphSummary() {
            if (!this.graphDetail.aiContent.trim()) return;
            if (!confirm('确认把这份知识点精要保存到知识库？')) return;
            await axios.post('/api/ai/save', {
                kp_id: this.graphDetail.kp.id,
                mode: 'summary',
                content: this.graphDetail.aiContent
            });
            const res = await axios.get('/api/ai/materials', { params: { kp_id: this.graphDetail.kp.id } });
            this.graphDetail.materials = res.data || [];
            alert('已保存');
        },
        async applyGraphSummaryAsDescription() {
            if (!this.graphDetail.aiContent.trim()) return;
            if (!confirm('确认把这份 AI 精要设为该知识点的详细说明？')) return;
            await axios.post(`/api/knowledge_points/${this.graphDetail.kp.id}/description`, {
                description: this.graphDetail.aiContent
            });
            this.graphDetail.kp.description = this.graphDetail.aiContent;
            await this.loadKnowledgePoints();
            await this.loadGraph();
            alert('已更新知识点说明');
        },
        async saveResource(resource = null) {
            const payload = resource || this.graphDetail.resourceForm;
            if (!payload.title && !payload.url && !payload.content && !payload.page) {
                alert('请至少填写标题、页码、链接或笔记内容');
                return;
            }
            if (!confirm('确认保存这条学习资源？')) return;
            if (resource && resource.id) {
                await axios.post(`/api/resources/${resource.id}`, payload);
            } else {
                await axios.post(`/api/knowledge_points/${this.graphDetail.kp.id}/resources`, payload);
                this.graphDetail.resourceForm = { type: 'textbook', title: '', url: '', page: '', content: '', attachment: '' };
            }
            const res = await axios.get(`/api/knowledge_points/${this.graphDetail.kp.id}/resources`);
            this.graphDetail.resources = res.data || [];
            alert('学习资源已保存');
        },
        async deleteResource(resource) {
            if (!confirm('确定删除这条学习资源？')) return;
            await axios.delete(`/api/resources/${resource.id}`);
            const res = await axios.get(`/api/knowledge_points/${this.graphDetail.kp.id}/resources`);
            this.graphDetail.resources = res.data || [];
        },
        async uploadResourceAttachment(event) {
            const file = event.target.files && event.target.files[0];
            event.target.value = '';
            if (!file) return;
            const fd = new FormData();
            fd.append('file', file);
            const res = await axios.post('/api/upload_attachment', fd);
            this.graphDetail.resourceForm.attachment = res.data.url;
            alert('附件已上传');
        },
        async generateAiResources() {
            if (!this.ensureApiKey()) return;
            this.graphDetail.aiResourcesLoading = true;
            try {
                const res = await axios.post('/api/ai/generate', {
                    kp_id: this.graphDetail.kp.id,
                    mode: 'resources'
                });
                this.graphDetail.aiResources = res.data.resources || [];
            } catch (err) {
                alert((err.response && err.response.data && err.response.data.error) || '推荐失败');
            } finally {
                this.graphDetail.aiResourcesLoading = false;
            }
        },
        async saveAiResource(item) {
            if (!confirm('确认把这条 AI 推荐保存到学习资源？')) return;
            await axios.post(`/api/knowledge_points/${this.graphDetail.kp.id}/resources`, {
                type: item.type === 'course' ? 'course' : 'note',
                title: item.title || '',
                url: item.url || '',
                content: item.content || ''
            });
            const res = await axios.get(`/api/knowledge_points/${this.graphDetail.kp.id}/resources`);
            this.graphDetail.resources = res.data || [];
            alert('已保存到学习资源');
        },
        async selectReviewKp(kp) {
            this.reviewSelectedKp = kp;
            const res = await axios.get('/api/questions', { params: { kp_id: kp.id } });
            this.reviewQuestions = res.data;
            this.reviewSelectedQuestion = null;
            this.reviewAiContent = '';
            this.reviewShowAnswer = false;
            this.reviewView = 'questions';
            this.$nextTick(() => this.renderMath());
        },
        backToReviewHome() {
            this.reviewView = 'home';
            this.reviewSelectedQuestion = null;
            this.reviewAiContent = '';
            this.reviewShowAnswer = false;
        },
        backToReviewQuestions() {
            this.reviewView = 'questions';
            this.reviewSelectedQuestion = null;
            this.reviewAiContent = '';
            this.reviewShowAnswer = false;
        },
        openReviewQuestion(q) {
            this.reviewSelectedQuestion = q;
            this.reviewAiContent = '';
            this.reviewShowAnswer = false;
            this.reviewView = 'detail';
            this.$nextTick(() => this.renderMath());
        },
        async explainReviewQuestion() {
            if (!this.reviewSelectedQuestion) return;
            if (!this.ensureApiKey()) return;
            this.reviewAiLoading = true;
            try {
                const res = await axios.post('/api/ai/generate', {
                    mode: 'explain',
                    question_id: this.reviewSelectedQuestion.id
                });
                this.reviewAiContent = this.humanizeMath(res.data.content || '');
            } catch (err) {
                alert((err.response && err.response.data && err.response.data.error) || 'AI 解答失败');
            } finally {
                this.reviewAiLoading = false;
            }
        },
        async markReview(q, result) {
            const label = result === 1 ? '已掌握' : '仍需加强';
            if (!confirm(`确认将这道题标记为「${label}」？`)) return;
            await axios.post(`/api/questions/${q.id}/review`, { result });
            const res = await axios.get('/api/questions', { params: { kp_id: this.reviewSelectedKp.id } });
            this.reviewQuestions = res.data;
            const fresh = this.reviewQuestions.find(item => item.id === q.id);
            if (fresh) this.reviewSelectedQuestion = fresh;
            const keepKp = this.reviewSelectedKp;
            await this.loadReview(true);
            this.reviewSelectedKp = this.reviewKps.find(kp => kp.id === keepKp.id) || keepKp;
            this.reviewView = 'detail';
            await this.loadQuestions();
        },
        startChildKp(kp) {
            this.weakParentId = kp.id;
            this.weakAddHint = kp.name;
            this.$nextTick(() => {
                const input = this.$refs.weakKpInput;
                if (input) input.focus();
            });
        },
        async addWeakKp() {
            const name = (this.weakKpName || '').trim();
            const sid = this.weakFilter.subject_id;
            if (!name) {
                alert('请输入知识点名称');
                return;
            }
            if (!sid) {
                alert('请先选择学科');
                return;
            }
            const parent = this.kpTree.find(k => k.id === this.weakParentId);
            await axios.post('/api/knowledge_points', {
                subject_id: sid,
                name: name,
                parent_id: this.weakParentId || null,
                level: parent ? parent.level + 1 : 0
            });
            this.weakKpName = '';
            this.weakParentId = null;
            this.weakAddHint = '';
            await this.loadWeak();
        },
        async deleteWeakKp(kp) {
            if (!confirm(`确定删除知识点「${kp.name}」？其下子知识点会一并删除。`)) return;
            await axios.delete(`/api/knowledge_points/${kp.id}`);
            if (this.weakParentId === kp.id) {
                this.weakParentId = null;
                this.weakAddHint = '';
            }
            await this.loadWeak();
        },
        async loadSettings() {
            const res = await axios.get('/api/settings');
            this.settings = res.data;
        },
        statusText(s) {
            return ['未掌握', '已掌握', '已复习', '已归档'][s] || '未知';
        },
        heatColor(v) {
            if (v >= 7) return '#dc2626';
            if (v >= 4) return '#f59e0b';
            return '#10b981';
        },
        async openCamera() {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.cameraError = '当前浏览器不支持摄像头，已改为打开系统拍摄';
                this.$nextTick(() => {
                    this.$refs.captureInput && this.$refs.captureInput.click();
                });
                return;
            }
            this.cameraError = '';
            this.cameraActive = true;
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 960 } },
                    audio: false
                });
                this.cameraStream = stream;
                await this.$nextTick();
                const video = this.$refs.cameraVideo;
                if (video) {
                    video.srcObject = stream;
                    await video.play().catch(() => {});
                }
            } catch (err) {
                this.cameraActive = false;
                this.cameraError = '无法打开摄像头：' + (err.message || err);
                this.$refs.captureInput && this.$refs.captureInput.click();
            }
        },
        closeCamera() {
            if (this.cameraStream) {
                this.cameraStream.getTracks().forEach(t => t.stop());
            }
            this.cameraStream = null;
            this.cameraActive = false;
            this.cameraError = '';
        },
        takePhoto() {
            const video = this.$refs.cameraVideo;
            if (!video || !video.videoWidth) return;
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            canvas.toBlob(blob => {
                if (!blob) return;
                const file = new File([blob], 'camera_' + Date.now() + '.jpg', { type: 'image/jpeg' });
                this.closeCamera();
                this.processImageFile(file);
            }, 'image/jpeg', 0.9);
        },
        handleImageUpload(e) {
            this.processImageFile(e.target.files[0]);
            e.target.value = '';
        },
        async processImageFile(file) {
            if (!file) return;
            const fd = new FormData();
            fd.append('file', file);
            this.form.ocrLoading = true;
            try {
                // 同时进行 OCR 识别和上传
                const ocrRes = await axios.post('/api/ocr', fd);
                if (ocrRes.data.text) {
                    this.form.title_text = (this.form.title_text ? this.form.title_text + '\n' : '') + ocrRes.data.text;
                }
                this.form.title_image = ocrRes.data.url;
            } catch (err) {
                // OCR 失败时只上传图片
                const fd2 = new FormData();
                fd2.append('file', file);
                const res = await axios.post('/api/upload_image', fd2);
                this.form.title_image = res.data.url;
                console.warn('OCR 识别失败', err);
            } finally {
                this.form.ocrLoading = false;
            }
        },
        async handleImportFile(e) {
            const file = e.target.files && e.target.files[0];
            e.target.value = '';
            if (!file) return;
            this.importLoading = true;
            this.importMessage = '';
            try {
                const fd = new FormData();
                fd.append('file', file);
                const res = await axios.post('/api/import/document', fd);
                this.importPreview = (res.data.questions || []).map(q => ({ ...q, checked: true }));
                this.importMessage = `${res.data.filename} · ${res.data.mode} · 共解析出 ${res.data.count} 道题`;
            } catch (err) {
                alert((err.response && err.response.data && err.response.data.error) || '文件解析失败');
            } finally {
                this.importLoading = false;
            }
        },
        cancelImport() {
            this.importPreview = [];
            this.importMessage = '';
        },
        async saveImportedQuestions() {
            const selected = this.importPreview.filter(q => q.checked && (q.title_text || '').trim());
            if (!selected.length) {
                alert('请至少勾选一道题');
                return;
            }
            if (!this.form.subject_id) {
                alert('请先在错题录入页选择学科');
                return;
            }
            const subject = this.subjects.find(s => s.id === this.form.subject_id);
            if (!confirm(`确认将 ${selected.length} 道题导入「${subject ? subject.name : ''}」？`)) return;
            try {
                const res = await axios.post('/api/import/save', {
                    subject_id: this.form.subject_id,
                    questions: selected.map(q => ({ title_text: q.title_text }))
                });
                alert(`成功导入 ${res.data.saved} 道题`);
                this.cancelImport();
                await this.loadQuestions();
                await this.loadWeak();
                this.currentNav = 'library';
            } catch (err) {
                alert((err.response && err.response.data && err.response.data.error) || '导入失败');
            }
        },
        async openAiMaterial(kp, mode) {
            if (!this.ensureApiKey()) return;
            this.aiModal = {
                show: true,
                kp,
                mode,
                content: '',
                title: `${kp.name} · ${mode === 'concept' ? '概念回顾' : '变式练习'}`
            };
            await this.generateAiMaterial();
        },
        async openTypicalExamples(kp, mode = 'typical') {
            this.typicalModal = { show: true, kp, mode, ownExamples: [], questions: [], aiContent: '', view: 'own', openAnswer: '' };
            this.typicalLoading = true;
            try {
                const res = await axios.get('/api/kp/typical', { params: { kp_id: kp.id } });
                this.typicalModal.ownExamples = res.data || [];
            } finally {
                this.typicalLoading = false;
            }
        },
        async openTrace(question) {
            if (!question || !question.id) return;
            if (!this.ensureApiKey()) return;
            this.traceModal = { show: true, loading: true, saving: false, data: null };
            try {
                const res = await axios.post(`/api/questions/${question.id}/trace`);
                const data = res.data;
                (data.direct_points || []).forEach(p => { p._selected = true; });
                (data.prerequisite_points || []).forEach(p => { p._selected = true; });
                this.traceModal.data = data;
            } catch (err) {
                this.traceModal.show = false;
                alert((err.response && err.response.data && err.response.data.error) || '知识溯源失败');
            } finally {
                this.traceModal.loading = false;
            }
        },
        async confirmTrace() {
            const data = this.traceModal.data;
            if (!data) return;
            const points = []
                .concat((data.direct_points || []).map(p => ({ ...p, group: 'direct_points' })))
                .concat((data.prerequisite_points || []).map(p => ({ ...p, group: 'prerequisite_points' })))
                .filter(p => p._selected);
            if (!points.length) {
                alert('请至少勾选一个知识点');
                return;
            }
            if (!confirm(`确认用选中的 ${points.length} 个知识点生成知识溯源导图？`)) return;
            this.traceModal.saving = true;
            try {
                const qid = data.question_id || (this.detailQuestion && this.detailQuestion.id) || (this.reviewSelectedQuestion && this.reviewSelectedQuestion.id);
                const res = await axios.post(`/api/questions/${qid}/trace/confirm`, {
                    points,
                    symptom: data.symptom,
                    root_cause: data.root_cause,
                    path: data.path
                });
                this.traceModal.show = false;
                this.mindMapModal = {
                    show: true,
                    map: res.data.mindmap,
                    question: { id: qid },
                    newLabel: '',
                    newType: 'direct'
                };
            } catch (err) {
                alert('确认失败');
            } finally {
                this.traceModal.saving = false;
            }
        },
        async openMindMap(question) {
            if (!question || !question.id) return;
            const res = await axios.get(`/api/questions/${question.id}/mindmap`);
            if (!res.data.mindmap) {
                if (confirm('这道题还没有知识溯源导图，是否现在生成？')) {
                    this.openTrace(question);
                }
                return;
            }
            this.mindMapModal = { show: true, map: res.data.mindmap, question, newLabel: '', newType: 'direct' };
        },
        removeMindMapNode(nodeId) {
            if (nodeId === 'question') return;
            const map = this.mindMapModal.map;
            map.nodes = map.nodes.filter(n => n.id !== nodeId);
            map.edges = map.edges.filter(e => e.from !== nodeId && e.to !== nodeId);
        },
        addMindMapNode() {
            const label = (this.mindMapModal.newLabel || '').trim();
            if (!label) return;
            const map = this.mindMapModal.map;
            const id = 'custom-' + Date.now();
            map.nodes.push({
                id,
                type: this.mindMapModal.newType,
                label,
                detail: ''
            });
            const source = this.mindMapModal.newType === 'root'
                ? (map.nodes.find(n => n.type === 'direct') || map.nodes.find(n => n.type === 'symptom') || map.nodes[0])
                : (map.nodes.find(n => n.type === 'symptom') || map.nodes[0]);
            if (source && source.id !== id) {
                map.edges.push({ from: source.id, to: id });
            }
            this.mindMapModal.newLabel = '';
        },
        async saveMindMap() {
            const qid = this.mindMapModal.question.id;
            if (!confirm('确认保存这张知识溯源导图？')) return;
            await axios.post(`/api/questions/${qid}/mindmap`, { mindmap: this.mindMapModal.map });
            alert('导图已保存');
        },
        async generateTypicalAi(append = false) {
            if (!this.ensureApiKey()) return;
            this.typicalModal.view = 'ai';
            this.typicalModal.openAnswer = '';
            this.typicalAiLoading = true;
            try {
                const res = await axios.post('/api/ai/generate', {
                    kp_id: this.typicalModal.kp.id,
                    mode: this.typicalModal.mode
                });
                const stamp = Date.now();
                const questions = (res.data.questions || []).map((q, i) => ({
                    ...q, _selected: false, _key: `${stamp}-${i}`
                }));
                this.typicalModal.questions = append
                    ? this.typicalModal.questions.concat(questions)
                    : questions;
            } catch (err) {
                alert((err.response && err.response.data && err.response.data.error) || '生成失败');
            } finally {
                this.typicalAiLoading = false;
            }
        },
        continueTypicalAi() {
            this.generateTypicalAi(true);
        },
        toggleTypicalAnswer(key) {
            this.typicalModal.openAnswer = this.typicalModal.openAnswer === key ? '' : key;
        },
        humanizeMath(text) {
            if (!text) return '';
            let out = String(text);
            const greek = {
                alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', Delta: 'Δ',
                epsilon: 'ε', varepsilon: 'ε', zeta: 'ζ', eta: 'η', theta: 'θ',
                Theta: 'Θ', iota: 'ι', kappa: 'κ', lambda: 'λ', Lambda: 'Λ',
                mu: 'μ', nu: 'ν', xi: 'ξ', pi: 'π', Pi: 'Π', rho: 'ρ',
                sigma: 'σ', Sigma: 'Σ', tau: 'τ', phi: 'φ', varphi: 'φ',
                chi: 'χ', psi: 'ψ', omega: 'ω', Omega: 'Ω'
            };
            const sup = { '0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','+':'⁺','-':'⁻','n':'ⁿ','i':'ⁱ','(':'⁽',')':'⁾' };
            const sub = { '0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉','+':'₊','-':'₋','i':'ᵢ','j':'ⱼ','n':'ₙ' };
            // 矩阵/行列式
            out = out.replace(/\\begin\{(p|b|v|)matrix\}([\s\S]*?)\\end\{\1matrix\}/g, (m, kind, body) => {
                const rows = body.split(/\\\\/).map(r => r.trim().split('&').map(c => c.trim()).join('  ')).filter(Boolean);
                const open = kind === 'b' ? '[' : kind === 'v' ? '|' : '(';
                const close = kind === 'b' ? ']' : kind === 'v' ? '|' : ')';
                return rows.join('\n').replace(/^/gm, '  ');
            });
            out = out.replace(/\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}/g, '($1) ÷ ($2)');
            out = out.replace(/\\(dfrac|tfrac)\s*\{([^{}]+)\}\s*\{([^{}]+)\}/g, '($2) ÷ ($3)');
            out = out.replace(/\\sqrt\s*\[([^\]]+)\]\s*\{([^{}]+)\}/g, '($1)次根号($2)');
            out = out.replace(/\\sqrt\s*\{([^{}]+)\}/g, '√($1)');
            out = out.replace(/\\(vec|overrightarrow)\s*\{([^{}]+)\}/g, '$2⃗');
            out = out.replace(/\\hat\s*\{([^{}]+)\}/g, '$1̂');
            out = out.replace(/\\bar\s*\{([^{}]+)\}/g, '$1̄');
            out = out.replace(/\\dot\s*\{([^{}]+)\}/g, '$1̇');
            Object.keys(greek).forEach(k => {
                out = out.replace(new RegExp('\\\\' + k + '\\b', 'g'), greek[k]);
            });
            out = out.replace(/\\sum/g, 'Σ').replace(/\\int/g, '∫').replace(/\\infty/g, '∞');
            out = out.replace(/\\(to|rightarrow)/g, '→').replace(/\\Rightarrow/g, '⇒');
            out = out.replace(/\\times/g, '×').replace(/\\cdot/g, '·').replace(/\\div/g, '÷');
            out = out.replace(/\\leq?/g, '≤').replace(/\\geq?/g, '≥').replace(/\\neq/g, '≠');
            out = out.replace(/\\approx/g, '≈').replace(/\\pm/g, '±');
            out = out.replace(/\\partial/g, '∂').replace(/\\nabla/g, '∇');
            out = out.replace(/\\(sin|cos|tan|cot|sec|csc|log|ln|lim|max|min)\b/g, '$1');
            out = out.replace(/\\(left|right|,|;|!|quad|qquad)/g, ' ');
            // 上下标
            out = out.replace(/\^\s*\{([^{}]+)\}|\^\s*([0-9n+\-()])/g, (m, a, b) => {
                const src = a || b || '';
                return src.split('').map(ch => sup[ch] || ch).join('');
            });
            out = out.replace(/_\s*\{([^{}]+)\}|_\s*([0-9ijn+\-])/g, (m, a, b) => {
                const src = a || b || '';
                return src.split('').map(ch => sub[ch] || ch).join('');
            });
            out = out.replace(/\\([a-zA-Z]+)/g, '$1');
            out = out.replace(/[{}$]/g, '');
            out = out.replace(/\*\*/g, '').replace(/`/g, '');
            out = out.replace(/\*/g, '×').replace(/<=/g, '≤').replace(/>=/g, '≥');
            out = out.replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
            return out;
        },
        latexHtml(text) {
            const raw = String(text || '');
            const escapeHtml = s => s
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            if (!window.katex) {
                return escapeHtml(this.humanizeMath(raw)).replace(/\n/g, '<br>');
            }
            const pattern = /(\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|\$[^$\n]+?\$)/g;
            let out = '';
            let last = 0;
            let match;
            while ((match = pattern.exec(raw)) !== null) {
                out += escapeHtml(raw.slice(last, match.index)).replace(/\n/g, '<br>');
                let token = match[0];
                let displayMode = false;
                let expr = token;
                if (token.startsWith('$$')) {
                    expr = token.slice(2, -2);
                    displayMode = true;
                } else if (token.startsWith('\\[')) {
                    expr = token.slice(2, -2);
                    displayMode = true;
                } else if (token.startsWith('\\(')) {
                    expr = token.slice(2, -2);
                } else {
                    expr = token.slice(1, -1);
                }
                try {
                    out += window.katex.renderToString(expr, {
                        displayMode,
                        throwOnError: false,
                        strict: false
                    });
                } catch (e) {
                    out += escapeHtml(this.humanizeMath(token));
                }
                last = pattern.lastIndex;
            }
            out += escapeHtml(raw.slice(last)).replace(/\n/g, '<br>');
            return out;
        },
        async saveTypicalAi() {
            const selected = this.typicalModal.questions.filter(q => q._selected);
            if (!selected.length) {
                alert('请先勾选要保存的题目');
                return;
            }
            if (!confirm(`确认保存选中的 ${selected.length} 道题？`)) return;
            const content = selected.map((q, i) =>
                `第 ${i + 1} 题\n${q.question}\n\n答案：${q.answer}\n\n解析：${q.analysis}`
            ).join('\n\n');
            await axios.post('/api/ai/save', {
                kp_id: this.typicalModal.kp.id,
                mode: this.typicalModal.mode,
                content
            });
            alert('已保存');
            selected.forEach(q => { q._selected = false; });
        },
        async saveTypicalOne(q) {
            if (!confirm('确认保存这道题？')) return;
            await axios.post('/api/ai/save', {
                kp_id: this.typicalModal.kp.id,
                mode: this.typicalModal.mode,
                content: `题目：${q.question}\n\n答案：${q.answer}\n\n解析：${q.analysis}`
            });
            q._selected = false;
            alert('已保存本题');
        },
        ensureApiKey() {
            if (this.settings && this.settings.llm_api_key) return true;
            if (confirm('尚未配置大模型 API Key。请先到右上角「大模型配置」填写 API Key 后才能使用。是否现在打开配置？')) {
                this.openLlmConfig();
            }
            return false;
        },
        async generateAiMaterial() {
            if (!this.aiModal.kp) return;
            this.aiLoading = true;
            try {
                const res = await axios.post('/api/ai/generate', {
                    kp_id: this.aiModal.kp.id,
                    mode: this.aiModal.mode,
                    count: 2
                });
                this.aiModal.content = this.humanizeMath(res.data.content || '');
            } catch (err) {
                this.aiModal.content = '';
                alert((err.response && err.response.data && err.response.data.error) || '生成失败');
            } finally {
                this.aiLoading = false;
            }
        },
        regenerateAiMaterial() {
            this.generateAiMaterial();
        },
        async saveAiMaterial() {
            if (!this.aiModal.content.trim()) {
                alert('内容为空，无法保存');
                return;
            }
            if (!confirm('确认把这份内容保存到知识库？')) return;
            try {
                await axios.post('/api/ai/save', {
                    kp_id: this.aiModal.kp.id,
                    mode: this.aiModal.mode,
                    content: this.aiModal.content
                });
                alert('已保存');
                this.aiModal.show = false;
            } catch (err) {
                alert('保存失败');
            }
        },
        async saveQuestion() {
            if (!this.form.title_text && !this.form.title_image) {
                alert('请输入题干文本或上传图片');
                return;
            }
            if (!confirm('确认保存这道错题？')) return;
            if (this.form.id) {
                await axios.put(`/api/questions/${this.form.id}`, this.form);
            } else {
                await axios.post('/api/questions', this.form);
            }
            alert('保存成功');
            this.resetForm();
            await this.loadQuestions();
            await this.loadWeak();
            this.currentNav = 'library';
        },
        resetForm() {
            this.form = this.emptyForm();
            if (this.subjects.length) this.form.subject_id = this.subjects[0].id;
        },
        async recommendKp() {
            if (!this.form.title_text) {
                alert('请先输入题干文本');
                return;
            }
            this.recommending = true;
            try {
                // 如果没有题目id，先临时保存再推荐
                let qid = this.form.id;
                if (!qid) {
                    const res = await axios.post('/api/questions', this.form);
                    qid = res.data.id;
                    this.form.id = qid;
                }
                const rec = await axios.post(`/api/questions/${qid}/recommend_kp`);
                for (const item of (rec.data.auto_bound || [])) {
                    if (!this.form.knowledge_points.find(k => k.id === item.id)) {
                        this.form.knowledge_points.push({ ...item, is_auto: 1 });
                    }
                }
                this.pendingKps = (rec.data.pending || []).map(item => ({ ...item, _selected: true }));
                if (this.pendingKps.length) {
                    this.showPendingKpModal = true;
                } else if ((rec.data.auto_bound || []).length) {
                    alert('已自动绑定高置信度知识点');
                } else {
                    alert('没有达到推荐阈值的新知识点');
                }
            } catch (e) {
                alert('推荐失败：' + (e.response?.data?.error || e.message));
            } finally {
                this.recommending = false;
            }
        },
        async removeKp(idx) {
            const kp = this.form.knowledge_points[idx];
            this.form.knowledge_points.splice(idx, 1);
            if (kp && kp.is_auto && this.form.id) {
                try {
                    await axios.post(`/api/questions/${this.form.id}/kp_feedback`, {
                        kp_id: kp.id,
                        action: 'remove'
                    });
                    await axios.put(`/api/questions/${this.form.id}`, {
                        knowledge_points: this.form.knowledge_points
                    });
                } catch (e) {
                    // 反馈失败不影响移除
                }
            }
        },
        async confirmPendingKp() {
            const selected = this.pendingKps.filter(k => k._selected);
            if (!selected.length) {
                this.showPendingKpModal = false;
                return;
            }
            if (!confirm(`确认绑定选中的 ${selected.length} 个待确认知识点？`)) return;
            const res = await axios.post(`/api/questions/${this.form.id}/confirm_kp`, {
                kp_ids: selected.map(k => k.id)
            });
            for (const kp of (res.data.added || [])) {
                if (!this.form.knowledge_points.find(k => k.id === kp.id)) {
                    this.form.knowledge_points.push({ ...kp, confidence: 1, is_auto: 0 });
                }
            }
            this.showPendingKpModal = false;
        },
        isKpSelected(kid) {
            return this.form.knowledge_points.some(k => k.id === kid);
        },
        toggleKp(k) {
            const idx = this.form.knowledge_points.findIndex(x => x.id === k.id);
            if (idx >= 0) {
                this.form.knowledge_points.splice(idx, 1);
            } else {
                this.form.knowledge_points.push({ id: k.id, name: k.name, confidence: 1, is_auto: 0 });
            }
        },
        confirmKps() {
            this.showKpSelector = false;
        },
        openQuestion(q) {
            this.detailQuestion = q;
            this.$nextTick(() => this.renderMath());
        },
        editQuestion(q) {
            this.form = JSON.parse(JSON.stringify(q));
            this.showEditModal = true;
        },
        closeEditModal() {
            this.showEditModal = false;
            this.form = this.emptyForm();
        },
        async saveEditQuestion() {
            if (!this.form.title_text && !this.form.title_image) {
                alert('题干文本和图片不能都为空');
                return;
            }
            if (!confirm('确认保存这次修改？')) return;
            await axios.put(`/api/questions/${this.form.id}`, this.form);
            this.showEditModal = false;
            this.form = this.emptyForm();
            await this.loadQuestions();
            await this.loadWeak();
            alert('修改已保存');
        },
        async deleteQuestion(q) {
            if (!confirm('确定把这道错题移入回收站？')) return;
            await axios.delete(`/api/questions/${q.id}`);
            await this.loadQuestions();
            await this.loadWeak();
        },
        onFilterSubjectChange() {
            this.filter.kp_id = null;
            this.loadQuestions();
        },
        toggleQuestionSelect(qid) {
            const idx = this.selectedQuestionIds.indexOf(qid);
            if (idx >= 0) this.selectedQuestionIds.splice(idx, 1);
            else this.selectedQuestionIds.push(qid);
        },
        toggleSelectAllQuestions() {
            const ids = this.filteredQuestions.map(q => q.id);
            this.selectedQuestionIds = this.selectedQuestionIds.length === ids.length ? [] : ids;
        },
        async batchDeleteQuestions() {
            if (!this.selectedQuestionIds.length) {
                this.batchAction = '';
                return;
            }
            if (!confirm(`确认把选中的 ${this.selectedQuestionIds.length} 道错题移入回收站？`)) return;
            await axios.post('/api/questions/batch', { action: 'delete', ids: this.selectedQuestionIds });
            await this.loadQuestions();
            await this.loadWeak();
            this.batchAction = '';
            alert('已移入回收站');
        },
        handleBatchAction() {
            if (!this.selectedQuestionIds.length) {
                alert('请先多选错题');
                this.batchAction = '';
                return;
            }
            if (this.batchAction === 'bind_kp') {
                this.openBatchKp();
            } else if (this.batchAction === 'delete') {
                this.batchDeleteQuestions();
            }
        },
        async batchUpdateStatus() {
            if (!this.selectedQuestionIds.length) return;
            if (!confirm(`确认修改 ${this.selectedQuestionIds.length} 道错题的状态？`)) return;
            await axios.post('/api/questions/batch', {
                action: 'status',
                ids: this.selectedQuestionIds,
                status: this.batchStatus
            });
            await this.loadQuestions();
            await this.loadWeak();
            this.batchAction = '';
            alert('状态已更新');
        },
        openBatchKp() {
            if (!this.selectedQuestionIds.length) return;
            this.batchKpModal = { show: true, selected: [] };
        },
        isBatchKpSelected(kid) {
            return this.batchKpModal.selected.includes(kid);
        },
        toggleBatchKp(kid) {
            const idx = this.batchKpModal.selected.indexOf(kid);
            if (idx >= 0) this.batchKpModal.selected.splice(idx, 1);
            else this.batchKpModal.selected.push(kid);
        },
        async confirmBatchKp() {
            if (!this.batchKpModal.selected.length) {
                alert('请选择知识点');
                return;
            }
            if (!confirm(`确认给 ${this.selectedQuestionIds.length} 道错题关联所选知识点？`)) return;
            await axios.post('/api/questions/batch', {
                action: 'bind_kp',
                ids: this.selectedQuestionIds,
                kp_ids: this.batchKpModal.selected
            });
            this.batchKpModal.show = false;
            this.batchAction = '';
            await this.loadQuestions();
            await this.loadWeak();
            alert('知识点已关联');
        },
        async openTrash() {
            this.trashMode = true;
            this.trashQuestions = (await axios.get('/api/questions/trash')).data || [];
        },
        async closeTrash() {
            this.trashMode = false;
            await this.loadQuestions();
        },
        async restoreQuestion(q) {
            if (!confirm('确定恢复这道错题？')) return;
            await axios.post(`/api/questions/${q.id}/restore`);
            await this.openTrash();
            await this.loadWeak();
        },
        async purgeQuestion(q) {
            if (!confirm('彻底删除后无法恢复，确定继续？')) return;
            await axios.delete(`/api/questions/${q.id}/purge`);
            await this.openTrash();
        },
        async addSubject() {
            if (!this.newSubject) return;
            await axios.post('/api/subjects', { name: this.newSubject });
            this.newSubject = '';
            await this.loadSubjects();
        },
        async deleteSubject(s) {
            if (!confirm(`确定删除学科 ${s.name}？`)) return;
            await axios.delete(`/api/subjects/${s.id}`);
            await this.loadSubjects();
            await this.loadKnowledgePoints();
        },
        async addKp() {
            if (!this.kpForm.name || !this.kpForm.subject_id) return;
            const parent = this.knowledgePoints.find(k => k.id === this.kpForm.parent_id);
            const level = parent ? parent.level + 1 : 0;
            await axios.post('/api/knowledge_points', {
                subject_id: this.kpForm.subject_id,
                name: this.kpForm.name,
                parent_id: this.kpForm.parent_id,
                level: level
            });
            this.kpForm.name = '';
            await this.loadKnowledgePoints();
            await this.loadWeak();
        },
        changeSettingsSubject() {
            this.kpForm.parent_id = null;
            this.settingsKpHint = '';
        },
        startSettingsChildKp(kp) {
            this.kpForm.parent_id = kp.id;
            this.settingsKpHint = kp.name;
            this.$nextTick(() => {
                const input = this.$refs.settingsKpInput;
                if (input) input.focus();
            });
        },
        async addSettingsKp() {
            const name = (this.kpForm.name || '').trim();
            if (!name) {
                alert('请输入知识点名称');
                return;
            }
            if (!this.kpForm.subject_id) {
                alert('请先选择学科');
                return;
            }
            const parent = this.subjectKnowledgePoints.find(k => k.id === this.kpForm.parent_id);
            await axios.post('/api/knowledge_points', {
                subject_id: this.kpForm.subject_id,
                name: name,
                parent_id: this.kpForm.parent_id || null,
                level: parent ? parent.level + 1 : 0
            });
            this.kpForm.name = '';
            this.kpForm.parent_id = null;
            this.settingsKpHint = '';
            await this.loadKnowledgePoints();
            await this.loadWeak();
        },
        async deleteSettingsKp(kp) {
            if (!confirm(`确定删除知识点「${kp.name}」？其下子知识点会一并删除。`)) return;
            await axios.delete(`/api/knowledge_points/${kp.id}`);
            if (this.kpForm.parent_id === kp.id) {
                this.kpForm.parent_id = null;
                this.settingsKpHint = '';
            }
            await this.loadKnowledgePoints();
            await this.loadWeak();
        },
        selectSubjectDir(s) {
            this.kpForm.subject_id = s.id;
            this.kpForm.parent_id = null;
            this.settingsKpHint = '';
            this.$nextTick(() => {
                const input = this.$refs.settingsKpInput;
                if (input) input.focus();
            });
        },
        async openKpDetail(kp) {
            if (!kp) return;
            const byId = {};
            this.knowledgePoints.forEach(k => { byId[k.id] = k; });
            const names = [kp.name];
            let cur = kp.parent_id && byId[kp.parent_id] ? byId[kp.parent_id] : null;
            while (cur) {
                names.unshift(cur.name);
                cur = cur.parent_id && byId[cur.parent_id] ? byId[cur.parent_id] : null;
            }
            const subject = this.subjects.find(s => s.id === kp.subject_id);
            if (subject) names.unshift(subject.name);
            this.kpDetail = {
                show: true,
                kp,
                path: names.join(' > '),
                materials: [],
                newType: 'custom',
                newContent: ''
            };
            try {
                const res = await axios.get('/api/ai/materials', { params: { kp_id: kp.id } });
                this.kpDetail.materials = res.data || [];
            } catch (e) {
                this.kpDetail.materials = [];
            }
        },
        toggleDirRow(row) {
            if (row.isSubject) {
                const key = 's' + row.node.id;
                this.dirExpanded = { ...this.dirExpanded, [key]: !this.dirExpanded[key] };
                this.kpForm.subject_id = row.node.id;
                this.clearDirParent();
            } else {
                this.dirExpanded = { ...this.dirExpanded, [row.node.id]: !this.dirExpanded[row.node.id] };
            }
        },
        startRootKp(subject) {
            this.kpForm.subject_id = subject.id;
            this.kpForm.parent_id = null;
            this.settingsKpHint = subject.name;
            this.$nextTick(() => {
                const input = this.$refs.settingsKpInput;
                if (input) input.focus();
            });
        },
        startDirChild(kp) {
            this.kpForm.subject_id = kp.subject_id;
            this.kpForm.parent_id = kp.id;
            this.settingsKpHint = kp.name;
            this.$nextTick(() => {
                const input = this.$refs.settingsKpInput;
                if (input) input.focus();
            });
        },
        clearDirParent() {
            this.kpForm.parent_id = null;
            this.settingsKpHint = '';
        },
        subjectKpCount(sid) {
            return this.knowledgePoints.filter(k => k.subject_id === sid).length;
        },
        async addDirKp() {
            const name = (this.kpForm.name || '').trim();
            if (!name) {
                alert('请输入知识点名称');
                return;
            }
            if (!this.kpForm.subject_id) {
                alert('请先选择或展开一个学科');
                return;
            }
            try {
                const parent = this.knowledgePoints.find(k => k.id === this.kpForm.parent_id);
                const res = await axios.post('/api/knowledge_points', {
                    subject_id: this.kpForm.subject_id,
                    name: name,
                    parent_id: this.kpForm.parent_id || null,
                    level: parent ? parent.level + 1 : 0
                });
                const created = res.data;
                // 展开新节点所在的完整路径，并清掉搜索词，确保立刻可见
                const expand = {};
                if (created.parent_id) {
                    const byId = {};
                    this.knowledgePoints.forEach(k => { byId[k.id] = k; });
                    let cur = byId[created.parent_id];
                    while (cur) {
                        expand[cur.id] = true;
                        if (cur.subject_id) expand['s' + cur.subject_id] = true;
                        cur = cur.parent_id && byId[cur.parent_id] ? byId[cur.parent_id] : null;
                    }
                } else {
                    expand['s' + created.subject_id] = true;
                }
                this.dirExpanded = { ...this.dirExpanded, ...expand };
                this.kpSearch = '';
                this.kpForm.name = '';
                this.lastAddedKpId = created.id;
                this.clearDirParent();
                await this.loadKnowledgePoints();
                await this.loadWeak();
                // 让新节点闪现一下，方便定位
                setTimeout(() => {
                    this.lastAddedKpId = null;
                }, 2500);
            } catch (e) {
                const msg = (e.response && e.response.data && e.response.data.error) || '添加失败';
                alert(msg);
            }
        },
        async deleteDirKp(kp) {
            if (!confirm(`确定删除知识点「${kp.name}」？其下子知识点会一并删除。`)) return;
            await axios.delete(`/api/knowledge_points/${kp.id}`);
            if (this.kpForm.parent_id === kp.id) {
                this.clearDirParent();
            }
            await this.loadKnowledgePoints();
            await this.loadWeak();
        },
        async openLlmConfig() {
            this.mobileMenuOpen = false;
            if (!this.settings.llm_model) {
                await this.loadSettings();
            }
            this.showLlmModal = true;
        },
        async saveLlmConfig() {
            await axios.post('/api/settings', this.settings);
            this.showLlmModal = false;
            alert('大模型配置已保存');
        },
        async saveSettings() {
            await axios.post('/api/settings', this.settings);
            alert('设置已保存');
        },
        renderedTitle(text) {
            // 简单转义 HTML
            return (text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
        },
        renderMath() {
            if (typeof window !== 'undefined' && window.renderMathInElement) {
                window.renderMathInElement(document.body, {
                    delimiters: [
                        { left: '$$', right: '$$', display: true },
                        { left: '\\[', right: '\\]', display: true },
                        { left: '\\(', right: '\\)', display: false },
                        { left: '$', right: '$', display: false }
                    ],
                    throwOnError: false,
                    ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
                });
            }
        }
    }
};
const app = createApp(appOptions);
window.appInstance = app;
app.mount('#app');
console.log('错题本前端已加载');
