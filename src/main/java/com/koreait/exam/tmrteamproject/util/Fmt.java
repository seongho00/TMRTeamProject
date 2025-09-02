package com.koreait.exam.tmrteamproject.util;

import org.springframework.stereotype.Component;

// 메인 화면 그래프 평균 명/원 정규화
@Component("fmt")
public class Fmt {

    // 기준 상수
    private static final long TEN_THOUSAND = 10_000L;         // 만
    private static final long HUNDRED_MILLION = 100_000_000L; // 억
    private static final String DASH = "–"; // 값 없음 표시

    // 유동인구 표시 콤마 + "명"
    public String people(Long v) {
        if (v == null || v <= 0) return DASH;
        return String.format("%,d명", v);
    }

    // 축약: "x.x만명", "x.xx억명" (기본 소수 0자리)
    public String peopleCompact(Long v) {
        return peopleCompact(v, 0);
    }

    // 축약: "x.x만명", "x.xx억명" (소수 자리 지정)
    public String peopleCompact(Long v, int maxFractionDigits) {
        if (v == null || v <= 0) return DASH;

        if (v >= HUNDRED_MILLION) {               // 1억 명 이상 → 억명
            double n = v / (double) HUNDRED_MILLION;
            return trim(n, maxFractionDigits) + "억명";
        }
        if (v >= TEN_THOUSAND) {                  // 1만 명 이상 → 만명
            double n = v / (double) TEN_THOUSAND;
            return trim(n, maxFractionDigits) + "만명";
        }
        // 그 외 → 그냥 명
        return String.format("%,d명", v);
    }

    // 매출액 표시 콤마 + "원"
    public String krw(Long v) {
        if (v == null || v <= 0) return DASH;
        return String.format("%,d원", v);
    }

    // 축약: "x,xxx만원", "x.xx억원" (기본 소수 0자리)
    public String krwCompact(Long v) {
        return krwCompact(v, 0);
    }

    // 축약: "x,xxx만원", "x.xx억원" (소수 자리 지정)
    public String krwCompact(Long v, int maxFractionDigits) {
        if (v == null || v <= 0) return DASH;

        // 1억 이상은 억원으로 우선 표기(대부분 대시보드에 적합)
        if (v >= HUNDRED_MILLION) {
            double n = v / (double) HUNDRED_MILLION;
            return trim(n, maxFractionDigits) + "억원";
        }
        // 1만 이상은 만원으로 표기
        if (v >= TEN_THOUSAND) {
            double n = v / (double) TEN_THOUSAND;
            // 만원은 정수 위주가 보기 좋아서 기본 자리수 0 추천
            return trim(n, Math.min(maxFractionDigits, 0)) + "만원";
        }
        // 그 외 → 원
        return String.format("%,d원", v);
    }

    // 정수면 소수 제거, 아니면 maxFractionDigits 까지만 표시(뒤 0/점 제거)
    private String trim(double n, int maxFractionDigits) {
        // 안전 가드
        if (Double.isNaN(n) || Double.isInfinite(n)) return DASH;
        if (maxFractionDigits <= 0) {
            long rounded = Math.round(n);
            return String.format("%,d", rounded);
        }
        // 반올림 포맷 문자열 구성
        String fmt = "%,." + Math.min(maxFractionDigits, 6) + "f";
        String s = String.format(fmt, n);
        // 뒤쪽 0 제거, 소수점만 남으면 제거
        s = s.replaceAll("0+$", "").replaceAll("\\.$", "");
        // "1,000" 처럼 천단위 구분 유지
        return s;
    }
}
