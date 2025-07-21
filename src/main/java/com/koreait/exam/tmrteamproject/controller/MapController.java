package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.MapService;
import com.koreait.exam.tmrteamproject.service.MemberService;
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
    private MapService mapService;

    @GetMapping("/commercialZoneMap")
    public String commercialZoneMap() {

        return "map/commercialZoneMap";
    }

    @GetMapping("/getEmds")
    @ResponseBody
    public List<AdminDong> getEmds(String sgg) {

        List<AdminDong> adminDong = mapService.getEmdsBySgg(sgg);

        return adminDong;
    }
}
