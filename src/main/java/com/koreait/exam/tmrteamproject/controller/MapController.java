package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.AdminDongService;
import com.koreait.exam.tmrteamproject.service.UpjongCodeService;
import com.koreait.exam.tmrteamproject.vo.AdminDong;
import com.koreait.exam.tmrteamproject.vo.UpjongCode;
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

    @GetMapping("/commercialZoneMap")
    public String commercialZoneMap(Model model) {

        List<AdminDong> adminDongsGroupBySggCd = adminDongService.getAdminDongsGroupBySgg();

        model.addAttribute("adminDongsGroupBySggCd", adminDongsGroupBySggCd);

        return "map/commercialZoneMap";
    }

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

    // 위험도 페이지
    @GetMapping("/correlationMap")
    public String correlationMap(Model model) {

        List<AdminDong> adminDongsGroupBySggCd = adminDongService.getAdminDongsGroupBySgg();

        model.addAttribute("adminDongsGroupBySggCd", adminDongsGroupBySggCd);

        return "map/correlationMap";
    }

    @GetMapping("/api/upjong")
    @ResponseBody
    public List<UpjongCode> listUpjong() {

        return upjongCodeService.findAll();
    }
}
