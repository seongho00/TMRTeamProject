// 최근 수신 알림 1건을 메모리에 보관
let lastAlert = null;

document.addEventListener('DOMContentLoaded', () => {

    // STOMP 연결 및 구독
    const socket = new SockJS('/ws');
    const stomp  = Stomp.over(socket);
    stomp.debug  = null; // 디버그 로그 비활성화

    stomp.connect({}, () => {
        console.log('Connected!');

        // 로그인 사용자 개인 토픽 구독
        if (window.LOGIN_MEMBER_ID) {
            const memberTopic = '/topic/member/' + window.LOGIN_MEMBER_ID;
            stomp.subscribe(memberTopic, (frame) => {
                try {
                    const p = JSON.parse(frame.body); // DueAlert 구조
                    lastAlert = p;
                } catch (e) {
                    lastAlert = { name: '일정 알림', msg: frame.body };
                }
            });
        }
    }, (err) => {
        setTimeout(() => location.reload(), 5000);
    });
});
