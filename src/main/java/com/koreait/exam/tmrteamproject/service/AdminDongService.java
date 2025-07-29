package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.AdminDongRepository;
import com.koreait.exam.tmrteamproject.vo.AdminDong;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AdminDongService {
    private final AdminDongRepository adminDongRepository;


    public List<AdminDong> getAdminDongsBySggNm(String sgg) {

        return adminDongRepository.getAdminDongsBySggNm(sgg);
    }

    public List<AdminDong> getAdminDongsGroupBySgg() {

        return adminDongRepository.getAdminDongGroupBySggCd();
    }
}
