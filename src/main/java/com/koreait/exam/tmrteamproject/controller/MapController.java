package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.AdminDongService;
import com.koreait.exam.tmrteamproject.service.UpjongCodeService;
import com.koreait.exam.tmrteamproject.vo.AdminDong;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.List;

@Controller
@RequestMapping("usr/map")
@Slf4j
@RequiredArgsConstructor
public class MapController {

    @Autowired
    private AdminDongService adminDongService;

    @Autowired
    private UpjongCodeService upjongCodeService;

    @GetMapping("/getEmdsBySggNm")
    @ResponseBody
    public List<AdminDong> getEmdsBySggNm(String sgg) {

        return adminDongService.getAdminDongsBySggNm(sgg);
    }

    @GetMapping("/getSggByEmd")
    @ResponseBody
    public List<AdminDong> getSggByEmd(String sgg) {

        return adminDongService.getAdminDongsBySggNm(sgg);
    }

    // 유동인구 및 매출액 맵
    @GetMapping("/commercialZoneMap")
    public String commercialZoneMap(Model model) {

        List<AdminDong> adminDongsGroupBySggCd = adminDongService.getAdminDongsGroupBySgg();

        model.addAttribute("adminDongsGroupBySggCd", adminDongsGroupBySggCd);
        model.addAttribute("upjongNames", upjongCodeService.getAllNames());

        return "map/commercialZoneMap";
    }

    // 위험도 페이지
    @GetMapping("/riskMap")
    public String correlationMap(Model model) {

        List<AdminDong> adminDongsGroupBySggCd = adminDongService.getAdminDongsGroupBySgg();

        model.addAttribute("adminDongsGroupBySggCd", adminDongsGroupBySggCd);
        model.addAttribute("upjongNames", upjongCodeService.getAllNames());

        return "map/riskMap";
    }
}
