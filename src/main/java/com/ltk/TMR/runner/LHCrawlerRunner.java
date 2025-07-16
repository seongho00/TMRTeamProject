package com.ltk.TMR.runner;
/* 앱 실행시 저장된 JSON을 읽어 DB에 저장 */

import com.ltk.TMR.service.LhApplyInfoService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class LHCrawlerRunner implements ApplicationRunner {

    private final LhApplyInfoService svc;

    @Override
    public void run(ApplicationArguments args) {
        log.info("[Runner] LH 크롤러 작업 시작");

        svc.refreshFromCrawler();

    }
}
