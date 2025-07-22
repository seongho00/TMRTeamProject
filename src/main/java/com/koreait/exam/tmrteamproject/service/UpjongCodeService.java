package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.AdminDongRepository;
import com.koreait.exam.tmrteamproject.repository.UpjongCodeRepository;
import com.koreait.exam.tmrteamproject.vo.UpjongCode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UpjongCodeService {

    private final UpjongCodeRepository upjongCodeRepository;

    public List<UpjongCode> getUpjongCodesByMajorNm(String majorNm) {
        return upjongCodeRepository.getUpjongCodesByMajorNm(majorNm);
    }

    public List<UpjongCode> getGroupedUpjongCodesByMajorCd(String majorCd) {
        return upjongCodeRepository.getGroupedUpjongCodesByMajorCd(majorCd);
    }

    public List<UpjongCode> getUpjongCodesByMiddleCode(String middleCd) {
        return upjongCodeRepository.getUpjongCodesByMiddleCd(middleCd);
    }
}
