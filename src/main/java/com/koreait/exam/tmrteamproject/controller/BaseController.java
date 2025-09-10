package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.vo.Rq;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ModelAttribute;

@RequiredArgsConstructor
@ControllerAdvice
public class BaseController {

    private final Rq rq;

    @ModelAttribute("rq")
    public Rq getRq() {
        return rq;
    }
}
