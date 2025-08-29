package com.koreait.exam.tmrteamproject.util;

import org.springframework.stereotype.Component;

// 메인 화면 그래프 평균 명/원 정규화
@Component("fmt")
public class Fmt {

    // 유동인구 단위 정규화
    // 인구수 12,345명 -> 축약 1.234만명
    public String peopleCompact(Long v) {
        if (v == null || v <= 0) return "–";
        if (v >= 100_000_000L) {
            double n = v / 100_000_000.0;
            return trim(n) + "억명";
        } else if (v >= 10_000L) {
            double n = v / 10_000.0;
            return trim(n) + "만명";
        } else {
            return String.format("%,d명" , v);
        }
    }

    // 매출액 단위 정규화
    public String krwCompact(Long v) {
        if (v == null || v <= 0) return "–";
        if (v >= 100_000_000L) {
            double n = v / 100_000_000.0;
            return trim(n) + "억원";
        }
        if (v >= 10_000L) {
            double n = v / 10_000.0;
            return trim(n) + "만원";
        }
        return String.format("%,d원", v);
    }

    // 소수점 표시 보정: 정수면 소수 제거, 아니면 최대 2자리
    private String trim(double n) {
        if (Math.abs(n - Math.rint(n)) < 1e-9) {
            return String.valueOf((long) Math.rint(n));
        }
        return String.format("%.2f", n).replaceAll("0+$", "").replaceAll("\\.$", "");
    }
}
