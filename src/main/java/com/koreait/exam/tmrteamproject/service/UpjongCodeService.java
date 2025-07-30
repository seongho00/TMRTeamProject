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
        return null;
    }

    public List<UpjongCode> getGroupedUpjongCodesByMajorCd(String majorCd) {
        return null;
    }

    public List<UpjongCode> getUpjongCodesByMiddleCd(String middleCd) {
        return null;
    }

    public UpjongCode getUpjongCodeByMinorCd(String minorCd) {
        return null;
    }

    public List<UpjongCode> getUpjongCodeByKeyword(String keyword) {

        return null;
    }

    public List<UpjongCode> findAll() {
        return upjongCodeRepository.findAll();
    }
}
