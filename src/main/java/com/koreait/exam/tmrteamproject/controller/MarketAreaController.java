package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.MarketAreaService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import java.util.List;

@Controller
@Slf4j
@RequiredArgsConstructor
@RequestMapping("usr/area")
public class MarketAreaController {

    @Autowired
    private MarketAreaService marketAreaService;

    @GetMapping("/page")
    public String binPage() {
        return "trade/binPage";
    }

    @GetMapping("/pdfread")
    public String pdfread(Model model) {
        List<String> images = marketAreaService.extractImagesFromPdf();
        model.addAttribute("images", images);
        String pdfText = marketAreaService.getPdfRead();
        model.addAttribute("pdfText", pdfText);
        return "trade/pdfread";
    }
}
