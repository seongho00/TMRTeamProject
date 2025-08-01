package com.ltk.TMR.repository;

import com.ltk.TMR.entity.LhApplyInfo;
import com.ltk.TMR.entity.LhProcessingStatus;
import com.ltk.TMR.entity.MarkdownStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface LhApplyInfoRepository extends JpaRepository<LhApplyInfo, Long> {

    Optional<LhApplyInfo> findBySiteNo(int siteNo);

    List<LhApplyInfo> findByMarkdownStatusAndProcessingStatus(MarkdownStatus markdownStatus, LhProcessingStatus processingStatus);

    // [수정] 아래 메서드 선언을 추가하세요.
    List<LhApplyInfo> findAllByOrderBySiteNoDesc();
}