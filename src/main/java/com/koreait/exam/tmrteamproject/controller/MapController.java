package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.AdminDongService;
import com.koreait.exam.tmrteamproject.service.MapService;
import com.koreait.exam.tmrteamproject.service.MemberService;
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
    private MapService mapService;
    @Autowired
    private AdminDongService adminDongService;
    @Autowired
    private UpjongCodeService upjongCodeService;


    @GetMapping("/commercialZoneMap")
    public String commercialZoneMap() {

        return "map/commercialZoneMap";
    }

    @GetMapping("/getEmds")
    @ResponseBody
    public List<AdminDong> getEmds(String sgg) {

        List<AdminDong> adminDong = adminDongService.getAdminDongsBySgg(sgg);

        return adminDong;
    }

    @GetMapping("/getMiddleCategories")
    @ResponseBody
    public List<UpjongCode> getMiddleCategories(String majorCd) {

        List<UpjongCode> upjongCode = upjongCodeService.getGroupedUpjongCodesByMajorCd(majorCd);

        return upjongCode;
    }

    @GetMapping("/getMinorCategories")
    @ResponseBody
    public List<UpjongCode> getMinorCategories(String middleCd) {

        List<UpjongCode> upjongCode = upjongCodeService.getUpjongCodesByMiddleCd(middleCd);

        return upjongCode;
    }


    @GetMapping("/getUpjongCodeByMinorCd")
    @ResponseBody
    public UpjongCode getUpjongCodeByMinorCd(String minorCd) {

        UpjongCode upjongCode = upjongCodeService.getUpjongCodeByMinorCd(minorCd);
        return upjongCode;
    }

    @GetMapping("/searchUpjong")
    @ResponseBody
    public List<UpjongCode> searchUpjong(String keyword) {
        System.out.println(keyword);
        List<UpjongCode> upjongCode = upjongCodeService.getUpjongCodeByKeyword(keyword);
        System.out.println(upjongCode);
        return upjongCode;
    }
}
