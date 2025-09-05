package com.koreait.exam.tmrteamproject.runner;

import com.koreait.exam.tmrteamproject.service.CrawlExecService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class LHCrawlerRunner {

    private final CrawlExecService crawlExecService;

    // 10시 00분 30초 실행
    @Scheduled(cron = "30 0 10 * * *", zone = "Asia/Seoul")
    public void runCrawlerAt100030() {
        log.info("[Scheduler] 10:00:30 크롤러 작업 시작");
        int exit = crawlExecService.runPythonOnce();
        log.info("[Scheduler] exit={}", exit);
    }

    // 14시 00분 00초, 16시 00분 00초 실행
    @Scheduled(cron = "0 0 14,16 * * *", zone = "Asia/Seoul")
    public void runCrawlerAt1400And1600() {
        log.info("[Scheduler] 14:00/16:00 크롤러 작업 시작");
        int exit = crawlExecService.runPythonOnce();
        log.info("[Scheduler] exit={}", exit);
    }
}
