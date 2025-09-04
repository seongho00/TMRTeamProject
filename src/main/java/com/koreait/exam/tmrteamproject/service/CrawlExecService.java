package com.koreait.exam.tmrteamproject.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
public class CrawlExecService {

    @Value("${lh.crawler.enabled}")
    private boolean enabled;

    @Value("${lh.crawler.python}")
    private String pythonCmd;

    @Value("${lh.crawler.script}") // 작업폴더 기준 상대경로
    private String scriptRelPath;

    @Value("${lh.crawler.workdir}")
    private String workdir;

    @Value("${lh.crawler.timeout-sec}")
    private long timeoutSec;

    public int runPythonOnce() {
        if (!enabled) {
            log.info("[Crawler] disabled → skip");
            return 0;
        }
        try {
            // 파이썬 스크립트 실행
            ProcessBuilder pb = new ProcessBuilder(pythonCmd, scriptRelPath);
            log.info("[Crawler] cmd: {} {}", pythonCmd, scriptRelPath);

            if (workdir != null && !workdir.isBlank()) {
                File wd = new File(workdir);
                log.info("[Crawler] workdir={}", wd.getAbsolutePath());
                pb.directory(wd);

                // 패키지 루트(workdir)를 PYTHONPATH에 주입해서 import 경로 보장
                Map<String, String> env = pb.environment();
                String root = wd.getAbsolutePath();
                String old = env.getOrDefault("PYTHONPATH", "");
                env.put("PYTHONPATH", old.isBlank() ? root : (root + File.pathSeparator + old));
            }

            pb.redirectErrorStream(true);
            Process p = pb.start();

            try (BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = br.readLine()) != null) log.info("[PY] {}", line);
            }

            boolean ok = p.waitFor(timeoutSec, TimeUnit.SECONDS);
            if (!ok) {
                p.destroyForcibly();
                log.error("[Crawler] timeout({}s)", timeoutSec);
                return -1;
            }
            int exit = p.exitValue();
            log.info("[Crawler] exit={}", exit);
            return exit;
        } catch (Exception e) {
            log.error("[Crawler] failed", e);
            return -1;
        }
    }
}
