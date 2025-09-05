package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.LhApplyInfoService;
import com.koreait.exam.tmrteamproject.vo.LhApplyInfo;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;

import java.util.List;

@Controller
@Slf4j
@RequiredArgsConstructor
@RequestMapping("/usr/api")
public class LhIngestController {

    private final LhApplyInfoService lhApplyInfoService;

    @PostMapping("/ingest")
    public ResponseEntity<String> ingest(@RequestBody List<LhApplyInfo> items){
        int n = lhApplyInfoService.upsertBatch(items);
        log.info("InGest upsert = {}", n);
        return ResponseEntity.ok("upsert=" + n);
    }
}
