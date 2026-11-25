let allVideos = [];
let appSettings = {};
let pollInterval = null;
let isAccountConnected = false;

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('authorized') === '1') {
        alert("🎉 Tebrikler! Pinterest hesabınız resmi Authorize yöntemiyle başarıyla bağlandı.\n'pins:write' yetkisi dahil tüm video izinleri aktif edildi!");
        window.history.replaceState({}, document.title, window.location.pathname);
    }
    refreshData();
    pollInterval = setInterval(refreshStatusAndLogs, 4000);
});

async function refreshData() {
    await Promise.all([
        loadSettings(),
        loadVideos(),
        loadStatus(),
        loadLogs()
    ]);
}

async function refreshStatusAndLogs() {
    await Promise.all([
        loadStatus(),
        loadVideos(false),
        loadLogs()
    ]);
}

// Ayarları Yükle
async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        if (res.ok) {
            appSettings = await res.json();
            document.getElementById('inputInterval').value = appSettings.interval_minutes || '1';
            document.getElementById('inputDefaultLink').value = appSettings.default_link || '';
            document.getElementById('inputGeminiKey').value = appSettings.gemini_api_key || '';
            if (document.getElementById('checkUseSandbox')) {
                document.getElementById('checkUseSandbox').checked = appSettings.use_sandbox === 'true';
            }
            if (document.getElementById('inputModalAccessToken')) {
                document.getElementById('inputModalAccessToken').value = appSettings.pinterest_access_token || '';
            }
            if (document.getElementById('inputOAuthAppId')) {
                document.getElementById('inputOAuthAppId').value = appSettings.pinterest_app_id || '';
            }
            if (document.getElementById('inputOAuthAppSecret')) {
                document.getElementById('inputOAuthAppSecret').value = appSettings.pinterest_app_secret || '';
            }
            
            document.getElementById('intervalDisplay').innerText = `${appSettings.interval_minutes || 1} Dakika`;
            document.getElementById('boardNameDisplay').innerText = `Pano: ${appSettings.pinterest_board_name || 'Seçilmedi'}`;
        }
    } catch (e) {
        console.error('Ayarlar yüklenemedi:', e);
    }
}

// Durumu Yükle
async function loadStatus() {
    try {
        const res = await fetch('/api/status');
        if (res.ok) {
            const data = await res.json();
            const isRunning = data.is_running;
            isAccountConnected = data.account_connected;

            // Otomasyon Durumu
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            const btnStart = document.getElementById('btnStartAuto');
            const btnStop = document.getElementById('btnStopAuto');

            if (isRunning) {
                statusDot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse';
                statusText.innerText = 'Otomasyon Aktif (1 Dk)';
                statusText.className = 'text-emerald-400 font-bold';
                btnStart.classList.add('hidden');
                btnStop.classList.remove('hidden');
            } else {
                statusDot.className = 'w-2.5 h-2.5 rounded-full bg-slate-500';
                statusText.innerText = 'Durduruldu';
                statusText.className = 'text-slate-300';
                btnStart.classList.remove('hidden');
                btnStop.classList.add('hidden');
            }

            // Pinterest Hesap Durumu
            const warningBanner = document.getElementById('connectWarningBanner');
            const navBtn = document.getElementById('navConnectBtn');
            const navBtnText = document.getElementById('navConnectBtnText');
            const accName = document.getElementById('accountNameDisplay');
            const connectBadge = document.getElementById('connectStateBadge');
            const detailsBox = document.getElementById('connectedAccountDetails');

            if (isAccountConnected && data.account_info) {
                const user = data.account_info;
                warningBanner.classList.add('hidden');

                navBtn.className = 'px-4 py-2 rounded-xl text-sm font-bold bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-emerald-500/30 transition flex items-center gap-2';
                navBtnText.innerText = `@${user.username || 'findsdecks'}`;

                accName.innerText = `@${user.username || 'findsdecks'}`;
                accName.className = 'text-lg font-bold text-emerald-400 truncate';

                if (connectBadge) {
                    connectBadge.className = 'font-bold text-emerald-400 flex items-center gap-1';
                    connectBadge.innerHTML = '<i class="fas fa-circle-check"></i> Hesabınız Bağlı & Aktif';
                }

                if (detailsBox) {
                    detailsBox.classList.remove('hidden');
                    document.getElementById('connectedUserName').innerText = user.business_name || user.username;
                    document.getElementById('connectedUserType').innerText = `${user.account_type || 'Pinterest Hesabı'} (Aktif)`;
                    if (user.profile_image) {
                        document.getElementById('connectedUserAvatar').src = user.profile_image;
                    }
                }
            } else {
                warningBanner.classList.remove('hidden');
                navBtn.className = 'px-4 py-2 rounded-xl text-sm font-bold bg-red-600 hover:bg-red-500 text-white transition flex items-center gap-2 shadow-lg shadow-red-600/30 animate-pulse';
                navBtnText.innerText = 'Pinterest Hesabını Bağla';

                accName.innerText = 'Bağlı Değil';
                accName.className = 'text-lg font-bold text-slate-400 truncate';

                if (connectBadge) {
                    connectBadge.className = 'font-bold text-rose-400 flex items-center gap-1';
                    connectBadge.innerHTML = '<i class="fas fa-circle-xmark"></i> Bağlı Değil';
                }
                if (detailsBox) {
                    detailsBox.classList.add('hidden');
                }
            }
        }
    } catch (e) {
        console.error('Durum yüklenemedi:', e);
    }
}

