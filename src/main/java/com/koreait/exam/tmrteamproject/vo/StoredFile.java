package com.koreait.exam.tmrteamproject.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.Builder;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class StoredFile {
    private String originalName;
    private String contentType;
    private long size;
    private String storedPath;  // 절대 경로
    private String fileName;    // 저장 파일명
}