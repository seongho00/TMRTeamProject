package com.koreait.exam.tmrteamproject.runner;

import com.koreait.exam.tmrteamproject.service.CrawlExecService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@Order(1)
@RequiredArgsConstructor
public class LHCrawlerRunner implements ApplicationRunner {

    private final CrawlExecService crawlExecService;

    @Override
    public void run(ApplicationArguments args) {
        log.info("크롤러 작업 시작");
        int exit = crawlExecService.runPythonOnce();
        log.info("[Startup] python exit={}", exit);
    }
}