// Pinterest Hesabını Doğrula ve Bağla
async function connectPinterestAccount() {
    const token = document.getElementById('inputModalAccessToken').value.trim();
    if (!token) {
        alert('Lütfen Pinterest Access Token bilginizi girin.');
        return;
    }

    const btn = document.getElementById('btnConnectPinterest');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Doğrulanıyor...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/pinterest/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ access_token: token })
        });
        const data = await res.json();

        if (data.success) {
            alert(data.message);
            populateBoardsDropdown(data.boards, data.selected_board);
            refreshData();
        } else {
            alert('Bağlantı Hatası: ' + data.message);
        }
    } catch (e) {
        alert('Sunucu iletişim hatası: ' + e);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function fetchBoardsManually() {
    try {
        const res = await fetch('/api/pinterest/boards');
        if (res.ok) {
            const data = await res.json();
            populateBoardsDropdown(data.boards);
        }
    } catch (e) {
        alert('Panolar alınamadı: ' + e);
    }
}

function populateBoardsDropdown(boards, selectedBoard = null) {
    const dropdown = document.getElementById('boardSelectDropdown');
    if (!boards || boards.length === 0) {
        dropdown.innerHTML = '<option value="">Panolarınız bulunamadı (Önce hesap bağlayın)</option>';
        return;
    }

    dropdown.innerHTML = boards.map(b => {
        const isSelected = (selectedBoard && selectedBoard.id === b.id) || (appSettings.pinterest_board_id === b.id);
        return `<option value="${b.id}" ${isSelected ? 'selected' : ''}>${escapeHtml(b.name)}</option>`;
    }).join('');
}

async function handleBoardSelect(event) {
    const boardId = event.target.value;
    const boardName = event.target.options[event.target.selectedIndex].text;
    if (!boardId) return;

    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pinterest_board_id: boardId,
                pinterest_board_name: boardName
            })
        });
        document.getElementById('boardNameDisplay').innerText = `Pano: ${boardName}`;
        refreshData();
    } catch (e) {
        console.error('Pano seçimi kaydedilemedi:', e);
    }
}

