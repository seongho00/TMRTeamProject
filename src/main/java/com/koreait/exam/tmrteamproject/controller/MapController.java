package com.koreait.exam.tmrteamproject.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("usr/map")
@Slf4j
@RequiredArgsConstructor
public class MapController {

    @GetMapping("/commercialZoneMap")
    public String commercialZoneMap() {
        return "map/commercialZoneMap";
    }

    @GetMapping("/correlationMap")
    public String correlationMap() {
        return "map/correlationMap";
    }
}
