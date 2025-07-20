package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.TradeAreaService;
import com.koreait.exam.tmrteamproject.vo.TradeArea;
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
@RequestMapping("usr/trade")
public class TradeAreaController {

    @Autowired
    private TradeAreaService tradeAreaService;

    @GetMapping("/pdfread")
    public String pdfread(String fileName, Model model) {
        // fileName이 없으면 최신 10개 파일 목록 보여주기
        if (fileName == null || fileName.isBlank()) {
            List<String> fileList = tradeAreaService.getRecentFileName();
            model.addAttribute("fileList", fileList);
            return "trade/select_file";  // 사용자가 파일 선택하는 페이지
        }

        // PDF 텍스트 추출
        String pdfText = tradeAreaService.getPdfTextFromDb(fileName);
        System.out.println("PDF 원문:\n" + pdfText);

        // PDF 텍스트에서 분석된 데이터 추출
        TradeArea tradeArea = tradeAreaService.parseAndSaveTradeArea(pdfText, fileName);

        model.addAttribute("pdfText", pdfText);
        model.addAttribute("images", tradeAreaService.extractImagesFromDbPdf(fileName));
        model.addAttribute("tradeArea", tradeArea);
        model.addAttribute("fileName", fileName);

        return "trade/pdfread";
    }
}
