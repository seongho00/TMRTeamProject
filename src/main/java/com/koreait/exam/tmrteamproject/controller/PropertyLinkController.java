package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.RegionService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/properties")
@RequiredArgsConstructor
public class PropertyLinkController {

    private final RegionService regionService;

    @GetMapping("/link")
    public String linkPage(Model model) {
        model.addAttribute("regionData", regionService.getRegionData());
        return "property_links";
    }
}
