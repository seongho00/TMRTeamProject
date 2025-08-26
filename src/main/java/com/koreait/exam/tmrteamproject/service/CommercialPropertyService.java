package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.CommercialPropertyRepository;
import com.koreait.exam.tmrteamproject.vo.CommercialProperty;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CommercialPropertyService {

    private final CommercialPropertyRepository commercialPropertyRepository;

    // 문자열에서 월세만 추출
    private int parseMonthlyRent(String price) {
        if (price == null || !price.contains("/")) return 0;

        try {
            String[] parts = price.replace(",", "").split("/");
            return Integer.parseInt(parts[1].trim()) * 10_000;  // 두 번째 숫자 (월세)
        } catch (Exception e) {
            return 0;
        }
    }

    private int parseDeposit(String price) {
        if (price == null || !price.contains("/")) return 0;

        String depositStr = price.split("/")[0].trim(); // "1억 4,000" 등

        depositStr = depositStr.replace(",", "").replace(" ", "");

        int deposit = 0;

        try {
            // 예: "1억4000" → 100000000 + 4000000
            if (depositStr.contains("억")) {
                String[] parts = depositStr.split("억");
                int eok = Integer.parseInt(parts[0]) * 100_000_000;

                int man = 0;
                if (parts.length > 1 && !parts[1].isEmpty()) {
                    man = Integer.parseInt(parts[1]) * 10_000;
                }
                deposit = eok + man;
            } else {
                deposit = Integer.parseInt(depositStr) * 10_000;
            }

            System.out.println(deposit);
        } catch (NumberFormatException e) {
            // 파싱 실패 시 0으로 처리
            deposit = 0;
        }

        return deposit;
    }

    public Map<String, Double> getAverageDepositAndMonthlyRent() {
        List<CommercialProperty> list = commercialPropertyRepository.findByPriceType("월세");
        List<Integer> monthlyRents = new ArrayList<>();
        List<Integer> deposits = new ArrayList<>();
        List<Integer> managementFees = new ArrayList<>();

        for (CommercialProperty p : list) {
            String price = p.getPrice();
            if (price == null || !price.contains("/")) continue;

            int rent = parseMonthlyRent(price);
            int deposit = parseDeposit(price);
            int fee = p.getManagementFee() * 10000;

            if (rent > 0) monthlyRents.add(rent);
            if (deposit > 0) deposits.add(deposit);
            if (fee > 0) managementFees.add(fee);
        }

        double avgRent = monthlyRents.stream().mapToInt(Integer::intValue).average().orElse(0);
        double avgDeposit = deposits.stream().mapToInt(Integer::intValue).average().orElse(0);
        double avgFee = managementFees.stream().mapToInt(Integer::intValue).average().orElse(0);

        Map<String, Double> result = new HashMap<>();
        result.put("avgMonthlyRent", avgRent);
        result.put("avgManagementFee", avgFee);
        result.put("avgDeposit", avgDeposit);
        return result;
    }
}
