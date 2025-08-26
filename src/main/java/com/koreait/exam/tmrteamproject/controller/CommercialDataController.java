package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.AdminDongService;
import com.koreait.exam.tmrteamproject.service.CommercialDataService;
import com.koreait.exam.tmrteamproject.service.UpjongCodeService;
import com.koreait.exam.tmrteamproject.vo.AdminDong;
import com.koreait.exam.tmrteamproject.vo.CommercialData;
import com.koreait.exam.tmrteamproject.vo.UpjongCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.List;

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
