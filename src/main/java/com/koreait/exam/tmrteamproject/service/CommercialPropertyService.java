package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.CommercialPropertyRepository;
import com.koreait.exam.tmrteamproject.repository.MemberRepository;
import com.koreait.exam.tmrteamproject.vo.CommercialProperty;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CommercialPropertyService {

    private final CommercialPropertyRepository commercialPropertyRepository;

    public List<CommercialProperty> getCommercialProperty() {
        return commercialPropertyRepository.findAll();
    }
}
