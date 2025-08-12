package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.LhSupplyScheduleRepository;
import com.koreait.exam.tmrteamproject.repository.ScheduleInterestRepository;
import com.koreait.exam.tmrteamproject.vo.LhSupplySchedule;
import com.koreait.exam.tmrteamproject.vo.ScheduleInterest;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class LhSupplyScheduleService {

    private final LhSupplyScheduleRepository lhSupplyScheduleRepository;

    public LhSupplySchedule findById(Long id) {
        return lhSupplyScheduleRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("데이터 없음"));
    }
}