function switchConnectTab(tab) {
    const tabAuth = document.getElementById('tabContentAuthorize');
    const tabToken = document.getElementById('tabContentToken');
    const btnAuth = document.getElementById('tabBtnAuthorize');
    const btnToken = document.getElementById('tabBtnToken');

    if (tab === 'authorize') {
        tabAuth.classList.remove('hidden');
        tabToken.classList.add('hidden');
        btnAuth.className = 'flex-1 py-2.5 text-center text-red-400 border-b-2 border-red-500 flex items-center justify-center gap-1.5';
        btnToken.className = 'flex-1 py-2.5 text-center text-slate-400 hover:text-slate-200 border-b-2 border-transparent flex items-center justify-center gap-1.5';
    } else {
        tabAuth.classList.add('hidden');
        tabToken.classList.remove('hidden');
        btnToken.className = 'flex-1 py-2.5 text-center text-red-400 border-b-2 border-red-500 flex items-center justify-center gap-1.5';
        btnAuth.className = 'flex-1 py-2.5 text-center text-slate-400 hover:text-slate-200 border-b-2 border-transparent flex items-center justify-center gap-1.5';
    }
}

function startPinterestAuthorize() {
    const appId = document.getElementById('inputOAuthAppId').value.trim();
    const appSecret = document.getElementById('inputOAuthAppSecret').value.trim();

    if (!appId) {
        alert('Lütfen Pinterest Developers sayfanızdaki App ID (Client ID) bilgisini girin.');
        return;
    }
    if (!appSecret) {
        alert('Lütfen Pinterest Developers sayfanızdaki App Secret bilgisini girin.');
        return;
    }

    const redirectUri = window.location.origin + '/oauth/callback';
    const confirmMsg = `Pinterest resmi yetkilendirme ekranına yönlendiriliyorsunuz.\n\nLütfen developers.pinterest.com/apps sayfasında Redirect URI olarak şu adresin kayıtlı olduğundan emin olun:\n${redirectUri}\n\nDevam edilsin mi?`;
    
    if (confirm(confirmMsg)) {
        window.location.href = `/oauth/pinterest/login?app_id=${encodeURIComponent(appId)}&app_secret=${encodeURIComponent(appSecret)}`;
    }
}

// Modal Kontrolleri
function openConnectModal() {
    document.getElementById('connectModal').classList.remove('hidden');
    if (isAccountConnected) {
        fetchBoardsManually();
    }
}

function closeConnectModal() {
    document.getElementById('connectModal').classList.add('hidden');
}

function openSettingsModal() {
    document.getElementById('settingsModal').classList.remove('hidden');
}

function closeSettingsModal() {
    document.getElementById('settingsModal').classList.add('hidden');
}

async function saveGeneralSettings() {
    const payload = {
        interval_minutes: document.getElementById('inputInterval').value.trim(),
        default_link: document.getElementById('inputDefaultLink').value.trim(),
        gemini_api_key: document.getElementById('inputGeminiKey').value.trim(),
        use_sandbox: document.getElementById('checkUseSandbox').checked ? 'true' : 'false'
    };

    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        alert(data.message);
        closeSettingsModal();
        refreshData();
    } catch (e) {
        alert('Ayarlar kaydedilemedi: ' + e);
    }
}

// Videoları Yükle
async function loadVideos(showLoader = true) {
    try {
        const res = await fetch('/api/videos');
        if (res.ok) {
            allVideos = await res.json();
            renderVideos(allVideos);
        }
    } catch (e) {
        console.error('Videolar yüklenemedi:', e);
    }
}

