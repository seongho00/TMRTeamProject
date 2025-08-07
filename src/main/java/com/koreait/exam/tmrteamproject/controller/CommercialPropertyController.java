package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.repository.CommercialPropertyRepository;
import com.koreait.exam.tmrteamproject.service.CommercialDataService;
import com.koreait.exam.tmrteamproject.service.CommercialPropertyService;
import com.koreait.exam.tmrteamproject.vo.CommercialData;
import com.koreait.exam.tmrteamproject.vo.CommercialProperty;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.List;

@Controller
@RequestMapping("usr/commercialProperty")
@Slf4j
@RequiredArgsConstructor
@CrossOrigin(origins = "http://localhost:3000")
public class CommercialPropertyController {
    private final CommercialPropertyService commercialPropertyService;

    @GetMapping("/getCommercialProperty")
    @ResponseBody
    public List<CommercialProperty> getCommercialProperty() {
        return commercialPropertyService.getCommercialProperty();
    }


}
