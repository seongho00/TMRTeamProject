package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.CommercialPropertyService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.Map;

@Controller
@RequestMapping("/usr/commercialProperty")
@Slf4j
@RequiredArgsConstructor
@CrossOrigin(origins = "http://localhost:3000")
public class CommercialPropertyController {
    private final CommercialPropertyService commercialPropertyService;

    @GetMapping("/getAverageDepositAndMonthlyRent")
    @ResponseBody
    public Map<String, Double> getAverageDepositAndMonthlyRent(String emdCode) {
        Map<String, Double> data = commercialPropertyService.getAverageDepositAndMonthlyRent();
        System.out.println(data.toString());

        return data;
    }
}
