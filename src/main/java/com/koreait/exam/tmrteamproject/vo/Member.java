package com.koreait.exam.tmrteamproject.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class Member {
    private int id;
    private String name;
    private String loginPw;
    private String email;
    private String phoneNum;
}
