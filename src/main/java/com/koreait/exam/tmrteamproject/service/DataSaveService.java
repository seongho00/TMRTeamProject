package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.DataSaveRepository;
import com.koreait.exam.tmrteamproject.vo.ClosedBiz;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.*;
import org.springframework.stereotype.Service;
import org.springframework.ui.Model;

import java.io.File;
import java.io.FileInputStream;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class DataSaveService {

    private final DataSaveRepository dataSaveRepository;

    public String setInsertData(File file, Model model) {
        log.debug("파일명: {}", file.getName());
        log.debug("파일 크기: {}", file.length());

        try {
            // 파일 확인
            if (file.length() == 0) {
                model.addAttribute("message", "없는 파일입니다.");
                return "dataset/excel";
            }

            //확장자 검사
            String fileName = file.getName();
            if (!fileName.endsWith(".xlsx") && !fileName.endsWith(".xls")) {
                model.addAttribute("message", "Excel 파일만 가능합니다");
                return "dataset/excel";
            }

            List<ClosedBiz> closedBizs = new ArrayList<>();

            try {
                FileInputStream fis = new FileInputStream(file);
                Workbook workbook = WorkbookFactory.create(fis);

                Sheet sheet = workbook.getSheetAt(0);

                for (int i = 1; i < sheet.getPhysicalNumberOfRows(); i++) {
                    Row row = sheet.getRow(i);
                    if (row == null) continue;

                    try {
                        ClosedBiz closedBiz = ClosedBiz.builder()
                                .dongName(getCellString(row.getCell(0)))
                                .upjongType(getCellString(row.getCell(1)))
                                .closeYm(getCellString(row.getCell(2)))
                                .closeCount(getCellString(row.getCell(3)))
                                .build();

                        closedBizs.add(closedBiz);
                    } catch (Exception e) {
                        log.warn("행 {} 처리 중 오류: {}", i, e.getMessage());
                    }
                }
            } catch (Exception e) {
                model.addAttribute("message", "파일 읽기 실패" +  e.getMessage());
            }

            log.debug("파싱된 폐업 데이터 리스트: {}", closedBizs);
            model.addAttribute("message", "총 " + closedBizs.size() + "건의 데이터가 성공적으로 파싱되었습니다.");

            // DB 저장
            for (ClosedBiz closedBiz : closedBizs) {
                dataSaveRepository.save(closedBiz);
            }

        } catch (Exception e) {
            model.addAttribute("message", "파일 처리중 오류가 발생 했습니다." + e.getMessage());
        }

        return "dataset/excel";
    }

    private String getCellString(Cell cell) {
        if (cell == null) return "";
        return switch (cell.getCellType()) {
            case STRING -> cell.getStringCellValue();
            case NUMERIC -> String.valueOf(cell.getNumericCellValue());
            case BOOLEAN -> String.valueOf(cell.getBooleanCellValue());
            case FORMULA -> cell.getCellFormula();
            default -> "";
        };
    }
}
