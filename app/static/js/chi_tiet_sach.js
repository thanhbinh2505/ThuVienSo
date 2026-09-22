document.addEventListener('DOMContentLoaded', () => {
    const page = document.getElementById('book-detail-page');
    if (!page) return;

    const bookId = page.dataset.bookId;

    initRating(bookId);
    initComments(bookId);
    initBorrow(bookId);
    initFavorite(bookId);
});

function initRating(bookId) {
    const stars = document.querySelectorAll('.rating-star');
    const message = document.getElementById('rating-message');
    const container = document.getElementById('rating-stars');

    if (!stars.length) return;

    let selectedRating = 0;

    const renderStars = rating => {
        stars.forEach(star => {
            const value = Number(star.dataset.rating);
            const active = value <= rating;
            const icon = star.querySelector('[data-lucide="star"]');

            star.classList.toggle('text-amber-400', active);
            star.classList.toggle('text-slate-300', !active);
            star.classList.toggle('bg-amber-50', active);

            if (icon) {
                icon.classList.toggle('fill-current', active);
            }
        });
    };

    stars.forEach(star => {
        star.addEventListener('mouseenter', () => {
            renderStars(Number(star.dataset.rating));
        });

        star.addEventListener('click', async () => {
            const rating = Number(star.dataset.rating);

            try {
                const response = await fetch(`/api/sach/${bookId}/danh-gia`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ so_sao: rating })
                });

                const data = await response.json();

                if (!data.success) {
                    showMessage(message, data.message, 'error');
                    return;
                }

                selectedRating = rating;
                renderStars(selectedRating);

                document.querySelectorAll('.js-average-rating').forEach(element => {
                    element.textContent = data.diemDanhGiaTB;
                });

                document.querySelectorAll('.js-rating-count').forEach(element => {
                    element.textContent = `(${data.soLuotDanhGia} lượt đánh giá)`;
                });

                showMessage(message, `✓ ${data.message}`, 'success');
            } catch (error) {
                console.error('Lỗi đánh giá:', error);
                showMessage(message, 'Có lỗi xảy ra khi đánh giá!', 'error');
            }
        });
    });

    container?.addEventListener('mouseleave', () => {
        renderStars(selectedRating);
    });
}

