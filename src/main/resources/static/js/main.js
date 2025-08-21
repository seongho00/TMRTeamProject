// /static/js/main.js
// 헤더 아이콘 팝업 토글 + STOMP 구독(서버 push 수신 시 팝업 오픈)

(function(){
    // 팝업 열기: 제목/본문/링크 설정 후 보이기
    function openNotifPopover(title, message, linkUrl) {
        const pop = document.getElementById('notif-popover');
        if (!pop) return;

        // 제목/본문/링크 세팅
        const t = document.getElementById('notif-title');
        const m = document.getElementById('notif-message');
        const a = document.getElementById('notif-link');
        if (t) t.textContent = title || '일정 알림';
        if (m) m.textContent = message || '';
        if (a) {
            if (linkUrl) { a.href = linkUrl; a.style.display = 'inline-flex'; }
            else { a.style.display = 'none'; }
        }

        // 표시
        pop.classList.remove('hidden');

        // 화면 우측에서 잘리는 경우를 대비해 살짝 안쪽으로 밀어 넣기(안전 여백)
        const rect = pop.getBoundingClientRect();
        const gap = 8;
        if (rect.right > window.innerWidth - gap) {
            pop.style.right = (rect.right - (window.innerWidth - gap)) + 'px';
        } else {
            pop.style.right = '0px';
        }
    }

    // 팝업 닫기
    function closeNotifPopover() {
        const pop = document.getElementById('notif-popover');
        if (pop) pop.classList.add('hidden');
    }

    // 초기 바인딩
    document.addEventListener('DOMContentLoaded', () => {
        const icon = document.getElementById('notif-icon');
        const closeBtn = document.getElementById('notif-close');
        const pop = document.getElementById('notif-popover');

        // 아이콘 클릭 시 팝업 토글
        if (icon) {
            icon.addEventListener('click', () => {
                if (pop && pop.classList.contains('hidden')) {
                    openNotifPopover('알림센터', '새로운 알림이 없습니다.', null);
                } else {
                    closeNotifPopover();
                }
            });
        }

        // 닫기 버튼
        if (closeBtn) closeBtn.addEventListener('click', closeNotifPopover);

        // 바깥 클릭 시 닫기
        document.addEventListener('click', (e) => {
            const withinIcon = icon && icon.contains(e.target);
            const withinPop  = pop && pop.contains(e.target);
            if (!withinIcon && !withinPop) closeNotifPopover();
        });

        // 웹소켓(STOMP) 연결: 서버 push 수신 시 팝업 오픈
        if (window.LOGIN_MEMBER_ID) {
            const socket = new SockJS('/ws');
            const stomp  = Stomp.over(socket);
            stomp.debug = null; // 디버그 로그 끔

            stomp.connect({}, () => {
                const dest = '/topic/member/' + window.LOGIN_MEMBER_ID;
                stomp.subscribe(dest, (frame) => {
                    try {
                        const payload = JSON.parse(frame.body); // DueAlert 형태
                        const link = '/schedule/' + payload.scheduleId; // 상세 링크 예시
                        openNotifPopover(payload.name, payload.msg, link);
                    } catch (e) {
                        openNotifPopover('일정 알림', frame.body, null);
                    }
                });
            }, () => {
                // 연결 실패 시 재시도(간단 버전)
                setTimeout(() => { location.reload(); }, 5000);
            });
        }
    });
})();
