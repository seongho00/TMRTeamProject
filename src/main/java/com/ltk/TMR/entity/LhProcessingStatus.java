package com.ltk.TMR.entity;

// 설명: PDF의 마크다운 텍스트를 LLM으로 처리하는 작업의 상태를 나타냅니다.
public enum LhProcessingStatus {
    PENDING,    // 처리 대기 중 (마크다운 추출 완료)
    PROCESSING, // LLM API 호출 및 데이터 추출 진행 중
    COMPLETED,  // 데이터 추출 및 DB 저장 완료
    FAILED      // 처리 실패
}