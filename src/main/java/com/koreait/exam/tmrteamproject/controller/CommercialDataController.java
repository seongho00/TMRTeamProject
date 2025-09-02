package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.CommercialDataService;
import com.koreait.exam.tmrteamproject.vo.CommercialData;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

@Controller
@RequestMapping("usr/commercialData")
@Slf4j
@RequiredArgsConstructor
@CrossOrigin(origins = "http://localhost:3000")
public class CommercialDataController {
    private final CommercialDataService commercialDataService;

    @GetMapping("/getPopulation")
    @ResponseBody
    public CommercialData getPopulation() {
        return commercialDataService.getFirstRow();
    }

    @GetMapping("/findByEmdCode")
    @ResponseBody
    public CommercialData findByEmdCode(String emdCode) {
        return commercialDataService.findByEmdCode(emdCode);
    }

}
