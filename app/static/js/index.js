let state = {
    q: "",
    theloai_id: "",
    sort: "moi_nhat",
    page: 1,
};
let debounceTimer = null;

const searchInput = document.getElementById('searchInput');
const theloaiSelect = document.getElementById('theloaiSelect');
const sortSelect = document.getElementById('sortSelect');
const btnSearch = document.getElementById('btnSearch');
const chips = document.querySelectorAll('.chip-theloai');

function escapeHtml(str) {
    const div = document.createElement('div');
    div.innerText = str ?? "";
    return div.innerHTML;
}

function setActiveChip(id) {
    chips.forEach(chip => {
        const active = (chip.dataset.id || "") === (id || "");
        chip.classList.toggle('active', active);
        chip.classList.toggle('bg-primary', active);
        chip.classList.toggle('text-white', active);
        chip.classList.toggle('border-primary', active);
        chip.classList.toggle('border-gray-200', !active);
        chip.classList.toggle('text-slate-600', !active);
    });
}

function renderBookCard(s) {
    const badgeClass = s.soLuongConLai > 0 ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-500';
    const badgeText = s.soLuongConLai > 0 ? 'Còn sách' : 'Hết sách';
    return `
    <a href="/sach/${s.id}" class="group bg-white rounded-2xl overflow-hidden border border-gray-100 shadow-sm hover:shadow-xl transition-all duration-300">
        <div class="aspect-[3/4] overflow-hidden bg-slate-100">
            <img src="${s.anhBia}" alt="${s.tenSach}"
                 class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                 onerror="this.src='/static/image/default.png'">
        </div>
        <div class="p-4">
            <h3 class="font-bold text-slate-900 line-clamp-2 mb-1 group-hover:text-primary transition-colors">${escapeHtml(s.tenSach)}</h3>
            <p class="text-sm text-slate-500 mb-2 truncate">${escapeHtml(s.tacGia)}</p>
            <div class="flex items-center justify-between text-xs">
                <span class="flex items-center gap-1 text-amber-500 font-semibold">
                    <i data-lucide="star" class="w-3.5 h-3.5 fill-current"></i> ${s.diemDanhGiaTB}
                </span>
                <span class="px-2 py-1 rounded-full font-semibold ${badgeClass}">${badgeText}</span>
            </div>
        </div>
    </a>`;
}

function renderPagination(data) {
    const container = document.getElementById('pagination');
    container.innerHTML = "";
    if (data.total_pages <= 1) return;

    for (let i = 1; i <= data.total_pages; i++) {
        const btn = document.createElement('button');
        btn.innerText = i;
        const active = i === data.page;
        btn.className = `w-10 h-10 rounded-lg text-sm font-semibold transition-colors ${active ? 'bg-primary text-white' : 'bg-white border border-gray-200 text-slate-600 hover:border-primary hover:text-primary'}`;
        btn.addEventListener('click', () => {
            state.page = i;
            timKiemSach();
            window.scrollTo({ top: document.getElementById('the-loai').offsetTop - 100, behavior: 'smooth' });
        });
        container.appendChild(btn);
    }
}

async function timKiemSach() {
    const grid = document.getElementById('bookGrid');
    const loading = document.getElementById('loadingBooks');
    const empty = document.getElementById('emptyState');

    loading.classList.remove('hidden');
    grid.classList.add('hidden');
    empty.classList.add('hidden');

    const params = new URLSearchParams({
        q: state.q,
        sort: state.sort,
        page: state.page,
    });
    if (state.theloai_id) params.set('theloai_id', state.theloai_id);

    try {
        const res = await fetch(`/api/sach?${params.toString()}`);
        const data = await res.json();

        document.getElementById('resultCount').innerText = data.total ? `(${data.total} kết quả)` : "";
        document.getElementById('resultTitle').innerText = state.q ? `Kết quả tìm kiếm: "${state.q}"` : "Tất cả sách";

        if (!data.items || data.items.length === 0) {
            grid.innerHTML = "";
            empty.classList.remove('hidden');
        } else {
            grid.innerHTML = data.items.map(renderBookCard).join('');
            grid.classList.remove('hidden');
        }
        renderPagination(data);
        if (typeof lucide !== 'undefined') lucide.createIcons();
    } catch (e) {
        grid.innerHTML = '<p class="col-span-full text-center text-red-500 py-10">Lỗi tải dữ liệu sách.</p>';
        grid.classList.remove('hidden');
    } finally {
        loading.classList.add('hidden');
    }
}

searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        state.q = e.target.value.trim();
        state.page = 1;
        timKiemSach();
    }, 400);
});

btnSearch.addEventListener('click', () => {
    state.q = searchInput.value.trim();
    state.page = 1;
    timKiemSach();
});

searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        state.q = searchInput.value.trim();
        state.page = 1;
        timKiemSach();
    }
});

theloaiSelect.addEventListener('change', (e) => {
    state.theloai_id = e.target.value;
    state.page = 1;
    setActiveChip(e.target.value);
    timKiemSach();
});

sortSelect.addEventListener('change', (e) => {
    state.sort = e.target.value;
    state.page = 1;
    timKiemSach();
});

chips.forEach(chip => {
    chip.addEventListener('click', () => {
        state.theloai_id = chip.dataset.id || "";
        theloaiSelect.value = state.theloai_id;
        state.page = 1;
        setActiveChip(state.theloai_id);
        timKiemSach();
    });
});
