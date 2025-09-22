package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.AddressService;
import com.koreait.exam.tmrteamproject.vo.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("usr/address")
@Slf4j
@RequiredArgsConstructor
public class AddressController {

    private final AddressService addressService;

    @PostMapping("/search")
    public List<NormalizedAddress> search(@RequestParam String keyword,
                                          @RequestParam(defaultValue = "1") int page,
                                          @RequestParam(defaultValue = "10") int size) {
        return addressService.search(keyword, page, size);
    }


    @PostMapping("/confirm")
    public NormalizedAddress confirm(@RequestBody AddressPickReq req){
        return addressService.confirmAndGeocode(req); // 동/호 파싱 + addressKey 생성 + (선택) DB 저장
    }

    @PostMapping("/confirm-crawl")
    public ResponseEntity<Map<String, Object>> confirmCrawl(@RequestBody AddressPickReq req) {
        Map<String, Object> res = addressService.confirmGeoAndCrawl(req);
        return ResponseEntity.ok(res);
    }
}
