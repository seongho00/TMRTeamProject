package com.koreait.exam.tmrteamproject.service;

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

    public List<UpjongCode> findAll() {
        return upjongCodeRepository.findAll();
    }

    public List<String> getAllNames() {
        return upjongCodeRepository.findAllName();
    }

    public List<String> searchNames(String q) {
        if (q == null || q.isEmpty()) {
            return getAllNames();
        }

        return upjongCodeRepository.searchNames(q);
    }

}
