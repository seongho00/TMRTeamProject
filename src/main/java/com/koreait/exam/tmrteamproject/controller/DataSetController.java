package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.DataSetService;
import com.koreait.exam.tmrteamproject.vo.DataSet;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

@Controller
@RequiredArgsConstructor
@Slf4j
@RequestMapping("usr/dataset")
@CrossOrigin(origins = "http://localhost:3000")
public class DataSetController {

    private final DataSetService dataSetService;

    @GetMapping("/upload")
    @ResponseBody
    public String savedDB() {
        String csvDir = Paths.get("src/main/resources/seoul_data_merge").toString();
        CompletableFuture<Integer> future = dataSetService.saveAllFromDirAsync(csvDir);
        System.out.println(future);

        return "저장 작업을 백그라운드에서 시작했습니다. 잠시 후 완료 됩니다.";
    }

    @GetMapping("/emd/info")
    @ResponseBody
    public List<Map<String, Object>> getEmdInfo(@RequestParam("adminDongCode") String adminDongCode) {
        return dataSetService.getFloatingAndSalesByEmd(adminDongCode);
    }

    @GetMapping("/getDataSet")
    @ResponseBody
    public DataSet getAverageSales(
            @RequestParam String emdCode,
            @RequestParam String upjongCd
    ) {
        List<DataSet> dataSets = dataSetService.findAllByAdminDongCodeAndServiceIndustryCode(emdCode, upjongCd);


        return dataSets.get(0);
    }

}