function renderVideos(videos) {
    const listEl = document.getElementById('videosList');
    const pendingCountEl = document.getElementById('pendingCount');
    const completedCountEl = document.getElementById('completedCount');
    const summaryText = document.getElementById('queueSummaryText');

    let pending = 0;
    let completed = 0;

    videos.forEach(v => {
        if (v.status === 'pending') pending++;
        if (v.status === 'completed') completed++;
    });

    pendingCountEl.innerText = pending;
    completedCountEl.innerText = completed;
    summaryText.innerText = `${videos.length} video (${pending} sırada bekliyor)`;

    const master = document.getElementById('checkSelectAll');
    if (master) master.checked = false;
    const delBtn = document.getElementById('btnDeleteSelected');
    if (delBtn) delBtn.classList.add('hidden');

    if (videos.length === 0) {
        listEl.innerHTML = `
            <div class="p-8 text-center text-slate-500">
                <i class="fas fa-video-slash text-3xl mb-3 block"></i>
                Henüz video eklenmemiş. Yukarıdaki "Video Yükle" veya "Klasörden Toplu Çek" butonlarını kullanın.
            </div>
        `;
        return;
    }

    listEl.innerHTML = videos.map(video => {
        let statusBadge = '';
        if (video.status === 'pending') {
            statusBadge = '<span class="px-2.5 py-1 text-[11px] rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold"><i class="fas fa-clock mr-1"></i>Bekliyor</span>';
        } else if (video.status === 'processing') {
            statusBadge = '<span class="px-2.5 py-1 text-[11px] rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold animate-pulse"><i class="fas fa-spinner fa-spin mr-1"></i>Pinterest\'e Yükleniyor</span>';
        } else if (video.status === 'completed') {
            statusBadge = '<span class="px-2.5 py-1 text-[11px] rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold"><i class="fas fa-check mr-1"></i>Gerçekten Paylaşıldı</span>';
        } else {
            statusBadge = '<span class="px-2.5 py-1 text-[11px] rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold"><i class="fas fa-triangle-exclamation mr-1"></i>Paylaşılamadı</span>';
        }

        const titleText = video.title || 'Başlık henüz üretilmedi (Otomatik üretilecek)';
        const descText = video.description || 'Açıklama ve hashtagler otomatik oluşturulacak...';
        const tagsText = video.tags || 'Etiketler bekleniyor';

        return `
            <div class="p-5 hover:bg-slate-800/40 transition">
                <div class="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                    <!-- Sol: Video ve İçerik Detayları -->
                    <div class="space-y-3 flex-1">
                        <div class="flex items-center gap-3">
                            <input type="checkbox" class="video-checkbox w-4 h-4 rounded text-red-600 bg-slate-900 border-slate-700 cursor-pointer" data-id="${video.id}" onchange="updateSelectedCount()">
                            <span class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-red-500 font-bold text-xs border border-slate-700 shrink-0">
                                <i class="fas fa-play"></i>
                            </span>
                            <div>
                                <h4 class="text-sm font-bold text-white flex items-center gap-2">
                                    ${escapeHtml(video.product_name || video.filename)}
                                    ${statusBadge}
                                </h4>
                                <p class="text-[11px] text-slate-400">${escapeHtml(video.filename)} &bull; ${formatBytes(video.filesize)}</p>
                            </div>
                        </div>

                        <!-- Pinterest Alanları (Görselinizdeki formata göre) -->
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs bg-slate-900/90 p-3.5 rounded-xl border border-slate-800">
                            <div>
                                <span class="text-[11px] font-semibold text-slate-400 block mb-0.5">📌 Başlık:</span>
                                <div class="text-slate-200 font-medium">${escapeHtml(titleText)}</div>
                            </div>
                            <div>
                                <span class="text-[11px] font-semibold text-slate-400 block mb-0.5">🔗 Bağlantı:</span>
                                <div class="text-indigo-400 truncate">${escapeHtml(video.link || 'Varsayılan mağaza linki')}</div>
                            </div>
                            <div class="md:col-span-2">
                                <span class="text-[11px] font-semibold text-slate-400 block mb-0.5">📝 Açıklama & Hashtagler:</span>
                                <div class="text-slate-300 whitespace-pre-line text-[11px] line-clamp-2">${escapeHtml(descText)}</div>
                            </div>
                            <div class="md:col-span-2">
                                <span class="text-[11px] font-semibold text-slate-400 block mb-0.5">🏷️ Etiketlenen Konular:</span>
                                <div class="text-amber-300 text-[11px]">${escapeHtml(tagsText)}</div>
                            </div>
                        </div>

                        ${video.pin_url ? `
                            <div class="text-xs bg-red-950/20 p-2.5 rounded-xl border border-red-500/30 flex items-center justify-between">
                                <a href="${escapeHtml(video.pin_url)}" target="_blank" class="text-red-400 hover:text-red-300 font-bold flex items-center gap-1.5 underline">
                                    <i class="fab fa-pinterest text-base"></i> Gerçek Pin Yayında! Pinterest'te Görüntüle &rarr;
                                </a>
                                <span class="text-[11px] text-slate-400">${escapeHtml(video.published_at || '')}</span>
                            </div>
                        ` : ''}

                        ${video.error_message ? `
                            <div class="text-xs text-rose-400 bg-rose-950/30 p-2.5 rounded-xl border border-rose-900/50 flex items-start gap-2">
                                <i class="fas fa-triangle-exclamation text-rose-500 mt-0.5"></i>
                                <div>
                                    <strong>Paylaşım Hatası:</strong> ${escapeHtml(video.error_message)}
                                </div>
                            </div>
                        ` : ''}
                    </div>

                    <!-- Sağ: Butonlar -->
                    <div class="flex items-center lg:flex-col gap-2 shrink-0">
                        <button onclick="shareSingleNow(${video.id})" class="px-3.5 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1.5 w-full justify-center shadow-lg shadow-emerald-600/20">
                            <i class="fas fa-paper-plane"></i> Şimdi Paylaş
                        </button>
                        <button onclick="generateAIForVideo(${video.id})" class="px-3 py-1.5 rounded-xl text-xs font-medium bg-purple-900/40 hover:bg-purple-800 text-purple-200 border border-purple-500/30 transition flex items-center gap-1 w-full justify-center">
                            <i class="fas fa-wand-magic-sparkles"></i> AI Yenile
                        </button>
                        <button onclick="openEditModal(${video.id})" class="px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-1 w-full justify-center">
                            <i class="fas fa-pen"></i> Düzenle
                        </button>
                        <button onclick="deleteVideoItem(${video.id})" class="px-3 py-1.5 rounded-xl text-xs font-medium bg-rose-950/40 hover:bg-rose-900 text-rose-300 border border-rose-500/30 transition flex items-center gap-1 w-full justify-center">
                            <i class="fas fa-trash"></i> Sil
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Logları Yükle
async function loadLogs() {
    try {
        const res = await fetch('/api/logs');
        if (res.ok) {
            const logs = await res.json();
            const logsBox = document.getElementById('logsBox');
            if (logs.length > 0) {
                logsBox.innerHTML = logs.map(l => {
                    let color = 'text-slate-300';
                    if (l.level === 'SUCCESS') color = 'text-emerald-400 font-semibold';
                    if (l.level === 'ERROR') color = 'text-rose-400 font-semibold';
                    if (l.level === 'WARNING') color = 'text-amber-400';
                    return `<div><span class="text-slate-600">[${l.created_at}]</span> <span class="${color}">${escapeHtml(l.message)}</span></div>`;
                }).join('');
            }
        }
    } catch (e) {
        console.error('Loglar yüklenemedi:', e);
    }
}

// Otomasyon Başlat / Durdur
async function startAutomation() {
    try {
        const res = await fetch('/api/automation/start', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        refreshData();
    } catch (e) {
        alert('Otomasyon başlatılamadı: ' + e);
    }
}

async function stopAutomation() {
    try {
        const res = await fetch('/api/automation/stop', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        refreshData();
    } catch (e) {
        alert('Otomasyon durdurulamadı: ' + e);
    }
}

// Tek Video Şimdi Paylaş
async function shareSingleNow(id) {
    if (!confirm('Bu video hemen Pinterest hesabınızda paylaşılsın mı?')) return;
    try {
        const res = await fetch(`/api/videos/${id}/share`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            alert('Tebrikler! Video Pinterest hesabınızda başarıyla paylaşıldı!\nPin URL: ' + (data.result?.url || ''));
        } else {
            alert('Paylaşım başarısız: ' + (data.message || ''));
        }
        refreshData();
    } catch (e) {
        alert('Hata: ' + e);
    }
}

// AI İçerik Üret
async function scanAllVideosAI() {
    if (!confirm("Kuyruktaki tüm videolar taranacak ve ürünlerine özel başlık, açıklama ve etiketler yenilenecektir. Onaylıyor musunuz?")) return;
    
    alert("Videolar taranıyor, lütfen birkaç saniye bekleyin...");
    try {
        const res = await fetch("/api/videos/scan-all-ai", { method: "POST" });
        const data = await res.json();
        if (data.success) {
            alert("✅ " + data.message);
            loadVideos();
        } else {
            alert("Hata: " + data.message);
        }
    } catch (e) {
        alert("Tarama hatası: " + e);
    }
}

async function generateAIForVideo(id) {
    try {
        const res = await fetch(`/api/videos/${id}/generate-ai`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            refreshData();
        } else {
            alert('İçerik üretilemedi: ' + data.message);
        }
    } catch (e) {
        alert('Hata: ' + e);
    }
}

// Video Sil
async function deleteVideoItem(id) {
    if (!confirm('Bu videoyu listeden silmek istediğinize emin misiniz?')) return;
    try {
        await fetch(`/api/videos/${id}`, { method: 'DELETE' });
        refreshData();
    } catch (e) {
        alert('Silinemedi: ' + e);
    }
}

// Dosya Yükleme
async function handleFileUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        const res = await fetch('/api/videos/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        alert(data.message);
        event.target.value = '';
        refreshData();
    } catch (e) {
        alert('Yükleme hatası: ' + e);
    }
}

// Klasör Tarama
function openFolderScanModal() {
    document.getElementById('folderModal').classList.remove('hidden');
}

function closeFolderScanModal() {
    document.getElementById('folderModal').classList.add('hidden');
}

async function scanFolderSubmit() {
    const folderPath = document.getElementById('inputFolderPath').value.trim();
    if (!folderPath) {
        alert('Lütfen bir klasör yolu girin.');
        return;
    }

    try {
        const res = await fetch('/api/videos/scan-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: folderPath })
        });
        const data = await res.json();
        alert(data.message);
        closeFolderScanModal();
        refreshData();
    } catch (e) {
        alert('Klasör tarama hatası: ' + e);
    }
}

// Video Düzenleme Modalı
function openEditModal(videoId) {
    const video = allVideos.find(v => v.id === videoId);
    if (!video) return;

    document.getElementById('editVideoId').value = video.id;
    document.getElementById('editProductName').value = video.product_name || '';
    document.getElementById('editTitle').value = video.title || '';
    document.getElementById('editDescription').value = video.description || '';
    document.getElementById('editLink').value = video.link || '';
    document.getElementById('editTags').value = video.tags || '';

    document.getElementById('editVideoModal').classList.remove('hidden');
}

function closeEditModal() {
    document.getElementById('editVideoModal').classList.add('hidden');
}

async function regenerateAIForEditing() {
    const pName = document.getElementById('editProductName').value.trim();
    if (!pName) {
        alert('Lütfen önce bir ürün adı girin.');
        return;
    }

    try {
        const res = await fetch('/api/ai/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_name: pName })
        });
        const data = await res.json();
        document.getElementById('editTitle').value = data.title;
        document.getElementById('editDescription').value = data.description;
        document.getElementById('editTags').value = data.tags;
    } catch (e) {
        alert('AI içerik üretilemedi: ' + e);
    }
}

async function saveVideoEdit() {
    const videoId = document.getElementById('editVideoId').value;
    const payload = {
        product_name: document.getElementById('editProductName').value.trim(),
        title: document.getElementById('editTitle').value.trim(),
        description: document.getElementById('editDescription').value.trim(),
        link: document.getElementById('editLink').value.trim(),
        tags: document.getElementById('editTags').value.trim()
    };

    try {
        const res = await fetch(`/api/videos/${videoId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        closeEditModal();
        refreshData();
    } catch (e) {
        alert('Değişiklikler kaydedilemedi: ' + e);
    }
}

// Yardımcı Fonksiyonlar
function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// --- Toplu Video Silme Fonksiyonları ---
function toggleBulkDeleteMenu() {
    const el = document.getElementById('bulkDeleteDropdown');
    if (el) el.classList.toggle('hidden');
}

document.addEventListener('click', function(e) {
    const btn = document.getElementById('btnBulkMenu');
    const menu = document.getElementById('bulkDeleteDropdown');
    if (btn && menu && !btn.contains(e.target) && !menu.contains(e.target)) {
        menu.classList.add('hidden');
    }
});

function toggleSelectAllVideos(master) {
    const checkboxes = document.querySelectorAll('.video-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = master.checked;
    });
    updateSelectedCount();
}

function updateSelectedCount() {
    const checked = document.querySelectorAll('.video-checkbox:checked');
    const btn = document.getElementById('btnDeleteSelected');
    const countText = document.getElementById('selectedCountText');
    const master = document.getElementById('checkSelectAll');
    const allCbs = document.querySelectorAll('.video-checkbox');

    if (master && allCbs.length > 0) {
        master.checked = checked.length === allCbs.length;
    }

    if (btn && countText) {
        if (checked.length > 0) {
            btn.classList.remove('hidden');
            countText.innerText = `Seçilenleri Sil (${checked.length})`;
        } else {
            btn.classList.add('hidden');
            countText.innerText = `Seçilenleri Sil (0)`;
        }
    }
}

async function deleteSelectedVideos() {
    const checked = document.querySelectorAll('.video-checkbox:checked');
    if (checked.length === 0) {
        alert('Lütfen silinecek videoları işaretleyin.');
        return;
    }

    const ids = Array.from(checked).map(cb => parseInt(cb.dataset.id));
    if (!confirm(`Seçilen ${ids.length} adet videoyu kuyruktan ve diskten kalıcı olarak silmek istediğinize emin misiniz?`)) {
        return;
    }

    try {
        const res = await fetch('/api/videos/bulk-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: ids })
        });
        const data = await res.json();
        alert(data.message || `${ids.length} video silindi.`);
        refreshData();
    } catch (e) {
        alert('Silme işleminde hata: ' + e);
    }
}

