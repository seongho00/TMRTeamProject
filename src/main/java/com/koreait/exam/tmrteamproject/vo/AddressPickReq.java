package com.koreait.exam.tmrteamproject.vo;

import lombok.Getter;
import lombok.Setter;

// DTO: 사용자가 고른 항목 + 동/호
@Getter
@Setter
public class AddressPickReq {
    private NormalizedAddress selected;
    private String dong; // "101동" 가능
    private String ho;   // "202호" 가능
}