function initComments(bookId) {
    const button = document.getElementById('btn-comment');
    const input = document.getElementById('comment-input');
    const message = document.getElementById('comment-message');
    const list = document.getElementById('comment-list');

    if (!button || !input || !list) return;

    button.addEventListener('click', async () => {
        const content = input.value.trim();

        if (!content) {
            showMessage(message, 'Vui lòng nhập nội dung bình luận!', 'error');
            input.focus();
            return;
        }

        setButtonLoading(button, true);

        try {
            const response = await fetch(`/api/sach/${bookId}/binh-luan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ noi_dung: content })
            });

            const data = await response.json();

            if (!data.success) {
                showMessage(message, data.message, 'error');
                return;
            }

            document.getElementById('no-comment')?.remove();

            list.insertAdjacentHTML('afterbegin', createCommentHtml(data.data));

            input.value = '';
            updateCommentCount();
            refreshLucideIcons();

            showMessage(message, '✓ Bình luận thành công!', 'success');
        } catch (error) {
            console.error('Lỗi bình luận:', error);
            showMessage(message, 'Có lỗi xảy ra khi bình luận!', 'error');
        } finally {
            setButtonLoading(button, false);
            refreshLucideIcons();
        }
    });

    list.addEventListener('click', async event => {
        const deleteButton = event.target.closest('.btn-delete-comment');
        if (!deleteButton) return;

        await deleteComment(deleteButton.dataset.commentId);
    });
}

async function deleteComment(commentId) {
    if (!window.confirm('Bạn có chắc muốn xóa bình luận này?')) return;

    try {
        const response = await fetch(`/api/binh-luan/${commentId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (!data.success) {
            window.alert(data.message);
            return;
        }

        document.getElementById(`comment-${commentId}`)?.remove();

        updateCommentCount();
        showEmptyCommentState();
    } catch (error) {
        console.error('Lỗi xóa bình luận:', error);
        window.alert('Có lỗi xảy ra khi xóa bình luận!');
    }
}

function createCommentHtml(comment) {
    const name = (comment.hoTen || '?').trim();
    const avatar = escapeHtml(name.charAt(0).toUpperCase());

    return `
        <article id="comment-${comment.id}" class="group rounded-2xl border border-slate-100 bg-slate-50/60 p-5 hover:bg-white hover:shadow-sm transition-all">
            <div class="flex items-start gap-4">
                <div class="shrink-0 w-11 h-11 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                    ${avatar}
                </div>
                <div class="min-w-0 flex-1">
                    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                        <div>
                            <p class="font-bold text-slate-800">${escapeHtml(name)}</p>
                            <p class="text-xs text-slate-400 mt-1">${escapeHtml(comment.ngayTao || '')}</p>
                        </div>
                        <button type="button" class="btn-delete-comment inline-flex items-center gap-1.5 self-start text-xs font-semibold text-red-500 hover:text-red-600 hover:bg-red-50 px-2.5 py-1.5 rounded-lg transition" data-comment-id="${comment.id}">
                            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                            Xóa
                        </button>
                    </div>
                    <p class="text-slate-600 mt-4 leading-7 whitespace-pre-line">${escapeHtml(comment.noiDung)}</p>
                </div>
            </div>
        </article>
    `;
}

function showEmptyCommentState() {
    const list = document.getElementById('comment-list');

    if (!list || list.querySelector('article') || document.getElementById('no-comment')) return;

    list.insertAdjacentHTML(
        'beforeend',
        `
            <div id="no-comment" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 p-10 text-center">
                <i data-lucide="message-square" class="w-9 h-9 mx-auto text-slate-300"></i>
                <p class="text-slate-500 mt-3 font-medium">Chưa có bình luận nào.</p>
                <p class="text-sm text-slate-400 mt-1">Hãy là người đầu tiên chia sẻ cảm nhận về cuốn sách này.</p>
            </div>
        `
    );

    refreshLucideIcons();
}

function updateCommentCount() {
    const countElement = document.getElementById('comment-count');
    if (!countElement) return;

    const count = document.querySelectorAll('#comment-list > article').length;
    countElement.textContent = `${count} bình luận`;
}

function initBorrow(bookId) {
    const button = document.getElementById('btn-borrow');
    const message = document.getElementById('borrow-message');

    if (!button) return;

    button.addEventListener('click', async () => {
        if (!window.confirm('Bạn có chắc muốn đăng ký mượn cuốn sách này không?')) return;

        button.disabled = true;
        button.textContent = 'Đang gửi...';

        try {
            const response = await fetch(`/api/sach/${bookId}/muon`, {
                method: 'POST'
            });

            const data = await response.json();

            if (!data.success) {
                showMessage(message, data.message, 'error');
                resetBorrowButton(button);
                return;
            }

            showMessage(message, `✓ ${data.message}`, 'success');

            button.textContent = 'Đã đăng ký mượn';
            button.classList.remove('bg-primary');
            button.classList.add('bg-gray-400');
        } catch (error) {
            console.error('Lỗi đăng ký mượn:', error);
            showMessage(message, 'Có lỗi xảy ra khi đăng ký mượn!', 'error');
            resetBorrowButton(button);
        }
    });
}

function initFavorite(bookId) {
    const button = document.getElementById('btn-favorite');
    const message = document.getElementById('favorite-message');

    if (!button) return;

    button.addEventListener('click', async () => {
        button.disabled = true;

        try {
            const response = await fetch(`/api/sach/${bookId}/yeu-thich`, {
                method: 'POST'
            });

            const data = await response.json();

            if (!data.success) {
                showMessage(message, data.message, 'error');
                return;
            }

            showMessage(message, `✓ ${data.message}`, 'success');
            updateFavoriteButton(button, data.da_yeu_thich);
        } catch (error) {
            console.error('Lỗi cập nhật yêu thích:', error);
            showMessage(message, 'Có lỗi xảy ra khi cập nhật yêu thích!', 'error');
        } finally {
            button.disabled = false;
        }
    });
}

function updateFavoriteButton(button, isFavorite) {
    if (isFavorite) {
        button.innerHTML = '❤️ Đã yêu thích';
        button.classList.remove('bg-red-50', 'text-red-500', 'border-red-200');
        button.classList.add('bg-red-500', 'text-white');
        return;
    }

    button.innerHTML = '🤍 Yêu thích';
    button.classList.remove('bg-red-500', 'text-white');
    button.classList.add('bg-red-50', 'text-red-500', 'border-red-200');
}

function resetBorrowButton(button) {
    button.disabled = false;
    button.textContent = '📚 Đăng ký mượn sách';
}

function setButtonLoading(button, loading) {
    button.disabled = loading;

    if (loading) {
        button.dataset.originalText = button.textContent.trim();
        button.textContent = 'Đang gửi...';
        return;
    }

    button.innerHTML = '<i data-lucide="send" class="w-4 h-4"></i> Gửi bình luận';
}

function showMessage(element, message, type) {
    if (!element) return;

    element.textContent = message;
    element.className = type === 'success'
        ? 'text-sm mt-3 min-h-[20px] text-green-600 font-semibold'
        : 'text-sm mt-3 min-h-[20px] text-red-500';
}

function refreshLucideIcons() {
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
}