async function deleteAllVideos() {
    const dropdown = document.getElementById('bulkDeleteDropdown');
    if (dropdown) dropdown.classList.add('hidden');

    if (!confirm('DİKKAT: Kuyruktaki TÜM videoları (tamamı silinecek) kalıcı olarak silmek istediğinizden emin misiniz? Bu işlem geri alınamaz!')) {
        return;
    }

    try {
        const res = await fetch('/api/videos/bulk-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ all: true })
        });
        const data = await res.json();
        alert(data.message || 'Tüm videolar silindi.');
        refreshData();
    } catch (e) {
        alert('Silme işleminde hata: ' + e);
    }
}

async function deleteCompletedVideos() {
    const dropdown = document.getElementById('bulkDeleteDropdown');
    if (dropdown) dropdown.classList.add('hidden');

    if (!confirm('Pinterest\'te başarıyla PAYLAŞILMIŞ olan tüm videoları kuyruktan temizlemek istiyor musunuz?')) {
        return;
    }

    try {
        const res = await fetch('/api/videos/bulk-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'completed' })
        });
        const data = await res.json();
        alert(data.message || 'Paylaşılan videolar temizlendi.');
        refreshData();
    } catch (e) {
        alert('Silme işleminde hata: ' + e);
    }
}

async function deleteFailedVideos() {
    const dropdown = document.getElementById('bulkDeleteDropdown');
    if (dropdown) dropdown.classList.add('hidden');

    if (!confirm('Hata veren tüm videoları kuyruktan temizlemek istiyor musunuz?')) {
        return;
    }

    try {
        const res = await fetch('/api/videos/bulk-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'failed' })
        });
        const data = await res.json();
        alert(data.message || 'Hatalı videolar temizlendi.');
        refreshData();
    } catch (e) {
        alert('Silme işleminde hata: ' + e);
    }
}
