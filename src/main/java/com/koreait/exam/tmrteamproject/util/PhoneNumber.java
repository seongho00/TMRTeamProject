package com.koreait.exam.tmrteamproject.util;

public class PhoneNumber {
    private PhoneNumber () {}

    // 국내형 정규화
    public static String toLocalKR (String phoneNumber) {
        if (phoneNumber == null) return null;

        String only = phoneNumber.replaceAll("[^0-9+]", "");

        // 국가코드 변형 처리
        if (only.startsWith("+82")) {
            only = only.substring(3);
        } else if (only.startsWith("0082")) {
            only = only.substring(4);
        } else if (only.startsWith("82")) {
            only = only.substring(2);
        }

        // 변형 후 앞자리가 0이 아니면 0 추가
        if (!only.startsWith("0")) {
            only = "0" + only;
        }

        // 하이픈 제거 최종 정리 (혹시 남아 있을 수 있는 비숫자 제거)
        only = only.replaceAll("\\D", "");

        // 유효성 체크 (01x 시작, 길이 10~11)
        if (!only.matches("^01[016789]\\d{7,8}$")) {
            return null; // 유효하지 않으면 null
        }

        return only;
    }

    // 국제형(E.164)으로 정규화: +8210XXXXXXXX
    public static String toE164KR(String raw) {
        String local = toLocalKR(raw);
        if (local == null) return null;
        // 010XXXXXXXX -> 10XXXXXXXX 추출
        String noZero = local.startsWith("0") ? local.substring(1) : local;
        return "+82" + noZero;
    }
}
