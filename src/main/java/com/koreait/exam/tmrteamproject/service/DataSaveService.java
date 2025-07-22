package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.DataSaveRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DataSaveService {

    private final DataSaveRepository dataSaveRepository;

    public void setInsertData() {

    }
}
