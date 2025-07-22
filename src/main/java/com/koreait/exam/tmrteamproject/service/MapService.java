package com.koreait.exam.tmrteamproject.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.koreait.exam.tmrteamproject.repository.AdminDongRepository;
import com.koreait.exam.tmrteamproject.vo.AdminDong;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.Rq;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class MapService {


}
