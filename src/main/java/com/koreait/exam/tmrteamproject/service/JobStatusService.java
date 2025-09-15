package com.koreait.exam.tmrteamproject.service;

import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class JobStatusService {
    private final Map<String, String> jobStatus = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> jobResults = new ConcurrentHashMap<>();

    public void setStatus(String jobId, String status) {
        jobStatus.put(jobId, status);
    }

    public String getStatus(String jobId) {
        return jobStatus.getOrDefault(jobId, "unknown");
    }


    // 결과 저장/조회
    public void setResult(String jobId, Map<String, Object> result) {
        jobResults.put(jobId, result);
    }

    public Map<String, Object> getResult(String jobId) {
        return jobResults.get(jobId);
    }
}