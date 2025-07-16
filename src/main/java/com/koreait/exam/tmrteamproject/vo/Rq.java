package com.koreait.exam.tmrteamproject.vo;

import com.koreait.exam.tmrteamproject.util.Ut;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import lombok.Getter;
import lombok.Setter;
import org.springframework.context.annotation.Scope;
import org.springframework.context.annotation.ScopedProxyMode;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
@Scope(value = "request", proxyMode = ScopedProxyMode.TARGET_CLASS)
@Getter
@Setter
public class Rq {

    private final HttpServletRequest req;
    private final HttpServletResponse resp;
    private final HttpSession session;

    private boolean isLogined = false;
    private int loginedMemberId = 0;
    private Member loginedMember = null;


    public Rq(HttpServletRequest req, HttpServletResponse resp) {
        this.req = req;
        this.resp = resp;
        this.session = req.getSession();

        if (session.getAttribute("loginedMemberId") != null) {
            isLogined = true;
            loginedMemberId = (int) session.getAttribute("loginedMemberId");
            loginedMember = (Member) session.getAttribute("loginedMember");
        }

        this.req.setAttribute("rq", this);
    }

    public void printHistoryBack(String msg) throws IOException {
        resp.setContentType("text/html; charset=UTF-8");
        println("<script>");
        if (!Ut.isEmpty(msg)) {
            println("alert('" + msg.replace("'", "\\'") + "');");
        }
        println("history.back();");
        println("</script>");
        resp.getWriter().flush();
        resp.getWriter().close();
    }

    private void println(String str) throws IOException {
        print(str + "\n");
    }

    private void print(String str) throws IOException {
        resp.getWriter().append(str);
    }

    public void logout() {
        session.removeAttribute("loginedMemberId");
        session.removeAttribute("loginedMember");
    }

    public void login(int loginedMemberId, Member loginedMember) {
        session.setAttribute("loginedMemberId", loginedMemberId);
        session.setAttribute("loginedMember", loginedMember);
    }

    public void initBeforeActionInterceptor() {
        System.err.println("initBeforeActionInterceptor 실행됨");
    }

    public String historyBackOnView(String msg) {
        req.setAttribute("msg", msg);
        req.setAttribute("historyBack", true);
        req.removeAttribute("replace");

        return "usr/common/js";
    }

    public String replace(String msg, String replaceLocation) {
        req.setAttribute("replaceLocation", replaceLocation);
        req.setAttribute("msg", msg);
        req.setAttribute("replace", true);
        req.removeAttribute("historyBack");
        return "usr/common/js";
    }

    public String getCurrentUri() {
        String currentUri = req.getRequestURI();
        String queryString = req.getQueryString();

        System.out.println(currentUri);
        System.out.println(queryString);

        if (currentUri != null && queryString != null) {
            currentUri += "?" + queryString;
        }

        return currentUri;
    }
}
