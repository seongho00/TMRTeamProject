package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.TradeAreaService;
import com.koreait.exam.tmrteamproject.vo.TradeArea;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
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

    private final TradeAreaService tradeAreaService;

    @GetMapping("/pdfread")
    public String pdfread(Model model) {
        tradeAreaService.processAndSaveAllTradeAreas(); // 전체 분석 및 저장 수행

        model.addAttribute("message", "PDF 분석 및 저장이 완료되었습니다.");
        return "trade/pdfread"; // 완료 메시지를 표시할 뷰
    }

    @GetMapping("/pdfread/detail")
    public String pdfreadDetail(String fileName, Model model) {

        if (fileName == null || fileName.isBlank()) {
            List<String> fileList = tradeAreaService.getRecentFileName();
            model.addAttribute("fileList", fileList);
            return "trade/select_file";
        }

        // PDF 텍스트 추출
        String pdfText = tradeAreaService.getPdfTextFromDb(fileName);

        // PDF 텍스트에서 분석된 데이터 추출
        TradeArea tradeArea = tradeAreaService.parseAndSaveTradeArea(pdfText, fileName);

        model.addAttribute("pdfText", pdfText);
        model.addAttribute("tradeArea", tradeArea);
        model.addAttribute("fileName", fileName);

        return "trade/pdfread";
    }
}
